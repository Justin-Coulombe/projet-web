#!/usr/bin/env python3
"""Crée des données fictives pour ParkShare (SQLite + carte OpenStreetMap).

À exécuter depuis le dépôt : python populate_db.py --reset --yes

DANGER : --reset supprime TOUTES les lignes des tables Reservation,
Publication et User dans la base locale database/parkshare.db.

Photos téléchargées depuis Lorem Picsum dans app/static/img/stationnement/.
Elles sont aléatoires et ne représentent pas forcément des stationnements.
Les adresses ET les positions GPS sont SYNTHÉTIQUES ; elles servent seulement
à tester la carte, pas à représenter des emplacements vérifiés.
"""

from __future__ import annotations

import argparse
import math
import os
import random
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from werkzeug.security import generate_password_hash

ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / "database" / "parkshare.db"
IMAGE_DIR = ROOT / "app" / "static" / "img" / "stationnement"
DEMO_PASSWORD = "ParkShareDemo123!"

# Centre approximatif des villes (pas des adresses individuelles).
# Les coordonnées de chaque publication sont réparties artificiellement
# autour du centre de sa ville pour tester Leaflet et les filtres.
VILLES = {
    "Montréal": {
        "centre": (45.5019, -73.5674), "rayon": 6,
        "rues": ["rue Saint-Denis", "boulevard Saint-Laurent",
                 "rue Sainte-Catherine Ouest", "rue Sherbrooke Ouest",
                 "rue de la Gauchetière Ouest", "rue Ontario Est"],
        "poids": 28,
    },
    "Québec": {
        "centre": (46.8139, -71.2080), "rayon": 5,
        "rues": ["rue Saint-Jean", "rue Saint-Joseph Est",
                 "boulevard Charest Est", "rue Cartier", "Grande Allée Est",
                 "chemin Sainte-Foy", "rue Saint-Vallier Ouest"],
        "poids": 25,
    },
    "Laval": {
        "centre": (45.6066, -73.7124), "rayon": 4,
        "rues": ["boulevard Saint-Martin", "boulevard des Laurentides", "boulevard Le Corbusier"],
        "poids": 5,
    },
    "Gatineau": {
        "centre": (45.4765, -75.7013), "rayon": 4,
        "rues": ["boulevard Gréber", "boulevard Saint-Joseph", "rue Montcalm"],
        "poids": 5,
    },
    "Longueuil": {
        "centre": (45.5312, -73.5180), "rayon": 3,
        "rues": ["rue Saint-Charles Ouest", "boulevard Taschereau", "chemin de Chambly"],
        "poids": 5,
    },
    "Sherbrooke": {
        "centre": (45.4042, -71.8929), "rayon": 3,
        "rues": ["rue King Ouest", "rue Wellington Nord", "boulevard de Portland"],
        "poids": 5,
    },
    "Lévis": {
        "centre": (46.8033, -71.1779), "rayon": 3,
        "rues": ["route du Président-Kennedy", "rue Saint-Georges", "boulevard Guillaume-Couture"],
        "poids": 4,
    },
    "Saguenay": {
        "centre": (48.4279, -71.0688), "rayon": 4,
        "rues": ["boulevard Talbot", "rue Racine Est", "boulevard Saint-Paul"],
        "poids": 3,
    },
    "Trois-Rivières": {
        "centre": (46.3430, -72.5430), "rayon": 3,
        "rues": ["boulevard des Forges", "rue des Ursulines", "boulevard Jean-XXIII"],
        "poids": 4,
    },
    "Terrebonne": {
        "centre": (45.6928, -73.6335), "rayon": 3,
        "rues": ["boulevard des Seigneurs", "rue Saint-Pierre", "montée Masson"],
        "poids": 3,
    },
    "Saint-Jean-sur-Richelieu": {
        "centre": (45.3077, -73.2623), "rayon": 3,
        "rues": ["rue Richelieu", "boulevard du Séminaire Nord", "rue Saint-Jacques"],
        "poids": 2,
    },
    "Brossard": {
        "centre": (45.4670, -73.4530), "rayon": 3,
        "rues": ["boulevard Taschereau", "boulevard de Rome", "boulevard du Quartier"],
        "poids": 3,
    },
    "Repentigny": {
        "centre": (45.7380, -73.4510), "rayon": 3,
        "rues": ["boulevard Brien", "rue Notre-Dame", "boulevard Iberville"],
        "poids": 2,
    },
    "Saint-Jérôme": {
        "centre": (45.7800, -74.0030), "rayon": 3,
        "rues": ["rue Saint-Georges", "boulevard du Curé-Labelle", "rue de Martigny Ouest"],
        "poids": 2,
    },
    "Drummondville": {
        "centre": (45.8830, -72.4840), "rayon": 3,
        "rues": ["boulevard Saint-Joseph", "rue Lindsay", "boulevard Lemire"],
        "poids": 2,
    },
}

