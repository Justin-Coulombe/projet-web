"""Réponses JSON pour AJAX, avec fallback HTML pour les formulaires traditionnels."""
from flask import jsonify, redirect, render_template, request


def wants_json():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def fail(errors, template, *, status=422, **context):
    if wants_json():
        return jsonify(ok=False, errors=errors), status
    # Le JS n'est pas indispensable : le serveur fournit aussi les erreurs.
    return render_template(template, errors=errors, **context), status


def success(url, *, message='Enregistré.'):
    if wants_json():
        return jsonify(ok=True, redirect=url, message=message)
    return redirect(url, code=303)
