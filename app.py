from flask import Flask, render_template


app = Flask(__name__, static_url_path='')


@app.route('/')
def index():
    """Affiche l'accueil"""
    return render_template('index.jinja', Entete="Accueil",
                           message="PARKSHARE encore en cours de developememnt")
