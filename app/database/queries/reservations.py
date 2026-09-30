from app.database.connection import create_connection, close_connection


def create_reservation_table():
    conn = create_connection()
    cursor = conn.cursor()

    command = """
        CREATE TABLE IF NOT EXISTS Reservation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            publication INTEGER NOT NULL,
            debut DATETIME NOT NULL,
            fin DATETIME NOT NULL,

            FOREIGN KEY (publication)
                REFERENCES Publication(id)
        )
    """

    cursor.execute(command)
    close_connection(conn, cursor)