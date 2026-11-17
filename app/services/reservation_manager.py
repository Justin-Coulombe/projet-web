
"""Validation des périodes et logique des disponibilités."""

from datetime import datetime, timedelta

from app.database.queries.reservations import verifier_disponibilite


def valider_periode(date_debut, date_fin):
    """Valide et normalise les dates d'une réservation."""

    if not date_debut or not date_fin:
        return None, None, "Les deux dates sont obligatoires."

    try:
        debut = datetime.fromisoformat(date_debut)
        fin = datetime.fromisoformat(date_fin)
    except (ValueError, TypeError):
        return None, None, "Les dates fournies sont invalides."

    if debut.tzinfo is not None or fin.tzinfo is not None:
        return None, None, "Format de date non accepté."

    if debut <= datetime.now():
        return None, None, "La date de début doit être dans le futur."

    if fin - debut < timedelta(minutes=30):
        return (
            None,
            None,
            "La réservation doit durer au moins 30 minutes."
        )

    return (
        debut.strftime("%Y-%m-%d %H:%M:%S"),
        fin.strftime("%Y-%m-%d %H:%M:%S"),
        None
    )


def verifier_si_disponible(pub_id, date_debut, date_fin):
    """Valide la période et vérifie les places disponibles."""

    debut, fin, erreur = valider_periode(date_debut, date_fin)

    if erreur:
        return False, erreur

    return verifier_disponibilite(pub_id, debut, fin)