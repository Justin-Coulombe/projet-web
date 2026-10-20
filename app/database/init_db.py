from app.database.queries.users import create_user_table
from app.database.queries.publications import create_publication_table
from app.database.queries.reservations import create_reservation_table
from app.database.queries.admin import create_table_admin, add_admin

def init_database():
    create_user_table()
    create_publication_table()
    create_reservation_table()
    create_table_admin()
    add_admin()