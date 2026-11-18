import sqlite3
from datetime import datetime
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
                REFERENCES Publication(id),
            FOREIGN KEY (client) REFERENCES User(id)

        )
    """

    cursor.execute(command)
    close_connection(conn, cursor)


def _places_disponibles(conn, publication_id, debut, fin):
    """Vérifie la capacité disponible sur toute la période."""

    publication = conn.execute(
        """
        SELECT p.placetotal, p.banni, p.author, u.banni
        FROM Publication p
        JOIN User u ON u.id = p.author
        WHERE p.id = ?
        """,
        (publication_id,)
    ).fetchone()

    if publication is None:
        return False, "Stationnement introuvable."

    capacite, publication_bannie, proprietaire, auteur_banni = publication

    if publication_bannie or auteur_banni:
        return False, "Ce stationnement n'est pas disponible."

    reservations = conn.execute(
        """
        SELECT debut, fin
        FROM Reservation
        WHERE publication = ?
          AND datetime(debut) < datetime(?)
          AND datetime(fin) > datetime(?)
        """,
        (publication_id, fin, debut)
    ).fetchall()

    # Chaque événement indique l'occupation d'une place.
    evenements = []

    for debut_res, fin_res in reservations:
        debut_res = datetime.fromisoformat(debut_res)
        fin_res = datetime.fromisoformat(fin_res)

        # On limite les événements à la période demandée.
        debut_effectif = max(debut_res, datetime.fromisoformat(debut))
        fin_effective = min(fin_res, datetime.fromisoformat(fin))

        if debut_effectif < fin_effective:
            evenements.append((debut_effectif, 1))
            evenements.append((fin_effective, -1))

    # À heure égale, une sortie précède une entrée.
    evenements.sort(key=lambda item: (item[0], item[1]))

    occupation = 0
    occupation_max = 0

    for _, variation in evenements:
        occupation += variation
        occupation_max = max(occupation_max, occupation)

    if occupation_max >= capacite:
        return False, "Aucune place disponible pour cette période."

    return True, "Une place est disponible pour cette période."


def verifier_disponibilite(publication_id, debut, fin):
    """Vérification informative, sans créer de réservation."""

    conn = create_connection()

    try:
        return _places_disponibles(conn, publication_id, debut, fin)
    finally:
        conn.close()


def creer_reservation(user_id, debut, fin, publication_id):
    """
    Vérifie et crée la réservation dans une seule transaction.
    Retourne (succes, message).
    """

    if user_id is None:
        return False, "Vous devez être connecté."

    # Import local pour éviter une dépendance circulaire.
    from app.services.reservation_manager import valider_periode

    debut, fin, erreur = valider_periode(debut, fin)

    if erreur:
        return False, erreur

    conn = create_connection()

    try:
        # Verrou d'écriture avant la vérification.
        conn.execute("BEGIN IMMEDIATE")

        utilisateur = conn.execute(
            "SELECT banni FROM User WHERE id = ?",
            (user_id,)
        ).fetchone()

        if utilisateur is None or utilisateur[0]:
            conn.rollback()
            return False, "Compte utilisateur non autorisé."

        proprietaire = conn.execute(
            "SELECT author FROM Publication WHERE id = ?",
            (publication_id,)
        ).fetchone()

        if proprietaire is None:
            conn.rollback()
            return False, "Stationnement introuvable."

        if proprietaire[0] == user_id:
            conn.rollback()
            return False, "Vous ne pouvez pas réserver votre propre stationnement."

        # Vérifier si l'utilisateur possède déjà une réservation
        # qui chevauche la période demandée.
        reservation_existante = conn.execute(
            """
            SELECT id
            FROM Reservation
            WHERE client = ?
            AND publication = ?
            AND datetime(debut) < datetime(?)
            AND datetime(fin) > datetime(?)
            LIMIT 1
            """,
            (user_id, publication_id, fin, debut)
        ).fetchone()

        if reservation_existante is not None:
            conn.rollback()
            return (
                False,
                "Vous avez déjà une réservation pour ce stationnement "
                "pendant cette période."
            )

        disponible, message = _places_disponibles(
            conn, publication_id, debut, fin
        )

        if not disponible:
            conn.rollback()
            return False, message

        conn.execute(
            """
            INSERT INTO Reservation (
                client, publication, debut, fin
            )
            VALUES (?, ?, ?, ?)
            """,
            (user_id, publication_id, debut, fin)
        )

        conn.commit()

        return True, "Votre réservation a été enregistrée."

    except sqlite3.Error:
        conn.rollback()
        raise

    finally:
        conn.close()


def add_Reservation(user_id, debut, fin, publication_id):
    """Compatibilité avec les anciens appels."""

    succes, _ = creer_reservation(
        user_id, debut, fin, publication_id
    )

    return succes


def get_reservation_by_user(user_id):
    conn = create_connection()

    try:
        cursor = conn.cursor()

        command = """
            SELECT
                r.id,
                r.client,
                r.debut,
                r.fin,
                p.id,
                p.author,
                p.address,
                p.prix,
                p.ville,
                p.emplacement,
                p.image,
                p.placetotal,
                p.banni
            FROM Reservation r
            JOIN Publication p ON p.id = r.publication
            WHERE r.client = ?
            ORDER BY r.debut DESC
        """

        cursor.execute(command, (user_id,))
        results = cursor.fetchall()

        reservations = []

        for item in results:
            pub = publication(
                item[4], item[5], item[6],
                item[7], item[8], item[9],
                item[10], item[11], item[12]
            )

            reservations.append(
                reservation(
                    item[0],
                    item[1],
                    item[2],
                    item[3],
                    pub
                )
            )

        return reservations

    finally:
        conn.close()


def get_reservations_by_owner(owner_id):
    """Retourne les réservations des stationnements d'un propriétaire."""

    conn = create_connection()

    try:
        cursor = conn.cursor()

        command = """
            SELECT
                r.id,
                r.debut,
                r.fin,
                p.id,
                p.address,
                p.ville,
                c.id,
                c.nom,
                c.prenom
            FROM Reservation AS r
            JOIN Publication AS p
                ON r.publication = p.id
            JOIN User AS c
                ON c.id = r.client
            WHERE p.author = ?
            ORDER BY r.debut ASC, r.id ASC
        """

        cursor.execute(command, (owner_id,))
        results = cursor.fetchall()

        reservations = []

        for row in results:
            reservations.append({
                "id": row[0],
                "debut": row[1],
                "fin": row[2],
                "publication_id": row[3],
                "address": row[4],
                "ville": row[5],
                "client_id": row[6],
                "client_nom": row[7],
                "client_prenom": row[8],
            })

        return reservations

    finally:
        conn.close()


