from flask import render_template

def handle_bad_request(e):
    return render_template("error_page/400.html", error="Bad Request"), 400

def handle_unauthorized_request(e):
    return render_template("error_page/403.html", error="Unauthorized"), 403
