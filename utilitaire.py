import hashlib, logging
from flask import Flask, render_template

app = Flask(__name__, static_url_path='')
app.logger.setLevel(logging.INFO)

def hacher_mdp(mdp_en_clair):
    """Hache le mot de passe"""
    return hashlib.sha512(mdp_en_clair.encode()).hexdigest()