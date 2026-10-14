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
            placetotal INTEGER NOT NULL CHECK (placetotal > 0),
            placeactuel INTEGER NOT NULL CHECK (placeactuel >= 0),
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
            placeactuel,
            disponibilite
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            placeactuel,
            1
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


def get_publications_by_id(publication_id):
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
            id = ?
        """

    cursor.execute(command, (publication_id,))

    publications = cursor.fetchone()

    cursor.close()
    conn.close()

    if publications is None:
        return None

    resultat = publication(
        publications[0],
        publications[1],
        publications[2],
        publications[3],
        publications[4],
        publications[5],
        publications[6],
        publications[7],
        publications[8],
        publications[9],
        publications[10],
        publications[11]
    )
    return resultat


def update_publication(
        publication_id,
        address,
        prix,
        placetotal,
        placeactuel,
        debut,
        fin,
        ville,
        emplacement):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
       UPDATE publication
       SET address = ?,
       prix = ?,
       placetotal = ?,
       placeactuel = ?,
       debut = ?,
       fin = ?,
       ville = ?,
       emplacement = ?
       WHERE id = ?
        """,
        (address, prix, placetotal, placeactuel, debut,
         fin, ville, emplacement, publication_id)
    )

    close_connection(conn, cursor)


def update_image(publication_id, img):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
          UPDATE publication
          SET image = ?
          WHERE id = ?
            """,
        (img, publication_id)
    )

    close_connection(conn, cursor)


def delete_publication(publication_id, user_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM Publication
        WHERE id = ? AND author = ?
                """,
        (publication_id, user_id)
    )
    close_connection(conn, cursor)
