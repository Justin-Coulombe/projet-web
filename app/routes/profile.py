"""Modification de compte avec erreurs de validation par champ."""
import sqlite3
from flask import Blueprint, request, render_template, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from app.routes.auth import login_required
from app.database.queries.users import get_user_by_email, get_user_with_password, update_user, update_password
from app.form_validation import valider_identite, valider_mot_de_passe
from app.form_responses import fail, success

bp_profile = Blueprint('profile', __name__)


@bp_profile.route('/', methods=['GET', 'POST'])
@login_required
def edit():
    if request.method == 'GET':
        return render_template('profile/edit.jinja',
            success=request.args.get('success'),
            password_success=request.args.get('password_success'))

    clean, errors = valider_identite(request.form)
    if 'email' in clean:
        existing = get_user_by_email(clean['email'])
        if existing and existing['id'] != session['user_id']:
            errors['email'] = 'Ce courriel est déjà utilisé.'
    if errors:
        return fail(errors, 'profile/edit.jinja')
    try:
        update_user(session['user_id'], clean['prenom'], clean['nom'], clean['email'])
    except sqlite3.IntegrityError:
        return fail({'email': 'Ce courriel est déjà utilisé.'}, 'profile/edit.jinja', status=409)
    return success(url_for('profile.edit', success='Profil mis à jour.'), message='Profil mis à jour.')


@bp_profile.route('/password', methods=['POST'])
@login_required
def change_password():
    current = request.form.get('current_password', '')
    new = request.form.get('new_password', '')
    confirm = request.form.get('confirm_password', '')
    errors = valider_mot_de_passe(new, 'new_password')
    if not current:
        errors['current_password'] = 'Le mot de passe actuel est obligatoire.'
    if new != confirm:
        errors['confirm_password'] = 'Les mots de passe ne correspondent pas.'
    user = get_user_with_password(session['user_id'])
    if user is None:
        return fail({'_form': 'Session invalide. Reconnectez-vous.'}, 'profile/edit.jinja', status=401)
    if current and not check_password_hash(user['mdp'], current):
        errors['current_password'] = 'Mot de passe actuel incorrect.'
    if errors:
        return fail(errors, 'profile/edit.jinja')
    update_password(session['user_id'], generate_password_hash(new))
    return success(url_for('profile.edit', password_success='Mot de passe modifié.'), message='Mot de passe modifié.')
