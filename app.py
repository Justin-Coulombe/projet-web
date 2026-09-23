from flask import Flask, render_template
from modules.Recherche import Bp_recherche
from Database import bd

app = Flask(__name__)
app.register_blueprint(Bp_recherche, url_prefix='/Recherche')
bd.init_database()

@app.route('/')
def index():
    """Affiche l'accueil"""
    return render_template('index.jinja', Entete="Accueil",
                           message="PARKSHARE encore en cours de developememnt")
