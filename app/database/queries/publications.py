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
            ville TEXT NOT NULL,
            emplacement TEXT,
            image TEXT,
            placetotal INTEGER NOT NULL CHECK (placetotal BETWEEN 1 AND 100),
            banni BOOLEAN NOT NULL DEFAULT TRUE,
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
    ville,
    emplacement,
    image,
    id_author,
    latitude,
    longitude
):
    conn = create_connection()

    try:
        command = """
            INSERT INTO Publication (
                author,
                address,
                prix,
                ville,
                emplacement,
                image,
                placetotal,
                banni,
                latitude,
                longitude
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        conn.execute(
            command,
            (
                id_author,
                address,
                prix,
                ville,
                emplacement,
                image,
                placetotal,
                0,
                latitude,
                longitude
            )
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

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
            ville,
            emplacement,
            image,
            placetotal,
            banni
        FROM Publication WHERE banni = FALSE AND (SELECT banni FROM User WHERE id = author) = FALSE
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
                item[8]
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
            ville,
            emplacement,
            image,
            placetotal,
            banni
        FROM Publication
        WHERE banni = FALSE AND (SELECT banni FROM User WHERE id = author) = FALSE
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
                item[8]
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
            ville,
            emplacement,
            image,
            placetotal,
            banni
        from
        publication
        WHERE
        banni = FALSE AND author = ? AND (SELECT banni FROM User WHERE id = author) = FALSE
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
                item[8]                
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
                ville,
                emplacement,
                image,
                placetotal,
                banni
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
    )
    return resultat




def update_publication(
    publication_id,
    address,
    prix,
    placetotal,
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
            "p.latitude BETWEEN ? AND ?",
            "p.longitude BETWEEN ? AND ?",
            "p.banni = 0",
            "u.banni = 0"
        ]

        params = [south, north, west, east]

        if ville:
            conditions.append("p.ville = ?")
            params.append(ville)

        if emplacement in ("Intérieur", "Extérieur"):
            conditions.append("p.emplacement = ?")
            params.append(emplacement)

        if debut and fin:

            conditions.append("""
                (
                    SELECT COUNT(*)
                    FROM Reservation r
                    WHERE r.publication = p.id
                      AND datetime(r.debut) <= datetime(?)
                      AND datetime(r.fin) > datetime(?)
                ) < p.placetotal
            """)

            params.extend([debut, debut])

            conditions.append("""
                NOT EXISTS (
                    SELECT 1
                    FROM Reservation evt
                    WHERE evt.publication = p.id
                      AND datetime(evt.debut) > datetime(?)
                      AND datetime(evt.debut) < datetime(?)
                      AND (
                          SELECT COUNT(*)
                          FROM Reservation active
                          WHERE active.publication = p.id
                            AND datetime(active.debut)
                                <= datetime(evt.debut)
                            AND datetime(active.fin)
                                > datetime(evt.debut)
                      ) >= p.placetotal
                )
            """)

            params.extend([debut, fin])

        sql = f"""
            SELECT
                p.id,
                p.address,
                p.ville,
                p.prix,
                p.emplacement,
                p.image,
                p.placetotal,
                p.latitude,
                p.longitude
            FROM Publication p
            JOIN User u ON u.id = p.author
            WHERE {' AND '.join(conditions)}
            ORDER BY p.id DESC
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
                "total": row[6],
                "latitude": row[7],
                "longitude": row[8]
            }
            for row in rows
        ]

    finally:
        conn.close()

def ban_publication_by_id(publication_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE Publication
        SET banni = 1
        WHERE id = ?
        """,
        (publication_id,)
    )
    count = cursor.rowcount
    close_connection(conn, cursor)
    return count

    