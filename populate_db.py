"""
Populate (and, if needed, create) the ParkShare SQLite database with fake data.

Schema (matches the provided CREATE TABLE statements):
    User(id, nom, prenom, email UNIQUE, mdp)
    Publication(id, author -> User.id, address, prix, debut, fin, ville,
                emplacement, image, placemax, placedispo)
    Reservation(id, publication -> Publication.id, debut, fin)

- User: creates N users, guarantees at least one with nom = 'admin', email is unique.
- Publication: creates M publications, linked to a random existing user.
  `emplacement` is either 'interieur' or 'exterieur'. `image` is always left NULL.
  `placedispo` (spots available) never exceeds `placemax` (spots total).
- Reservation: left empty, as requested.

Usage:
    python populate_db.py
    python populate_db.py --users 20 --publications 50
    python populate_db.py --db PARKSHARE.db --users 10 --publications 30 --reset
    python populate_db.py --create                      # create tables if the db/tables don't exist yet
"""

import argparse
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_NAME = "PARKSHARE.db"  # expected to sit next to this script

# --- schema, matching the provided sqlite_master dump ---

SCHEMA = """
CREATE TABLE IF NOT EXISTS User (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    mdp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Publication (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author INTEGER NOT NULL,
    address TEXT NOT NULL,
    prix DOUBLE NOT NULL,
    debut DATETIME NOT NULL,
    fin DATETIME NOT NULL,
    ville TEXT NOT NULL,
    emplacement TEXT,
    image TEXT,
    placemax INTEGER NOT NULL,
    placedispo INTEGER NOT NULL,
    FOREIGN KEY (author) REFERENCES User(id)
);

CREATE TABLE IF NOT EXISTS Reservation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    publication INTEGER NOT NULL,
    debut DATETIME NOT NULL,
    fin DATETIME NOT NULL,
    FOREIGN KEY (publication) REFERENCES Publication(id)
);
"""

# --- fake data pools (kept simple, no external dependencies) ---

PRENOMS = [
    "Alice", "Bob", "Charlie", "David", "Emma", "Fatima", "Gabriel", "Hugo",
    "Isabelle", "Jacques", "Karim", "Léa", "Marc", "Nadia", "Olivier",
    "Patricia", "Quentin", "Rania", "Simon", "Théo",
]

NOMS = [
    "Tremblay", "Gagnon", "Roy", "Côté", "Bouchard", "Gauthier", "Morin",
    "Lavoie", "Fortin", "Gagné", "Ouellet", "Pelletier", "Bélanger",
    "Levesque", "Bergeron",
]

VILLES = [
    "Montréal", "Québec", "Laval", "Gatineau", "Longueuil", "Sherbrooke",
    "Trois-Rivières", "Terrebonne", "Saguenay", "Lévis",
]

RUES = [
    "rue Saint-Denis", "avenue du Parc", "boulevard René-Lévesque",
    "rue Sainte-Catherine", "rue Rachel", "avenue Mont-Royal",
    "rue Sherbrooke", "boulevard Saint-Laurent", "rue Ontario", "rue Notre-Dame",
]

EMPLACEMENTS = ["Intérieur", "Extérieur"]


def random_password(length=10):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(random.choice(chars) for _ in range(length))


def strip_accents(s):
    replacements = {
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "à": "a", "â": "a",
        "î": "i", "ï": "i",
        "ô": "o",
        "û": "u", "ù": "u", "ü": "u",
        "ç": "c",
    }
    for accented, plain in replacements.items():
        s = s.replace(accented, plain).replace(accented.upper(), plain.upper())
    return s


def make_email(prenom, nom, used_emails):
    base = strip_accents(f"{prenom}.{nom}").lower().replace(" ", "-")
    email = f"{base}@parkshare.com"
    suffix = 1
    while email in used_emails:
        suffix += 1
        email = f"{base}{suffix}@parkshare.com"
    used_emails.add(email)
    return email


def random_address():
    return f"{random.randint(1, 9999)} {random.choice(RUES)}"


def random_date_range():
    """Return (debut, fin) as 'YYYY-MM-DD HH:MM' strings, fin after debut."""
    debut = datetime(2026, 1, 1) + timedelta(days=random.randint(0, 300))
    fin = debut + timedelta(days=random.randint(1, 60))
    fmt = "%Y-%m-%d %H:%M"
    return debut.strftime(fmt), fin.strftime(fmt)


def create_users(cursor, count):
    """Insert `count` users, guaranteeing at least one admin. Returns list of new ids."""
    ids = []
    used_emails = set()

    # guaranteed admin account
    admin_email = make_email("admin", "admin", used_emails)
    cursor.execute(
        "INSERT INTO User (nom, prenom, email, mdp) VALUES (?, ?, ?, ?)",
        ("admin", "admin", admin_email, "admin"),
    )
    ids.append(cursor.lastrowid)

    for _ in range(count - 1):
        nom = random.choice(NOMS)
        prenom = random.choice(PRENOMS)
        email = make_email(prenom, nom, used_emails)
        mdp = random_password()
        cursor.execute(
            "INSERT INTO User (nom, prenom, email, mdp) VALUES (?, ?, ?, ?)",
            (nom, prenom, email, mdp),
        )
        ids.append(cursor.lastrowid)

    return ids


def create_publications(cursor, count, user_ids):
    for _ in range(count):
        author = random.choice(user_ids)
        address = random_address()
        prix = round(random.uniform(2.0, 25.0), 2)
        debut, fin = random_date_range()
        ville = random.choice(VILLES)
        emplacement = random.choice(EMPLACEMENTS)
        image = None  # always left null, as requested
        placemax = random.randint(1, 30)
        placedispo = random.randint(0, placemax)  # never more available than max

        cursor.execute(
            """INSERT INTO Publication
               (author, address, prix, debut, fin, ville, emplacement, image, placemax, placedispo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (author, address, prix, debut, fin, ville, emplacement, image, placemax, placedispo),
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=DB_NAME, help="Path to the sqlite db file")
    parser.add_argument("--users", type=int, default=15, help="Number of users to create")
    parser.add_argument("--publications", type=int, default=40, help="Number of publications to create")
    parser.add_argument("--reset", action="store_true", help="Delete existing User/Publication rows first")
    parser.add_argument("--create", action="store_true", help="Create tables (and db file) if they don't exist yet")
    args = parser.parse_args()

    if args.users < 1:
        parser.error("--users must be at least 1 (need at least the admin)")

    db_path = Path(__file__).resolve().parent / args.db
    if not db_path.exists() and not args.create:
        parser.error(f"Database not found: {db_path} (use --create to make it)")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    try:
        if args.create:
            cursor.executescript(SCHEMA)

        if args.reset:
            cursor.execute("DELETE FROM Reservation")
            cursor.execute("DELETE FROM Publication")
            cursor.execute("DELETE FROM User")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('Publication', 'User', 'Reservation')")

        user_ids = create_users(cursor, args.users)
        create_publications(cursor, args.publications, user_ids)

        conn.commit()
        print(f"Inserted {len(user_ids)} users (including 1 admin) and {args.publications} publications into {db_path}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
