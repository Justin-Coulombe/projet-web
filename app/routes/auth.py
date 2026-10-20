"""Authentification validée côté serveur, réponses AJAX + fallback HTML."""
import sqlite3
from functools import wraps
from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.database.queries.users import add_user, get_user_by_email
from app.form_validation import valider_identite, valider_mot_de_passe
from app.form_responses import fail, success, wants_json

bp_auth = Blueprint('auth', __name__)


@bp_auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('auth/register.jinja')

    clean, errors = valider_identite(request.form)
    password = request.form.get('password', '')
    confirm = request.form.get('password_confirm', '')
    errors.update(valider_mot_de_passe(password))
    if confirm != password:
        errors['password_confirm'] = 'Les mots de passe ne correspondent pas.'
    if 'email' in clean and get_user_by_email(clean['email']) is not None:
        errors['email'] = 'Ce courriel est déjà utilisé.'
    if errors:
        return fail(errors, 'auth/register.jinja')

    try:
        add_user(clean['nom'], clean['prenom'], clean['email'], generate_password_hash(password))
    except sqlite3.IntegrityError:
        return fail({'email': 'Ce courriel est déjà utilisé.'}, 'auth/register.jinja', status=409)

    user = get_user_by_email(clean['email'])
    if user is None:
        return fail({'_form': 'Impossible de créer le compte pour le moment.'}, 'auth/register.jinja', status=503)
    session.clear()
    session['user_id'] = user['id']
    return success(url_for('index'), message='Bienvenue sur ParkShare !')


@bp_auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login.jinja')

    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    _, errors = valider_identite({'email': email}, prenom=False, nom=False)
    if not password:
        errors['password'] = 'Le mot de passe est obligatoire.'
    if errors:
        return fail(errors, 'auth/login.jinja')

    user = get_user_by_email(email)
    if user is None or not check_password_hash(user['mdp'], password):
        return fail({'password': 'Courriel ou mot de passe incorrect.'}, 'auth/login.jinja', status=401)
    session.clear()
    session['user_id'] = user['id']
    return success(url_for('index'), message='Connexion réussie.')


@bp_auth.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return success(url_for('index'), message='Déconnexion réussie.')


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session:
            if wants_json() or request.path.startswith('/api/'):
                return jsonify(ok=False, errors={'_form': 'Connectez-vous pour continuer.'}), 401
            return redirect(url_for('auth.login'))
        return view(*args, **kwargs)
    return wrapped_view
