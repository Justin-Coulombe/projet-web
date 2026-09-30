from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from app.database.queries.users import (
    add_user,
    get_user_by_email
)


bp_auth = Blueprint("auth", __name__)


@bp_auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        prenom = request.form.get("prenom", "").strip()
        nom = request.form.get("nom", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if not prenom or not nom or not email or not password:
            return render_template(
                "auth/register.jinja",
                error="Tous les champs sont obligatoires."
            )

        if password != password_confirm:
            return render_template(
                "auth/register.jinja",
                error="Les mots de passe ne correspondent pas."
            )

        if len(password) < 8:
            return render_template(
                "auth/register.jinja",
                error="Le mot de passe doit contenir au moins 8 caractères."
            )

        if get_user_by_email(email):
            return render_template(
                "auth/register.jinja",
                error="Un compte existe déjà avec cette adresse courriel."
            )

        password_hash = generate_password_hash(password)

        add_user(
            nom,
            prenom,
            email,
            password_hash
        )

        user = get_user_by_email(email)

        session.clear()
        session["user_id"] = user["id"]

        return redirect(url_for("index"))

    return render_template("auth/register.jinja")


@bp_auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = get_user_by_email(email)
        if user is None or not check_password_hash(
            user["mdp"],
            password
        ):
            return render_template(
                "auth/login.jinja",
                error="Courriel ou mot de passe invalide."
            )

        session.clear()
        session["user_id"] = user["id"]

        return redirect(url_for("index"))

    return render_template("auth/login.jinja")


@bp_auth.route("/logout")
def logout():
    session.clear()

    return redirect(url_for("index"))


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("auth.login"))

        return view(*args, **kwargs)

    return wrapped_view