#!/usr/bin/env python3
"""Crée des données fictives pour ParkShare (SQLite + carte OpenStreetMap).

À exécuter depuis la racine du dépôt : python populate_db.py --reset --yes

Schéma ciblé (voir app/database/queries/) :
    User(id, nom, prenom, email, mdp, banni)
    Publication(id, author, address, prix, ville, emplacement, image,
                placetotal, banni, latitude, longitude)
    Reservation(id, client, publication, debut, fin)
    Admin(id, username, cle)            <- jamais touchée par ce script

DANGER : --reset supprime TOUTES les lignes de Reservation, Publication et
User (la table Admin est conservée).

Points importants pour les requêtes de l'application :
  * Publication.banni vaut TRUE par défaut et toutes les requêtes de lecture
    filtrent "banni = FALSE" -> les annonces sont insérées avec banni = 0,
    sauf quelques-unes volontairement à 1 (en attente / bannies).
  * Les requêtes filtrent aussi sur User.banni de l'auteur -> quelques
    utilisateurs bannis sont créés pour tester ce filtre.

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
FORMAT_DATE = "%Y-%m-%dT%H:%M"

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
    "User": {"id", "nom", "prenom", "email", "mdp", "banni"},
    "Publication": {
        "id", "author", "address", "prix", "ville", "emplacement",
        "image", "placetotal", "banni", "latitude", "longitude",
    },
    "Reservation": {"id", "client", "publication", "debut", "fin"},
}

# Même définition que app/database/queries/ ; sert uniquement si la base
# n'existe pas encore et que init_database() est introuvable.
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS User (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    mdp TEXT NOT NULL,
    banni BOOLEAN DEFAULT false
);
CREATE TABLE IF NOT EXISTS Publication (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author INTEGER NOT NULL,
    address TEXT NOT NULL,
    prix DOUBLE NOT NULL CHECK (prix >= 0.01 AND prix <= 1000),
    ville TEXT NOT NULL,
    emplacement TEXT,
    image TEXT,
    placetotal INTEGER NOT NULL CHECK (placetotal BETWEEN 1 AND 100),
    banni BOOLEAN NOT NULL DEFAULT TRUE,
    latitude REAL,
    longitude REAL,
    FOREIGN KEY (author) REFERENCES User(id)
);
CREATE TABLE IF NOT EXISTS Reservation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client INTEGER NOT NULL,
    publication INTEGER NOT NULL,
    debut DATETIME NOT NULL,
    fin DATETIME NOT NULL,
    FOREIGN KEY (publication) REFERENCES Publication(id),
    FOREIGN KEY (client) REFERENCES User(id)
);
CREATE TABLE IF NOT EXISTS Admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    cle TEXT NOT NULL
);
"""


def initialiser_db() -> None:
    # On préfère les fonctions officielles du projet (celles de Flask) ;
    # sinon on crée les tables avec le schéma ci-dessus.
    os.chdir(ROOT)
    try:
        from app.database.init_db import init_database
        init_database()
    except ImportError:
        DATABASE.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(DATABASE) as conn:
            conn.executescript(SCHEMA_SQL)


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


def creer_utilisateurs(
    conn: sqlite3.Connection, rng: random.Random, count: int, bannis: int
) -> tuple[list[int], set[int]]:
    """Le 1er utilisateur est le compte admin de démo (jamais banni).

    Les `bannis` derniers utilisateurs sont bannis (User.banni = 1) afin de
    tester le filtre « auteur non banni » des requêtes de publications.
    """
    ids = []
    ids_bannis: set[int] = set()
    nb_bannis = min(bannis, max(count - 2, 0))  # garde au moins 2 utilisateurs actifs

    for i in range(count):
        prenom, nom = ("Admin", "Demo") if i == 0 else (rng.choice(PRENOMS), rng.choice(NOMS))
        email = "admin@parkshare.test" if i == 0 else f"demo{i:03d}@parkshare.test"
        banni = int(i >= count - nb_bannis and i != 0)
        cursor = conn.execute(
            "INSERT INTO User (nom, prenom, email, mdp, banni) VALUES (?, ?, ?, ?, ?)",
            (nom, prenom, email, generate_password_hash(DEMO_PASSWORD), banni),
        )
        ids.append(cursor.lastrowid)
        if banni:
            ids_bannis.add(cursor.lastrowid)
    return ids, ids_bannis


