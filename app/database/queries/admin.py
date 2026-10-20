from app.database.connection import create_connection, close_connection

def create_table_admin():
    conn = create_connection()
    cursor = conn.cursor()

    command = """
        CREATE TABLE IF NOT EXISTS Admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            cle TEXT NOT NULL
        )
    """
    cursor.execute(command)
    close_connection(conn,cursor)


def add_admin():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO Admin VALUES(NULL, 'admin.test', 'abcd1234') ")
    close_connection(conn, cursor)


def get_admin_by_name_password(name, pwd):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Admin WHERE username = ? AND cle = ?", (name, pwd,))
    result = cursor.fetchone()
    close_connection(conn, cursor)
    return result

def get_admin_by_id(adminid):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Admin WHERE id = ?", (adminid,))
    result = cursor.fetchone()
    close_connection(conn, cursor)
    return result
    