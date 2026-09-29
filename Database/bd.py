import sqlite3
DBNAME = "Database/PARKSHARE.db"


def init_database():
    _create_user_table()
    _create_publication_table()
    _create_reservation_table()


def _create_connection():
    return sqlite3.connect(DBNAME)


def _close_connection(connection, curseur):
    connection.commit()
    curseur.close()
    connection.close()


def _create_user_table():
    conn = _create_connection()
    cursor = conn.cursor()
    command = "CREATE TABLE IF NOT EXISTS User (id INTEGER PRIMARY KEY AUTOINCREMENT, " \
        " nom TEXT NOT NULL, prenom TEXT NOT NULL, mdp TEXT NOT NULL)"
    cursor.execute(command)
    _close_connection(conn, cursor)


def _create_publication_table():
    conn = _create_connection()
    cursor = conn.cursor()
    command = "CREATE TABLE IF NOT EXISTS Publication (id INTEGER PRIMARY KEY AUTOINCREMENT, " \
        "author INTEGER NOT NULL ,address TEXT NOT NULL, prix DOUBLE NOT NULL, debut DATETIME NOT NULL, fin DATETIME NOT NULL, " \
        "ville TEXT NOT NULL, emplacement TEXT, image TEXT, place INTEGER NOT NULL,FOREIGN KEY(author) REFERENCES User(id))"
    cursor.execute(command)
    _close_connection(conn, cursor)


def _create_reservation_table():
    conn = _create_connection()
    cursor = conn.cursor()
    command = "CREATE TABLE IF NOT EXISTS Reservation (id INTEGER PRIMARY KEY AUTOINCREMENT," \
        "publication INTEGER NOT NULL, debut DATETIME NOT NULL, fin DATETIME NOT NULL)"
    cursor.execute(command)
    _close_connection(conn, cursor)


def ajouter_stationnement(address, prix, place, debut, fin, ville, emplacement, image, id_author):
    """Ajouter une place à la bd"""
    conn = _create_connection()
    cursor = conn.cursor()
    command = "INSERT INTO Publication (address,prix,debut,fin,ville,emplacement,image,place,author) VALUES(?,?,?,?,?,?,?,?,?)"
    cursor.execute(command, (address, prix, place, debut,
                   fin, ville, emplacement, image, id_author))
    _close_connection(conn, cursor)
