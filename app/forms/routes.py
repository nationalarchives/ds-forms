from app.forms import bp
from app.forms.config import form_flow_from_config, load_config
from flask import current_app, redirect, render_template, request, session

# from .config.example import forms


def get_form_flow(form_slug: str):
    try:
        config = load_config(form_slug)
        return form_flow_from_config(config, form_slug)
    except Exception as e:
        current_app.logger.error(
            f"Error loading configuration for form flow '{form_slug}': {e}"
        )
        return None


@bp.route("/<string:form_slug>/", methods=["GET", "POST"])
def start_page(form_slug):
    try:
        form_flow = get_form_flow(form_slug)
    except Exception as e:
        current_app.logger.error(f"Error loading form flow for '{form_slug}': {e}")
        return render_template("errors/server.html"), 500

    if not form_flow:
        return render_template("errors/page_not_found.html"), 404

    if form_flow.get_starting_path() != request.path:
        return redirect(form_flow.get_starting_path())

    return form_flow.get_starting_page().serve()


@bp.route("/<string:form_slug>/reset/")
def reset_form(form_slug):
    try:
        form_flow = get_form_flow(form_slug)
    except Exception as e:
        current_app.logger.error(f"Error resetting form flow for '{form_slug}': {e}")
        return render_template("errors/server.html"), 500

    if not form_flow:
        return render_template("errors/page_not_found.html"), 404

    session.clear()
    return redirect(form_flow.get_starting_path())


@bp.route("/<string:form_slug>/<string:page_slug>/", methods=["GET", "POST"])
def page(form_slug, page_slug):
    try:
        form_flow = get_form_flow(form_slug)
    except Exception as e:
        current_app.logger.error(
            f"Error loading form flow page for '{form_slug}/{page_slug}': {e}"
        )
        return render_template("errors/server.html"), 500

    if not form_flow:
        return render_template("errors/page_not_found.html"), 404

    if form_page := form_flow.get_page_by_slug(page_slug):
        return form_page.serve(pages=form_flow.get_all_pages())

    return render_template("errors/page_not_found.html"), 404
