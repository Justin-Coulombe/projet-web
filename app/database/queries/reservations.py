from venv import create
from app.database.connection import create_connection, close_connection
from app.database.objects import reservation, publication


def create_reservation_table():
    conn = create_connection()
    cursor = conn.cursor()

    command = """
        CREATE TABLE IF NOT EXISTS Reservation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client INTEGER NOT NULL,
            publication INTEGER NOT NULL,
            debut DATETIME NOT NULL,
            fin DATETIME NOT NULL,
            FOREIGN KEY (publication)
                REFERENCES Publication(id),
            FOREIGN KEY (client) REFERENCES User(id)

        )
    """

    cursor.execute(command)
    close_connection(conn, cursor)


def add_Reservation(user_id, debut, fin, publication_id):
    conn = create_connection()
    cursor = conn.cursor()

    command = """
        SELECT banni
        FROM Publication
        WHERE id = ?
    """

    cursor.execute(command, (publication_id,))
    result1 = cursor.fetchone()

    if result1 is None:
        close_connection(conn, cursor)
        return False

    banni = result1[0]
    print(f"ban : {banni}")
    if banni == 1:
        close_connection(conn, cursor)
        return False

    command = """
        INSERT INTO Reservation (
            client,
            publication,
            debut,
            fin
        )
        VALUES (?, ?, ?, ?)
    """

    cursor.execute(
        command,
        (user_id, publication_id, debut, fin)
    )

    close_connection(conn, cursor)
    return True


def get_reservation_by_user(user_id):
    conn = create_connection()

    try:
        cursor = conn.cursor()

        command = """
            SELECT
                r.id,
                r.client,
                r.debut,
                r.fin,
                p.id,
                p.author,
                p.address,
                p.prix,
                p.ville,
                p.emplacement,
                p.image,
                p.placetotal,
                p.banni
            FROM Reservation r
            JOIN Publication p ON p.id = r.publication
            WHERE r.client = ?
            ORDER BY r.debut DESC
        """

        cursor.execute(command, (user_id,))
        results = cursor.fetchall()

        reservations = []

        for item in results:
            pub = publication(
                item[4], item[5], item[6],
                item[7], item[8], item[9],
                item[10], item[11], item[12]
            )

            reservations.append(
                reservation(
                    item[0],
                    item[1],
                    item[2],
                    item[3],
                    pub
                )
            )

        return reservations

    finally:
        conn.close()

def get_reservations_by_owner(owner_id):
    """Retourne les réservations des stationnements d'un propriétaire."""

    conn = create_connection()

    try:
        cursor = conn.cursor()

        command = """
            SELECT
                r.id,
                r.debut,
                r.fin,
                p.id,
                p.address,
                p.ville
            FROM Reservation AS r
            JOIN Publication AS p
                ON r.publication = p.id
            WHERE p.author = ?
            ORDER BY r.debut ASC, r.id ASC
        """

        cursor.execute(command, (owner_id,))
        results = cursor.fetchall()

        reservations = []

        for row in results:
            reservations.append({
                "id": row[0],
                "debut": row[1],
                "fin": row[2],
                "publication_id": row[3],
                "address": row[4],
                "ville": row[5]
            })

        return reservations

    finally:
        conn.close()

def get_reservations_in_range(date_debut, date_fin):
    conn = create_connection()
    try:
        curseur = conn.cursor()
        query = """SELECT * FROM Reservation WHERE debut >= ? AND fin <= ? ORDER BY debut"""
        curseur.execute(query, (date_debut, date_fin,))
        res = curseur.fetchall()
        reservations = []
        for row in res:
            reservations.append(
                reservation(row[0], row[1],row[3],row[4],row[2]) 
            )
        return reservations
    finally:
        close_connection(conn, curseur)

def get_reservations_by_publication(pub_id):
    conn = create_connection()
    try:
        curseur = conn.cursor()
        query = """SELECT * FROM Reservation WHERE publication = ? ORDER BY debut"""
        curseur.execute(query, (pub_id,))
        res = curseur.fetchall()
        reservations = []
        for row in res:
            print(row)
            reservations.append(
                reservation(row[0], row[1],row[3],row[4],row[2]) 
            )
        return reservations
    finally:
        close_connection(conn, curseur)
