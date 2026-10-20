"""Contrôle CSRF et limite de taille pour les formulaires / API mutatrices."""
import hmac
import secrets
from flask import jsonify, render_template, request, session
from werkzeug.exceptions import RequestEntityTooLarge


def install_security(app):
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

    @app.before_request
    def protect_mutations():
        if '_csrf' not in session:
            session['_csrf'] = secrets.token_urlsafe(32)
        if request.method not in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            return None
        provided = request.headers.get('X-CSRFToken') or request.form.get('_csrf', '')
        valid = isinstance(provided, str) and hmac.compare_digest(session['_csrf'], provided)
        if not valid:
            if request.path.startswith('/api/') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(ok=False, errors={'_form': 'Session expirée, rechargez la page.'}), 400
            return 'Session expirée. Rechargez la page et réessayez.', 400
        return None

    @app.context_processor
    def expose_csrf():
        return {'csrf_token': lambda: session.get('_csrf', '')}

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(exc):
        if request.path.startswith('/api/') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(ok=False, errors={'image': 'Fichier trop volumineux (2 Mo par photo).'}), 413
        return 'La requête est trop volumineuse.', 413