def get_reservations_in_range(date_debut, date_fin):
    conn = create_connection()
    try:
        curseur = conn.cursor()
        query = """
            SELECT *
            FROM Reservation
            WHERE datetime(debut) < datetime(?)
            AND datetime(fin) > datetime(?)
            ORDER BY debut
        """
        curseur.execute(query, (date_fin, date_debut))
        res = curseur.fetchall()
        reservations = []
        for row in res:
            reservations.append(
                reservation(row[0], row[1], row[3], row[4], row[2])
            )
        return reservations
    finally:
        close_connection(conn, curseur)


def get_reservations_by_publication(pub_id):
    conn = create_connection()
    try:
        curseur = conn.cursor()
        query = """SELECT * FROM Reservation WHERE publication = ? ORDER BY debut"""
        curseur.execute(query, (pub_id,))
        res = curseur.fetchall()
        reservations = []
        for row in res:
            reservations.append(
                reservation(row[0], row[1], row[3], row[4], row[2])
            )
        return reservations
    finally:
        close_connection(conn, curseur)


def delete_reservation(reservation_id, client_id):
    """ supprime une réservation de la base de données"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
            DELETE from Reservation WHERE id = ? and client = ?
                     """,
        (reservation_id, client_id)
    )
    close_connection(conn, cursor)


def update_reservation(reservation_id, client_id, debut, fin):
    """met à jour une réservation"""
    if client_id is None:
        return False, "Vous devez être connecté."

    from app.services.reservation_manager import valider_periode

    debut, fin, erreur = valider_periode(debut, fin)

    if erreur:
        return False, erreur

    conn = create_connection()

    try:
        conn.execute("BEGIN IMMEDIATE")

        existante = conn.execute(
            "SELECT client, publication FROM Reservation WHERE id = ?",
            (reservation_id,)
        ).fetchone()

        if existante is None:
            conn.rollback()
            return False, "Réservation introuvable."

        client, publication_id = existante

        if client != client_id:
            conn.rollback()
            return False, "Vous ne pouvez pas modifier cette réservation."


        conn.execute(
            "DELETE FROM Reservation WHERE id = ?",
            (reservation_id,)
        )

        disponible, message = _places_disponibles(
            conn, publication_id, debut, fin
        )

        if not disponible:
            conn.rollback()
            return False, message

        conn.execute(
            "INSERT INTO Reservation (client, publication, debut, fin) "
            "VALUES (?, ?, ?, ?)",
            (client_id, publication_id, debut, fin)
        )

        conn.commit()
        return True, "Votre réservation a été modifiée."

    except sqlite3.Error:
        conn.rollback()
        raise

    finally:
        conn.close()
