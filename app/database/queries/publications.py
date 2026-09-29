from app.database.connection import create_connection, close_connection


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