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
            prix DOUBLE NOT NULL CHECK (prix >= 0.01 AND prix <= 1000),
            debut DATETIME NOT NULL,
            fin DATETIME NOT NULL,
            ville TEXT NOT NULL,
            emplacement TEXT,
            image TEXT,
            placetotal INTEGER NOT NULL CHECK (placetotal BETWEEN 1 AND 100),
            placeactuel INTEGER NOT NULL CHECK (placeactuel BETWEEN 0 AND placetotal),
            disponibilite BOOLEAN NOT NULL DEFAULT TRUE,
            latitude REAL,
            longitude REAL,
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
    id_author,
    latitude,
    longitude
):
    conn = create_connection()
    cursor = conn.cursor()


    command = """
        INSERT INTO Publication (
            author, address, prix, debut, fin,
            ville, emplacement, image,
            placetotal, placeactuel, disponibilite,
            latitude, longitude
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            1,
            latitude,
            longitude
        )
    )

    close_connection(conn, cursor)



def get_publications_with_city_date_location_location(params):
    conn = create_connection()

    try:
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
                disponibilite,
                latitude,
                longitude
            FROM Publication
            WHERE ville LIKE ?
              AND DATE(debut) >= DATE(?)
              AND DATE(fin) <= DATE(?)
              AND emplacement LIKE ?
              AND (SELECT banni FROM User WHERE id = author) = FALSE
    """

        cursor.execute(
            command,
            (
                params.get("city", "%"),
                params.get("start", "1970-01-01"),
                params.get("end", "3000-01-01"),
                params.get("filter", "%")
            )
        )

        results = cursor.fetchall()

        publications = []

        for item in results:
            publications.append(
                publication(
                    item[0],   # id
                    item[1],   # author
                    item[2],   # address
                    item[3],   # price
                    item[4],   # start
                    item[5],   # end
                    item[6],   # city
                    item[7],   # location
                    item[8],   # img
                    item[9],   # open_place
                    item[10],  # place_use
                    item[11],  # open
                    item[12],  # latitude
                    item[13]   # longitude
                )
            )

        return publications

    finally:
        conn.close()


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
        FROM Publication WHERE (SELECT banni FROM User WHERE id = author) = FALSE
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
        WHERE (SELECT banni FROM User WHERE id = author) = FALSE
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
        author = ? AND (SELECT banni FROM User WHERE id = author) = FALSE
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
    emplacement,
    latitude=None,
    longitude=None
):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE Publication
        SET address = ?,
            prix = ?,
            placetotal = ?,
            placeactuel = ?,
            disponibilite = CASE WHEN ? > 0 THEN 1 ELSE 0 END,
            debut = ?,
            fin = ?,
            ville = ?,
            emplacement = ?,
            latitude = COALESCE(?, latitude),
            longitude = COALESCE(?, longitude)
        WHERE id = ?
        """,
        (
            address,
            prix,
            placetotal,
            placeactuel,
            placeactuel,
            debut,
            fin,
            ville,
            emplacement,
            latitude,
            longitude,
            publication_id
        )
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

def get_publication_coordinates(publication_id):
    conn = create_connection()

    try:
        row = conn.execute(
            """
            SELECT latitude, longitude
            FROM Publication
            WHERE id = ?
            """,
            (publication_id,)
        ).fetchone()

        return row
    finally:
        conn.close()


def get_publications_in_bounds(
    south, north, west, east,
    emplacement="Tous",
    debut=None,
    fin=None,
    ville=None
):
    conn = create_connection()

    try:
        conditions = [
            "latitude BETWEEN ? AND ?",
            "longitude BETWEEN ? AND ?",
            "disponibilite = 1",
            "placeactuel > 0"
        ]

        params = [south, north, west, east]

        if ville:
            conditions.append("ville = ?")
            params.append(ville)

        if emplacement in ("Intérieur", "Extérieur"):
            conditions.append("emplacement = ?")
            params.append(emplacement)

        if debut:
            conditions.append("debut <= ?")
            params.append(debut)

        if fin:
            conditions.append("fin >= ?")
            params.append(fin)

        sql = f"""
            SELECT
                id, address, ville, prix, emplacement,
                image, placetotal, placeactuel,
                latitude, longitude, debut, fin
            FROM Publication
            WHERE {' AND '.join(conditions)}
            ORDER BY id DESC
            LIMIT 50
        """

        rows = conn.execute(sql, params).fetchall()

        return [
            {
                "id": row[0],
                "address": row[1],
                "city": row[2],
                "price": row[3],
                "location": row[4],
                "img": row[5],
                "open_place": row[6],
                "place_use": row[7],
                "latitude": row[8],
                "longitude": row[9],
                "start": row[10],
                "end": row[11]
            }
            for row in rows
        ]

    finally:
        conn.close()

def delete_publication_by_id(publication_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE Publication
        SET disponibilite = 0
        WHERE id = ?
        """,
        (publication_id,)
    )

    return cursor.rowcount

    close_connection(conn, cursor)