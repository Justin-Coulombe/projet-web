from flask import Flask, render_template
from modules.Recherche import Bp_recherche

app = Flask(__name__)

app.register_blueprint(Bp_recherche, url_prefix='/Recherche')

@app.route('/')
def index():
    """Affiche l'accueil"""
    return render_template('index.jinja', Entete="Accueil",
                           message="PARKSHARE encore en cours de developememnt")
