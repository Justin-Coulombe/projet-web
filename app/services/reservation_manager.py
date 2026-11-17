from app.database.queries.reservations import *
from app.database.queries.publications import get_publications_by_id
from datetime import datetime


def verifier_si_disponible(pub_id, date_debut, date_fin):
    reservations = get_reservations_by_publication(pub_id)
    publication = get_publications_by_id(pub_id)

    debut = datetime.fromisoformat(date_debut)
    fin = datetime.fromisoformat(date_fin)

    chevauchements = 0
    for res in reservations:
        debut_res = datetime.fromisoformat(res.start)
        fin_res = datetime.fromisoformat(res.end)
        if debut_res < fin and fin_res > debut:
            chevauchements += 1

    if chevauchements < publication.placeTotal:
        return True, "place disponible"

    return False, "la période demandée chevauche les réservations actuelles"