def creer_publications(
    conn: sqlite3.Connection,
    rng: random.Random,
    count: int,
    utilisateurs: list[int],
    noms_photos: list[str],
    taux_bannies: float,
) -> list[tuple[int, int, int, bool]]:
    """Renvoie (id, auteur, placetotal, visible) pour chaque annonce créée."""
    villes = list(VILLES)
    poids = [VILLES[ville]["poids"] for ville in villes]
    references = []

    for _ in range(count):
        ville = rng.choices(villes, weights=poids, k=1)[0]
        rue = rng.choice(VILLES[ville]["rues"])
        adresse = f"{rng.randint(10, 1900)} {rue}"
        latitude, longitude = generer_coordonnees(rng, ville)
        auteur = rng.choice(utilisateurs)
        prix = round(rng.uniform(3.0, 28.0), 2)               # CHECK 0.01..1000
        # Surtout des petits stationnements, parfois de grands lots (CHECK 1..100)
        if rng.random() < 0.1:
            places_totales = rng.randint(20, 60)
        else:
            places_totales = rng.randint(1, 12)
        type_emplacement = rng.choice(("Intérieur", "Extérieur"))
        photo = rng.choice(noms_photos) if noms_photos else None
        # banni = 1 : annonce en attente de validation ou bannie par l'admin
        banni = int(rng.random() < taux_bannies)

        cursor = conn.execute(
            """
            INSERT INTO Publication (
                author, address, prix, ville, emplacement,
                image, placetotal, banni, latitude, longitude
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                auteur, adresse, prix, ville, type_emplacement,
                photo, places_totales, banni, latitude, longitude,
            ),
        )
        references.append((cursor.lastrowid, auteur, places_totales, not banni))

    return references


def creer_reservations(
    conn: sqlite3.Connection,
    rng: random.Random,
    count: int,
    utilisateurs: list[int],
    utilisateurs_bannis: set[int],
    publications: list[tuple[int, int, int, bool]],
) -> int:
    """Réservations plausibles : jamais par le propriétaire, jamais sur une
    annonce bannie ou d'un auteur banni, et sans dépasser placetotal sur un
    même créneau. Un quart sont dans le passé (historique)."""
    maintenant = datetime.now().replace(minute=0, second=0, microsecond=0)
    clients_possibles = [u for u in utilisateurs if u not in utilisateurs_bannis]
    candidates = [
        p for p in publications if p[3] and p[1] not in utilisateurs_bannis
    ]
    creneaux: dict[int, list[tuple[datetime, datetime]]] = {}
    total = 0
    tentatives = 0

    while total < count and candidates and tentatives < count * 20:
        tentatives += 1
        identifiant, proprietaire, places_totales, _ = rng.choice(candidates)
        clients = [u for u in clients_possibles if u != proprietaire]
        if not clients:
            continue
        client = rng.choice(clients)

        if rng.random() < 0.25:
            depart = maintenant - timedelta(days=rng.randint(1, 30), hours=rng.randint(0, 10))
        else:
            depart = maintenant + timedelta(days=rng.randint(1, 45), hours=rng.randint(0, 10))
        arrivee = depart + timedelta(hours=rng.randint(1, 8))

        existants = creneaux.setdefault(identifiant, [])
        chevauchent = sum(1 for (d, a) in existants if d < arrivee and a > depart)
        if chevauchent >= places_totales:
            continue

        conn.execute(
            "INSERT INTO Reservation (client, publication, debut, fin) VALUES (?, ?, ?, ?)",
            (client, identifiant, depart.strftime(FORMAT_DATE), arrivee.strftime(FORMAT_DATE)),
        )
        existants.append((depart, arrivee))
        total += 1

    return total


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Génère la base fictive ParkShare et télécharge des images Picsum.")
    parser.add_argument("--users", type=int, default=15, help="Nombre d'utilisateurs fictifs (défaut : 15)")
    parser.add_argument("--banned-users", type=int, default=2, help="Dont combien sont bannis (défaut : 2)")
    parser.add_argument("--publications", type=int, default=80, help="Nombre d'annonces (défaut : 80)")
    parser.add_argument("--banned-rate", type=float, default=0.08, help="Part d'annonces banni=1 (défaut : 0.08)")
    parser.add_argument("--reservations", type=int, default=12, help="Nombre de réservations (défaut : 12)")
    parser.add_argument("--photos", type=int, default=16, help="Nombre de photos à télécharger (défaut : 16)")
    parser.add_argument("--no-photos", action="store_true", help="Ne pas télécharger de photos (Publication.image = NULL)")
    parser.add_argument("--force-photos", action="store_true", help="Télécharger à nouveau les photos déjà présentes")
    parser.add_argument("--seed", type=int, default=42, help="Graine des données fictives (défaut : 42)")
    parser.add_argument("--db", type=Path, default=None, help="Chemin de la base (défaut : database/parkshare.db)")
    parser.add_argument("--reset", action="store_true", help="Effacer les données de User/Publication/Reservation avant l'insertion")
    parser.add_argument("--yes", action="store_true", help="Confirmer la suppression avec --reset")
    args = parser.parse_args()
    if args.users < 1 or args.publications < 1 or args.reservations < 0 or args.photos < 0 or args.banned_users < 0:
        parser.error("--users et --publications doivent être >=1; les autres compteurs >=0")
    if not 0 <= args.banned_rate <= 1:
        parser.error("--banned-rate doit être entre 0 et 1")
    if args.reservations and args.users < 2:
        parser.error("Il faut au moins deux utilisateurs pour générer des réservations.")
    if args.reset and not args.yes:
        parser.error("--reset supprime les données existantes; ajoute --yes pour confirmer.")
    return args


def main() -> int:
    global DATABASE
    args = parse_args()
    if args.db:
        DATABASE = args.db.resolve()
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
            utilisateurs, bannis = creer_utilisateurs(conn, rng, args.users, args.banned_users)
            publications = creer_publications(
                conn, rng, args.publications, utilisateurs, noms_photos, args.banned_rate
            )
            reservations = creer_reservations(
                conn, rng, args.reservations, utilisateurs, bannis, publications
            )

        visibles = sum(
            1 for (_, auteur, _, visible) in publications if visible and auteur not in bannis
        )
        print(
            f"Créé : {len(utilisateurs)} utilisateurs ({len(bannis)} bannis), "
            f"{len(publications)} annonces ({visibles} visibles pour l'app), "
            f"{reservations} réservations"
        )
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
