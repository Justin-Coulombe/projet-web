from flask import request, render_template, Blueprint

Bp_admin = Blueprint('admin', __name__)

@Bp_admin.route("/")
def index():
    return render_template("admin/index.jinja")

@Bp_admin.route("/modération")
def modération():
    return render_template("admin/auth.jinja")