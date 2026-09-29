import os

from flask import Flask, render_template, session, g

from app.database.init_db import init_database
from app.database.queries.users import get_user_by_id
from dotenv import load_dotenv
from app.routes.profile import bp_profile
from app.routes.stationnement import bp_stationnement

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
        return render_template("index.jinja")

    app.register_blueprint(
    bp_profile,
    url_prefix="/profile"
    )

    app.register_blueprint(
    bp_stationnement,
    url_prefix="/stationnement"
    )

    return app