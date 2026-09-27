from flask import Flask, render_template
from station import bp_station

app = Flask(__name__, static_url_path='')
app.register_blueprint(bp_station, url_prefix='/station')


@app.route('/')
def index():
    """Affiche l'accueil"""
    return render_template('index.jinja', Entete="Accueil",
                           message="PARKSHARE encore en cours de developememnt")


@app.route('/ad')
def deck():
    """Affiche l'accueil"""
    return render_template('ad.jinja')
