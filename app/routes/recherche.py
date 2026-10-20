"""Ancienne URL de recherche : redirige sans faire de rendu d'un template supprimé."""
from flask import Blueprint, redirect, url_for

Bp_recherche = Blueprint('Recherche', __name__)

@Bp_recherche.route('', methods=['GET'])
def index():
    return redirect(url_for('publications.research'), code=308)
