import os

from flask import Flask, render_template, session, g

from app.database.init_db import init_database
from app.database.queries.users import get_user_by_id
from dotenv import load_dotenv
from app.routes.profile import bp_profile
from app.routes.stationnement import bp_stationnement
from app.routes.api import Bp_api
from app.routes.publication import Bp_publication
from app.database.queries.publications import get_sample_publications_limit

load_dotenv()


def create_app():
    app = Flask(__name__)

    app.secret_key = os.getenv(
        "SECRET_KEY",
        "dev-secret-key-change-me"
    )

    init_database()

    from app.routes.auth import bp_auth
    from app.routes.recherche import Bp_recherche

    app.register_blueprint(
        bp_auth,
        url_prefix="/auth"
    )

    app.register_blueprint(
        Bp_recherche,
        url_prefix="/Recherche"
    )

    @app.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")

        if user_id is None:
            g.user = None
        else:
            g.user = get_user_by_id(user_id)

    @app.route("/")
    def index():
        publications = get_sample_publications_limit(5)

        context = {
            "publications": publications
        }

        return render_template(
            "index.jinja",
            Entete="Accueil",
            message="PARKSHARE encore en cours de développement",
            context=context
    )

    app.register_blueprint(
    bp_profile,
    url_prefix="/profile"
    )

    app.register_blueprint(
    bp_stationnement,
    url_prefix="/stationnement"
    )

    app.register_blueprint(
    Bp_api,
    url_prefix="/api"
    )
    app.register_blueprint(
    Bp_publication,
    url_prefix="/publications"
    )

    return app