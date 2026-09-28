import sqlite3
from .objects import publication
import json

from click import command
DBNAME = "Database/PARKSHARE.db"



def init_database():
    _create_user_table()
    _create_publication_table()
    _create_reservation_table()
    _create_admin_user()
    _create_empty_publication()

def get_publications(params):
    conn = _create_connection()
    cursor = conn.cursor()
    command = 'SELECT * FROM  Publication WHERE city LIKE ? AND DATE(start) <= DATE(?) AND DATE(end) >= DATE(?)'
    cursor.execute(command, (params.get('city'), params.get('start'), params.get('end'),))
    results = cursor.fetchall()
    _close_connection(conn,cursor)

    publications = []
    for item in results:
        publications.append(publication(item[0],item[1],item[2],item[3],item[4],item[5],item[6],item[7],item[8],item[9],item[10]))

    return publications

def get_publication_t():
    conn = _create_connection()
    cursor = conn.cursor()
    command = 'SELECT * FROM  Publication WHERE ville LIKE ?'
    cursor.execute(command, ('ville',))
    res = cursor.fetchall()
    _close_connection(conn,cursor)
    return res


def _create_connection():
    son = sqlite3.connect('dsdfs')
    cus = son.cursor()
    son.commit()
    
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

def _create_admin_user():
    command = "INSERT INTO User (id, nom, prenom, mdp)"\
    " VALUES (NULL, 'admin', 'prenom', 'mdp')"
    conn = _create_connection()
    cursor = conn.cursor()
    cursor.execute(command)
    _close_connection(conn, cursor)

def _create_empty_publication():
    command = "INSERT INTO Publication"\
    " VALUES (NULL, (SELECT id FROM User WHERE nom = 'admin'), 'address', 0 , '1970-01-01', '3000-01-01','ville','extérieur', NULL ,30,30)"
    conn = _create_connection()
    cursor = conn.cursor()
    cursor.execute(command)
    _close_connection(conn, cursor)


def _create_publication_table():
    conn = _create_connection()
    cursor = conn.cursor()
    command = "CREATE TABLE IF NOT EXISTS Publication (id INTEGER PRIMARY KEY AUTOINCREMENT, " \
    "author INTEGER NOT NULL ,address TEXT NOT NULL, price DOUBLE NOT NULL, start DATE NOT NULL, end DATE NOT NULL, " \
    "city TEXT NOT NULL, location TEXT, image TEXT, place_max INTEGER NOT NULL, place_open INTEGER NOT NULL,FOREIGN KEY(author) REFERENCES User(id))"
    cursor.execute(command)
    _close_connection(conn, cursor)


def _create_reservation_table():
    conn = _create_connection()
    cursor = conn.cursor()
    command = "CREATE TABLE IF NOT EXISTS Reservation (id INTEGER PRIMARY KEY AUTOINCREMENT," \
    "publication INTEGER NOT NULL, debut DATETIME NOT NULL, fin DATETIME NOT NULL)"
    cursor.execute(command)
    _close_connection(conn, cursor)



