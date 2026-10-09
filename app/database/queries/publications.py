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
            placetotal INTEGER NOT NULL,
            placeactuel INTEGER NOT NULL,
            disponibilite BOOLEAN NOT NULL DEFAULT TRUE,
            FOREIGN KEY (author) REFERENCES User(id)
        )
    """

    cursor.execute(command)
    close_connection(conn, cursor)


def ajouter_stationnement(
    address,
    prix,
    placetotal,
    placeactuel,
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
            placetotal,
            placeactuel
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,?)
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
            placetotal,
            placeactuel
        )
    )

    close_connection(conn, cursor)


def get_publications_with_city_date_location_location(params):
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
            placetotal,
            placeactuel,
            disponibilite
        FROM Publication
        WHERE ville LIKE ?
          AND DATE(debut) >= DATE(?)
          AND DATE(fin) <= DATE(?)
          AND emplacement LIKE ?
    """

    cursor.execute(
        command,
        (
            params.get("city"),
            params.get("start"),
            params.get("end"),
            params.get("filter"),
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
                item[9],
                item[10],
                item[11]
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
            placetotal,
            placeactuel,
            disponibilite
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
                item[9],
                item[10],
                item[11]
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
            placetotal,
            placeactuel,
            disponibilite
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
                item[9],
                item[10],
                item[11]
            )
        )

    return publications


def get_publications_by_user(user_id):
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
            placetotal,
            placeactuel,
            disponibilite
        from
        publication
        WHERE
        author = ?
    """

    cursor.execute(command, (user_id,))

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
                item[9],
                item[10],
                item[11]
            )
        )
    return publications


def update_publications(publication_id):

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
     UPDATE Publication
     SET placeactuel = placeactuel - 1,
        disponibilite = CASE
            WHEN placeactuel - 1 > 0 THEN TRUE
            ELSE FALSE
        END
       WHERE id = ?
       AND placeactuel > 0

     """,
     (publication_id)

    )
