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
                REFERENCES Publication(id)
            FOREIGN KEY (client) REFERENCES User(id)

        )
    """

    cursor.execute(command)
    close_connection(conn, cursor)


def add_Reservation(user_id, debut, fin, publication_id):
    conn = create_connection()
    cursor = conn.cursor()

    command = """
        SELECT placeactuel, disponibilite
        FROM Publication
        WHERE id = ?
    """

    cursor.execute(command, (publication_id,))
    result1 = cursor.fetchone()

    if result1 is None:
        close_connection(conn, cursor)
        return False

    placeactuel, disponibilite = result1

    if not disponibilite or placeactuel <= 0:
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

    n_placeactuel = placeactuel - 1

    command = """
        UPDATE Publication
        SET placeactuel = ?,
            disponibilite = ?
        WHERE id = ?
    """

    cursor.execute(
        command,
        (
            n_placeactuel,
            1 if n_placeactuel > 0 else 0,
            publication_id
        )
    )

    close_connection(conn, cursor)
    return True


def get_reservation_by_user(user_id):

    conn = create_connection()
    cursor = conn.cursor()

    command = """
        SELECT
        r.id,r.client,r.debut,
        r.fin,p.id,p.author,
        p.address, p.prix, p.debut, p.fin,
        p.ville, p.emplacement, p.image,
        p.placetotal, p.placeactuel, p.disponibilite
        FROM Reservation r
        JOIN Publication p ON p.id = r.publication
        WHERE r.client = ?
    """

    cursor.execute(command, (user_id,))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    reservations = []
    for item in results:
        pub = publication(
            item[4], item[5], item[6], item[7], item[8],
            item[9], item[10], item[11], item[12],
            item[13], item[14], item[15]
        )
        reservations.append(
            reservation(item[0], item[1], item[2], item[3], pub)
        )

    return reservations
