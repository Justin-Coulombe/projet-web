from flask import Flask, render_template
from modules.Publication import Bp_publication
from modules.API import Bp_api
from Database import bd
from stationnement import bp_stationnement
from pathlib import Path
import os


app = Flask(__name__, static_url_path='')
app.secret_key = os.getenv("SECRET_SESSION")

app.register_blueprint(Bp_publication, url_prefix='/publications')
app.register_blueprint(Bp_api, url_prefix='/API')
app.register_blueprint(bp_stationnement, url_prefix='/stationnement')
bd.init_database()

@app.route('/')
def index():
    """Affiche l'accueil"""
    publications = bd.get_sample_publications_limit(4)
    context = {'publications': publications}
    return render_template('index.jinja', Entete="Accueil",
                           message="PARKSHARE encore en cours de developememnt", context=context)