PRENOMS = ["Alice", "David", "Emma", "Gabriel", "Hugo", "Isabelle", "Karim", "Léa", "Marc", "Nadia", "Olivier", "Rania", "Sophie", "Théo", "Zoé"]
NOMS = ["Tremblay", "Gagnon", "Roy", "Côté", "Bouchard", "Gauthier", "Morin", "Lavoie", "Fortin", "Pelletier"]

SCHEMA_ATTENDU = {
    "User": {"id", "nom", "prenom", "email", "mdp"},
    "Publication": {
        "id", "author", "address", "prix", "debut", "fin", "ville",
        "emplacement", "image", "placetotal", "placeactuel",
        "disponibilite", "latitude", "longitude",
    },
    "Reservation": {"id", "client", "publication", "debut", "fin"},
}


def initialiser_db() -> None:
    # Les fonctions officielles du projet créent les tables utilisées par Flask.
    os.chdir(ROOT)
    from app.database.init_db import init_database
    init_database()


def verifier_schema(conn: sqlite3.Connection) -> None:
    for table, colonnes in SCHEMA_ATTENDU.items():
        presentes = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        manque = colonnes - presentes
        if manque:
            raise RuntimeError(
                f"Schéma incomplet pour {table} : {', '.join(sorted(manque))}. "
                "Vérifie CREATE TABLE dans app/database/queries/ et, puisque "
                "tu n'as que des mock data, supprime database/parkshare.db puis relance le script."
            )


def generer_coordonnees(rng: random.Random, ville: str) -> tuple[float, float]:
    """Points artificiels proches du centre, PAS géocodage d'une adresse."""
    (lat, lon) = VILLES[ville]["centre"]
    rayon_km = VILLES[ville]["rayon"]
    angle = rng.uniform(0, 2 * math.pi)
    distance_km = rayon_km * math.sqrt(rng.random())
    delta_lat = distance_km * math.cos(angle) / 111.32
    delta_lon = distance_km * math.sin(angle) / (111.32 * math.cos(math.radians(lat)))
    return round(lat + delta_lat, 6), round(lon + delta_lon, 6)


def telecharger_photo(index: int, *, force: bool = False) -> str | None:
    """Télécharge une image JPEG déterministe; renvoie son nom ou None."""
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    nom = f"mock_parkshare_{index:03d}.jpg"
    destination = IMAGE_DIR / nom

    if destination.exists() and destination.stat().st_size > 1024 and not force:
        return nom

    url = f"https://picsum.photos/seed/parkshare-2026-{index:03d}/840/560.jpg"
    requete = Request(url, headers={"User-Agent": "ParkShare-MockSeeder/1.0"})
    temporaire = destination.with_suffix(".tmp")

    for tentative in range(1, 4):
        try:
            with urlopen(requete, timeout=18) as reponse:
                contenu = reponse.read(6 * 1024 * 1024 + 1)
            if len(contenu) > 6 * 1024 * 1024 or not contenu.startswith(b"\xff\xd8\xff"):
                raise ValueError("Réponse non JPEG ou image trop volumineuse")
            temporaire.write_bytes(contenu)
            temporaire.replace(destination)
            return nom
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as erreur:
            if temporaire.exists():
                temporaire.unlink()
            if tentative == 3:
                print(f"  [Photo {index}] Échec du téléchargement : {erreur}")
            else:
                time.sleep(tentative)

    return None


