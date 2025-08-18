from app.forms import bp
from flask import redirect, render_template, request, session

from .config.example import forms


@bp.route("/<string:form_slug>/", methods=["GET", "POST"])
def start_page(form_slug):
    if form_slug in forms:
        if forms[form_slug].get_starting_path() != request.path:
            return redirect(forms[form_slug].get_starting_path())
        return forms[form_slug].get_starting_page().serve()
    return render_template("errors/page_not_found.html"), 404


@bp.route("/<string:form_slug>/reset/")
def reset_form(form_slug):
    if form_slug in forms:
        session.clear()
        return redirect(forms[form_slug].get_starting_path())
    return render_template("errors/page_not_found.html"), 404


@bp.route("/<string:form_slug>/<string:page_slug>/", methods=["GET", "POST"])
def page(form_slug, page_slug):
    if form_slug in forms:
        if form_page := forms[form_slug].get_page_by_slug(page_slug):
            return form_page.serve(pages=forms[form_slug].get_all_pages())
    return render_template("errors/page_not_found.html"), 404
