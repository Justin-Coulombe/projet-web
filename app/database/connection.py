import sqlite3

DB_NAME = "database/parkshare.db"


def create_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def close_connection(connection, cursor):
    connection.commit()
    cursor.close()
    connection.close()