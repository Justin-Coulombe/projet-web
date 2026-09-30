from app.database.queries.users import create_user_table
from app.database.queries.publications import create_publication_table
from app.database.queries.reservations import create_reservation_table


def init_database():
    create_user_table()
    create_publication_table()
    create_reservation_table()