def creer_utilisateurs(conn: sqlite3.Connection, rng: random.Random, count: int) -> list[int]:
    ids = []
    for i in range(count):
        prenom, nom = ("Admin", "Demo") if i == 0 else (rng.choice(PRENOMS), rng.choice(NOMS))
        email = "admin@parkshare.test" if i == 0 else f"demo{i:03d}@parkshare.test"
        conn.execute(
            "INSERT INTO User (nom, prenom, email, mdp) VALUES (?, ?, ?, ?)",
            (nom, prenom, email, generate_password_hash(DEMO_PASSWORD)),
        )
        ids.append(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
    return ids


def creer_publications(
    conn: sqlite3.Connection,
    rng: random.Random,
    count: int,
    utilisateurs: list[int],
    noms_photos: list[str],
) -> list[tuple[int, int, int, datetime, datetime]]:
    villes = list(VILLES)
    poids = [VILLES[ville]["poids"] for ville in villes]
    maintenant = datetime.now().replace(second=0, microsecond=0)
    references = []

    for i in range(count):
        ville = rng.choices(villes, weights=poids, k=1)[0]
        rue = rng.choice(VILLES[ville]["rues"])
        adresse = f"{rng.randint(10, 1900)} {rue}"
        latitude, longitude = generer_coordonnees(rng, ville)
        auteur = rng.choice(utilisateurs)
        prix = round(rng.uniform(3.0, 28.0), 2)
        places_totales = rng.randint(1, 12)
        places_disponibles = rng.randint(1, places_totales)
        debut = maintenant - timedelta(days=rng.randint(1, 30))
        fin = maintenant + timedelta(days=rng.randint(20, 100))
        type_emplacement = rng.choice(("Intérieur", "Extérieur"))
        photo = rng.choice(noms_photos) if noms_photos else None

        cursor = conn.execute(
            """
            INSERT INTO Publication (
                author, address, prix, debut, fin, ville, emplacement,
                image, placetotal, placeactuel, disponibilite,
                latitude, longitude
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                auteur, adresse, prix, debut.strftime("%Y-%m-%dT%H:%M"),
                fin.strftime("%Y-%m-%dT%H:%M"), ville, type_emplacement,
                photo, places_totales, places_disponibles, 1,
                latitude, longitude,
            ),
        )
        references.append((cursor.lastrowid, auteur, places_disponibles, debut, fin))

    return references


def creer_reservations(
    conn: sqlite3.Connection,
    rng: random.Random,
    count: int,
    utilisateurs: list[int],
    publications: list[tuple[int, int, int, datetime, datetime]],
) -> int:
    # Une réservation utilise une place disponible et ne peut pas être faite
    # par le propriétaire. Modèle simplifié, comme l'application actuelle.
    possibles = list(publications)
    rng.shuffle(possibles)
    total = 0

    for identifiant, proprietaire, places_libres, debut_pub, fin_pub in possibles:
        if total >= count:
            break
        clients = [u for u in utilisateurs if u != proprietaire]
        if not clients or places_libres <= 0:
            continue
        client = rng.choice(clients)
        depart = max(datetime.now().replace(second=0, microsecond=0) + timedelta(days=1), debut_pub)
        arrivee = depart + timedelta(hours=rng.randint(1, 8))
        if arrivee > fin_pub:
            continue
        conn.execute(
            "INSERT INTO Reservation (client, publication, debut, fin) VALUES (?, ?, ?, ?)",
            (client, identifiant, depart.strftime("%Y-%m-%dT%H:%M"), arrivee.strftime("%Y-%m-%dT%H:%M")),
        )
        nouvelles_places = places_libres - 1
        conn.execute(
            "UPDATE Publication SET placeactuel = ?, disponibilite = ? WHERE id = ?",
            (nouvelles_places, int(nouvelles_places > 0), identifiant),
        )
        total += 1

    return total


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Génère la base fictive ParkShare et télécharge des images Picsum.")
    parser.add_argument("--users", type=int, default=15, help="Nombre d'utilisateurs fictifs (défaut : 15)")
    parser.add_argument("--publications", type=int, default=80, help="Nombre d'annonces (défaut : 80)")
    parser.add_argument("--reservations", type=int, default=12, help="Nombre de réservations (défaut : 12)")
    parser.add_argument("--photos", type=int, default=16, help="Nombre de photos à télécharger (défaut : 16)")
    parser.add_argument("--no-photos", action="store_true", help="Ne pas télécharger de photos (images placeholder)")
    parser.add_argument("--force-photos", action="store_true", help="Télécharger à nouveau les photos déjà présentes")
    parser.add_argument("--seed", type=int, default=42, help="Graine des données fictives (défaut : 42)")
    parser.add_argument("--reset", action="store_true", help="Effacer les données des trois tables avant l'insertion")
    parser.add_argument("--yes", action="store_true", help="Confirmer la suppression avec --reset")
    args = parser.parse_args()
    if args.users < 1 or args.publications < 1 or args.reservations < 0 or args.photos < 0:
        parser.error("--users et --publications doivent être >=1; --reservations et --photos >=0")
    if args.reservations and args.users < 2:
        parser.error("Il faut au moins deux utilisateurs pour générer des réservations.")
    if args.reset and not args.yes:
        parser.error("--reset supprime les données existantes; ajoute --yes pour confirmer.")
    return args


def main() -> int:
    args = parse_args()
    rng = random.Random(args.seed)
    initialiser_db()
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        verifier_schema(conn)
        existe = conn.execute("SELECT COUNT(*) FROM User").fetchone()[0]
        exist_pub = conn.execute("SELECT COUNT(*) FROM Publication").fetchone()[0]
        exist_res = conn.execute("SELECT COUNT(*) FROM Reservation").fetchone()[0]
        if (existe or exist_pub or exist_res) and not args.reset:
            raise RuntimeError(
                "La base contient déjà des données. Ajoute --reset --yes "
                "pour les remplacer (attention : cela supprime aussi tes annonces de test)."
            )

        print(f"Base de données : {DATABASE}")
        noms_photos = []
        if not args.no_photos and args.photos:
            print("Téléchargement / réutilisation des images Lorem Picsum...")
            for i in range(1, min(args.photos, args.publications) + 1):
                nom = telecharger_photo(i, force=args.force_photos)
                if nom:
                    noms_photos.append(nom)
            print(f"Photos disponibles : {len(noms_photos)}")

        with conn:
            if args.reset:
                conn.execute("DELETE FROM Reservation")
                conn.execute("DELETE FROM Publication")
                conn.execute("DELETE FROM User")
                conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('Reservation', 'Publication', 'User')")
            utilisateurs = creer_utilisateurs(conn, rng, args.users)
            publications = creer_publications(conn, rng, args.publications, utilisateurs, noms_photos)
            reservations = creer_reservations(conn, rng, args.reservations, utilisateurs, publications)

        print(f"Créé : {len(utilisateurs)} utilisateurs, {len(publications)} annonces, {reservations} réservations")
        print(f"Images : {IMAGE_DIR} (noms de fichiers enregistrés dans Publication.image)")
        print(f"Compte de démo : admin@parkshare.test / {DEMO_PASSWORD}")
        print("Coordonnées : artificielles, proches des villes; aucune adresse n'a été géocodée.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, sqlite3.Error) as exc:
        print(f"ERREUR : {exc}", file=sys.stderr)
        sys.exit(1)
