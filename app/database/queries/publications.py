from app.database.connection import create_connection, close_connection
from app.database.objects import publication



def create_publication_table():
    conn = create_connection()
    cursor = conn.cursor()

    command = """
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
        )
    """

    cursor.execute(command)
    close_connection(conn, cursor)

def ajouter_stationnement(
    address,
    prix,
    place,
    debut,
    fin,
    ville,
    emplacement,
    image,
    id_author
):
    conn = create_connection()
    cursor = conn.cursor()

    command = """
        INSERT INTO Publication (
            author,
            address,
            prix,
            debut,
            fin,
            ville,
            emplacement,
            image,
            placemax,
            placedispo
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    cursor.execute(
        command,
        (
            id_author,
            address,
            prix,
            debut,
            fin,
            ville,
            emplacement,
            image,
            place,
            place
        )
    )

    close_connection(conn, cursor)

def get_publications_with_city_date(params):
    conn = create_connection()
    cursor = conn.cursor()

    command = """
        SELECT
            id,
            author,
            address,
            prix,
            debut,
            fin,
            ville,
            emplacement,
            image,
            placedispo
        FROM Publication
        WHERE ville LIKE ?
          AND DATE(debut) <= DATE(?)
          AND DATE(fin) >= DATE(?)
    """

    cursor.execute(
        command,
        (
            params.get("city"),
            params.get("start"),
            params.get("end")
        )
    )

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    publications = []

    for item in results:
        publications.append(
            publication(
                item[0],
                item[1],
                item[2],
                item[3],
                item[4],
                item[5],
                item[6],
                item[7],
                item[8],
                item[9]
            )
        )

    return publications


def get_all_publications():
    conn = create_connection()
    cursor = conn.cursor()

    command = """
        SELECT
            id,
            author,
            address,
            prix,
            debut,
            fin,
            ville,
            emplacement,
            image,
            placedispo
        FROM Publication
    """

    cursor.execute(command)

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    publications = []

    for item in results:
        publications.append(
            publication(
                item[0],
                item[1],
                item[2],
                item[3],
                item[4],
                item[5],
                item[6],
                item[7],
                item[8],
                item[9]
            )
        )

    return publications


def get_sample_publications_limit(limite):
    conn = create_connection()
    cursor = conn.cursor()

    command = """
        SELECT
            id,
            author,
            address,
            prix,
            debut,
            fin,
            ville,
            emplacement,
            image,
            placedispo
        FROM Publication
        ORDER BY RANDOM()
        LIMIT ?
    """

    cursor.execute(command, (limite,))

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    publications = []

    for item in results:
        publications.append(
            publication(
                item[0],
                item[1],
                item[2],
                item[3],
                item[4],
                item[5],
                item[6],
                item[7],
                item[8],
                item[9]
            )
        )

    return publications