from app.database.connection import create_connection, close_connection


def create_user_table():
    conn = create_connection()
    cursor = conn.cursor()

    command = """
        CREATE TABLE IF NOT EXISTS User (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            mdp TEXT NOT NULL
        )
    """

    cursor.execute(command)
    close_connection(conn, cursor)


def add_user(nom, prenom, email, mdp):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO User (nom, prenom, email, mdp)
        VALUES (?, ?, ?, ?)
        """,
        (nom, prenom, email, mdp)
    )

    close_connection(conn, cursor)


def get_user_by_email(email):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, nom, prenom, email, mdp
        FROM User
        WHERE email = ?
        """,
        (email,)
    )

    row = cursor.fetchone()

    close_connection(conn, cursor)

    if row is None:
        return None

    return {
        "id": row[0],
        "nom": row[1],
        "prenom": row[2],
        "email": row[3],
        "mdp": row[4]
    }


def get_user_by_id(user_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, nom, prenom, email
        FROM User
        WHERE id = ?
        """,
        (user_id,)
    )

    row = cursor.fetchone()

    close_connection(conn, cursor)

    if row is None:
        return None

    return {
        "id": row[0],
        "nom": row[1],
        "prenom": row[2],
        "email": row[3]
    }

def update_user(user_id, prenom, nom, email):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE User
        SET prenom = ?, nom = ?, email = ?
        WHERE id = ?
        """,
        (prenom, nom, email, user_id)
    )

    close_connection(conn, cursor)


def update_password(user_id, password_hash):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE User
        SET mdp = ?
        WHERE id = ?
        """,
        (password_hash, user_id)
    )

    close_connection(conn, cursor)


def get_user_with_password(user_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, nom, prenom, email, mdp
        FROM User
        WHERE id = ?
        """,
        (user_id,)
    )

    row = cursor.fetchone()

    close_connection(conn, cursor)

    if row is None:
        return None

    return {
        "id": row[0],
        "nom": row[1],
        "prenom": row[2],
        "email": row[3],
        "mdp": row[4]
    }