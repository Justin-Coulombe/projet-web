from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    g
)

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from app.routes.auth import login_required

from app.database.queries.users import (
    get_user_by_email,
    get_user_with_password,
    update_user,
    update_password
)


bp_profile = Blueprint("profile", __name__)


@bp_profile.route("/", methods=["GET", "POST"])
@login_required
def edit():

    if request.method == "POST":
        prenom = request.form.get("prenom", "").strip()
        nom = request.form.get("nom", "").strip()
        email = request.form.get("email", "").strip().lower()

        if not prenom or not nom or not email:
            return render_template(
                "profile/edit.jinja",
                error="Tous les champs sont obligatoires."
            )

        existing_user = get_user_by_email(email)

        if (
            existing_user is not None
            and existing_user["id"] != session["user_id"]
        ):
            return render_template(
                "profile/edit.jinja",
                error="Cette adresse courriel est déjà utilisée."
            )

        update_user(
            session["user_id"],
            prenom,
            nom,
            email
        )

        return redirect(
            url_for(
                "profile.edit",
                success="Informations modifiées avec succès."
            )
        )

    success = request.args.get("success")
    password_success = request.args.get("password_success")

    return render_template(
        "profile/edit.jinja",
        success=success,
        password_success=password_success
    )


@bp_profile.route("/password", methods=["POST"])
@login_required
def change_password():

    current_password = request.form.get(
        "current_password",
        ""
    )

    new_password = request.form.get(
        "new_password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )

    user = get_user_with_password(
        session["user_id"]
    )

    if not check_password_hash(
        user["mdp"],
        current_password
    ):
        return render_template(
            "profile/edit.jinja",
            password_error="Le mot de passe actuel est incorrect."
        )

    if len(new_password) < 8:
        return render_template(
            "profile/edit.jinja",
            password_error="Le nouveau mot de passe doit contenir au moins 8 caractères."
        )

    if new_password != confirm_password:
        return render_template(
            "profile/edit.jinja",
            password_error="Les nouveaux mots de passe ne correspondent pas."
        )

    password_hash = generate_password_hash(
        new_password
    )

    update_password(
        session["user_id"],
        password_hash
    )

    return redirect(
        url_for(
            "profile.edit",
            password_success="Mot de passe modifié avec succès."
        )
    )