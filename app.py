from flask import Flask, render_template
from modules.Recherche import Bp_recherche
from Database import bd
from stationnement import bp_stationnement
from pathlib import Path
import os
app = Flask(__name__, static_url_path='')
app.secret_key = os.getenv("SECRET_SESSION")


app.config['ROUTE_VERS_AJOUTS'] = "/images/stationnement/"

app.config['CHEMIN_VERS_AJOUTS'] = os.path.join(
    app.instance_path.replace("instance", ""),
    "static",
    "images",
    "stationnement",
)
app.register_blueprint(Bp_recherche, url_prefix='/Recherche')
bd.init_database()
app.register_blueprint(bp_stationnement, url_prefix='/stationnement')


@app.route('/')
def index():
    """Affiche l'accueil"""
    return render_template('index.jinja', Entete="Accueil",
                           message="PARKSHARE encore en cours de developememnt")


@app.route('/ad')
def deck():
    """Affiche l'accueil"""
    return render_template('ad.jinja')

def verifier_image(id_image):
    """Vérifie l'existence de l'image"""

    chemin = Path(f"static/images/stationnement/{id_image}")

    if chemin.exists():
        return f"/images/stationnement/{id_image}"

    return "/images/stationnement/image.png"
