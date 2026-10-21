from flask import redirect, request, render_template, Blueprint, session
from app.database.queries import users as userqueries
from app.database.queries import publications as postqueries
from app.database.queries import admin as adminqueries
from app.routes.api import paginate_data as pagination
import time
Bp_admin = Blueprint('admin', __name__)

@Bp_admin.route("/")
def index():
    if 'admin_id' not in session:
        return redirect('login')
    admin = adminqueries.get_admin_by_id(session['admin_id'])

    context = {'admin' : admin}
    return render_template("admin/index.jinja", context=context)

@Bp_admin.route("/gestion", methods=['GET', 'POST'])
def gestion():
    if 'admin_id' not in session:
        return redirect('login')
    context = {}
    context['users'] = []
    context['no_search'] = False
    context['publications'] = []
    categorie = request.args.get('categorie', 'uti')

    admin = adminqueries.get_admin_by_id(session['admin_id'])
    context['admin'] = admin

    if request.method == "POST":
        form = request.form
        if form['identifier'] == "ban":
            if categorie == 'pub':
                pubid = request.form.get('selected')
                if pubid != 'none':
                    postqueries.delete_publication_by_id(pubid)
                    return redirect("confirmation")
                
            else:
                userid = request.form.get('selected')
                if userid != "none":
                    userqueries.ban_user_by_id(userid)
                    return redirect("confirmation")
        else:
            return "unknown request"

    if categorie == 'uti':
        mail = request.args.get('mail', default="")    
        if str.strip(mail) == "":
            query = "%"
        else:
            query = "%" + mail +"%"

        users = userqueries.get_users_by_email(query)
        pages = pagination(users, 5)
        context['page_number'] = len(pages)
        page_index = request.args.get('page', 1, type=int)

        if page_index < 1:
            page_index = 1

        if not pages:
            pages = [[]]

        if page_index > len(pages):
            page_index = len(pages)
        context['active_page'] = page_index
        
        for user in pages[page_index-1]:
            user['postnumber'] = get_user_posts_number(str(user['id']))
            context['users'].append(user)
            
    else:
        
        context['no_search'] = True
        pubs = postqueries.get_all_publications()
        pages = pagination(pubs, 5)
        context['page_number'] = len(pages)
        page_index = request.args.get('page', 1, type=int)

        if page_index < 1:
            page_index = 1

        if not pages:
            pages = [[]]

        if page_index > len(pages):
            page_index = len(pages)
        context['active_page'] = page_index

        for pub in pages[page_index-1]:
            context['publications'].append(pub)
            
    return render_template("admin/gestion.jinja", context=context)


@Bp_admin.route("/confirmation")
def confirmation():
    return "Opération réussie"

@Bp_admin.route('/login', methods=['GET','POST'])
def login():
    context = {}
    context['messages'] = []
    context['valid'] = True
    if 'admin_id' in session:
        return redirect("/admin")
    
    if request.method == 'POST':
        form = request.form
        identifier = form.get('inputidentifier')
        password = form.get('inputpassword')
        admin = adminqueries.get_admin_by_name_password(identifier, password)
        if admin :
            session['admin_id'] = admin[0]
            return redirect("/admin")
        else:
            context['messages'].append("Aucun administrateur avec ces identifiants")
            context['valid'] = False

    return render_template("admin/login.jinja", context=context)

@Bp_admin.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect("/")

def get_user_posts_number(userid):
    posts = postqueries.get_publications_by_user(userid)
    nb = 0
    for item in posts:
        nb = nb + 1
    return nb