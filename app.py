from flask import Flask, render_template
from modules.Recherche import Bp_recherche
from Database import bd
from stationnement import bp_stationnement
from pathlib import Path
import os
app = Flask(__name__, static_url_path='')
app.secret_key = os.getenv("SECRET_SESSION")

app.register_blueprint(Bp_recherche, url_prefix='/Recherche')
bd.init_database()
app.register_blueprint(bp_stationnement, url_prefix='/stationnement')


@app.route('/')
def index():
    """Affiche l'accueil"""
    return render_template('index.jinja', Entete="Accueil",
                           message="PARKSHARE encore en cours de developememnt")

