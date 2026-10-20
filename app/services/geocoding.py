
import json
import os
import re
import sqlite3
import time

from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from flask import current_app, session
from itsdangerous import (
    URLSafeTimedSerializer,
    BadSignature
)


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

CACHE_DB = (
    Path(__file__).resolve().parents[2]
    / "database"
    / "geocoding_cache.db"
)


class GeocodingIndisponible(Exception):
    pass


def normaliser(texte):
    """Normalisation utilisée pour le cache et les jetons."""
    return " ".join(str(texte or "").strip().split()).casefold()


def trouver_coordonnees(adresse, ville):
    """
    Recherche une adresse dans Nominatim.

    - Recherche libre avec q=adresse.
    - Récupère jusqu'à 5 résultats.
    - Privilégie un numéro civique exact.
    - Utilise le premier résultat pertinent sinon.
    - Conserve les résultats en cache.
    """

    adresse = " ".join(adresse.strip().split())
    ville = ville.strip()

    if not adresse or not ville:
        return None

    user_agent = os.getenv("NOMINATIM_USER_AGENT")

    if not user_agent:
        raise GeocodingIndisponible(
            "NOMINATIM_USER_AGENT n'est pas configuré."
        )

    # Numéro civique éventuel.
    match = re.match(r"^(\d+[A-Za-z]?)\b", adresse)
    numero_demande = (
        match.group(1).casefold() if match else None
    )

    # Cache lié à l'adresse et à la ville.
    cle = normaliser(f"{adresse}|{ville}")

    CACHE_DB.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with sqlite3.connect(CACHE_DB, timeout=30) as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS geocode_cache (
                cle TEXT PRIMARY KEY,
                resultat TEXT NOT NULL,
                date_creation REAL NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS limite_appels (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                dernier_appel REAL NOT NULL
            )
        """)

        conn.execute("""
            INSERT OR IGNORE INTO limite_appels
            VALUES (1, 0)
        """)

        conn.commit()

        conn.execute("BEGIN IMMEDIATE")

        cache = conn.execute(
            """
            SELECT resultat, date_creation
            FROM geocode_cache
            WHERE cle = ?
            """,
            (cle,)
        ).fetchone()

        if cache:
            resultat_cache = json.loads(cache[0])

            duree = (
                604800 if resultat_cache is not None
                else 86400
            )

            if time.time() - cache[1] < duree:
                return resultat_cache

        dernier_appel = conn.execute(
            """
            SELECT dernier_appel
            FROM limite_appels
            WHERE id = 1
            """
        ).fetchone()[0]

        attente = 1.1 - (time.time() - dernier_appel)

        if attente > 0:
            time.sleep(attente)

        params = {
            "q": adresse,
            "format": "jsonv2",
            "addressdetails": 1,
            "countrycodes": "ca",
            "limit": 5,
            "accept-language": "fr"
        }

        url = NOMINATIM_URL + "?" + urlencode(params)

        requete = Request(
            url,
            headers={
                "User-Agent": user_agent,
                "Accept-Language": "fr"
            }
        )

        try:
            with urlopen(requete, timeout=8) as reponse:
                candidats = json.load(reponse)

        except (
            HTTPError,
            URLError,
            TimeoutError,
            ValueError
        ) as exc:

            conn.execute(
                """
                UPDATE limite_appels
                SET dernier_appel = ?
                WHERE id = 1
                """,
                (time.time(),)
            )

            conn.commit()

            raise GeocodingIndisponible(
                "Le service de géocodage est indisponible."
            ) from exc

        resultat = None
        fallback = None

        for candidat in candidats:

            details = candidat.get("address", {})

            code_region = details.get("ISO3166-2-lvl4")

            if code_region and code_region != "CA-QC":
                continue

            try:
                latitude = float(candidat["lat"])
                longitude = float(candidat["lon"])
            except (KeyError, TypeError, ValueError):
                continue

            if not (
                -90 <= latitude <= 90
                and -180 <= longitude <= 180
            ):
                continue

            numero_trouve = str(
                details.get("house_number", "")
            ).strip().casefold()

            nom = str(
                candidat.get("name") or ""
            ).strip().casefold()

            numero_exact = bool(
                numero_demande
                and (
                    numero_trouve == numero_demande
                    or nom.startswith(numero_demande + " ")
                )
            )

            position = {
                "latitude": latitude,
                "longitude": longitude,
                "adresse_complete": candidat.get(
                    "display_name", adresse
                ),
                "numero_exact": numero_exact
            }

            # Premier résultat valide de Nominatim.
            if fallback is None:
                fallback = position

            # Priorité au numéro civique exact.
            if numero_exact:
                resultat = position
                break

        # Aucun numéro exact : premier résultat valide.
        if resultat is None:
            resultat = fallback

        # Enregistrer le résultat en cache.
        conn.execute(
            """
            INSERT INTO geocode_cache (
                cle, resultat, date_creation
            )
            VALUES (?, ?, ?)
            ON CONFLICT(cle) DO UPDATE SET
                resultat = excluded.resultat,
                date_creation = excluded.date_creation
            """,
            (
                cle,
                json.dumps(resultat),
                time.time()
            )
        )

        conn.execute(
            """
            UPDATE limite_appels
            SET dernier_appel = ?
            WHERE id = 1
            """,
            (time.time(),)
        )

        conn.commit()

        return resultat


def _serializer():
    """Génère le sérialiseur pour les jetons signés."""
    return URLSafeTimedSerializer(
        current_app.secret_key,
        salt="parkshare-geocode-v1"
    )


def creer_jeton(adresse, ville, position):
    """
    Crée un jeton signé associant :
    - l'utilisateur
    - l'adresse
    - la ville
    - les coordonnées
    """

    return _serializer().dumps({
        "user_id": session["user_id"],
        "adresse": normaliser(adresse),
        "ville": normaliser(ville),
        "latitude": position["latitude"],
        "longitude": position["longitude"]
    })


def valider_jeton(jeton, adresse, ville):
    """
    Vérifie que le jeton est valide
    et correspond à l'adresse actuelle.

    Expiration : 30 minutes.
    """

    if not jeton:
        return None

    try:
        donnees = _serializer().loads(
            jeton,
            max_age=1800
        )
    except BadSignature:
        return None

    if donnees.get("user_id") != session.get("user_id"):
        return None

    if donnees.get("adresse") != normaliser(adresse):
        return None

    if donnees.get("ville") != normaliser(ville):
        return None

    latitude = donnees.get("latitude")
    longitude = donnees.get("longitude")

    if not isinstance(latitude, (int, float)):
        return None

    if not isinstance(longitude, (int, float)):
        return None

    if not (
        -90 <= latitude <= 90
        and -180 <= longitude <= 180
    ):
        return None

    return {
        "latitude": latitude,
        "longitude": longitude
    }
