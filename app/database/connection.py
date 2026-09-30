import os
import sqlite3


DB_DIR = "database"
DB_NAME = os.path.join(DB_DIR, "parkshare.db")


def create_connection():
    os.makedirs(DB_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def close_connection(connection, cursor):
    connection.commit()
    cursor.close()
    connection.close()