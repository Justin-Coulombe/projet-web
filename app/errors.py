from flask import current_app, render_template, request
from werkzeug.exceptions import HTTPException


ERROR_PAGES = {
    400: (
        "Requête invalide",
        "La requête n'a pas pu être traitée. Vérifiez les "
        "informations envoyées ou rechargez la page.",
        "bi-exclamation-triangle"
    ),
    401: (
        "Authentification requise",
        "Vous devez vous connecter pour accéder à cette page.",
        "bi-lock"
    ),
    403: (
        "Accès refusé",
        "Vous n'avez pas les permissions nécessaires "
        "pour accéder à cette page.",
        "bi-shield-lock"
    ),
    404: (
        "Page introuvable",
        "La page que vous recherchez n'existe pas "
        "ou a été déplacée.",
        "bi-search"
    )
}


def error_response(error):
    code = error.code or 500

    titre, message, icone = ERROR_PAGES.get(
        code,
        (
            "Erreur du serveur",
            "Nous ne pouvons pas traiter votre demande "
            "pour le moment. Veuillez réessayer plus tard.",
            "bi-tools"
        )
    )

    response = error.get_response()

    is_api = request.path.startswith("/api/")
    is_ajax = (
        request.headers.get("X-Requested-With")
        == "XMLHttpRequest"
    )

    if is_api or is_ajax:
        response.set_data(current_app.json.dumps({
            "ok": False,
            "code": code,
            "error": message
        }))
        response.mimetype = "application/json"
        return response

    response.set_data(render_template(
        "errors/error.jinja",
        code=code,
        titre=titre,
        message=message,
        icone=icone
    ))
    response.mimetype = "text/html"

    return response


def register_error_handlers(app):

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        code = error.code or 500

        if code not in ERROR_PAGES and not (500 <= code < 600):
            return error

        return error_response(error)

    @app.errorhandler(500)
    def handle_internal_error(error):
        return error_response(error)