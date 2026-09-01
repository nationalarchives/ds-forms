from flask import current_app, redirect, render_template, request

from app.forms import bp
from app.forms.config import form_flow_from_config, load_config
from app.lib.limiter import limiter


def get_form_flow(form_path: str):
    config = load_config(form_path)
    return form_flow_from_config(config, form_path)


@bp.route("/<path:form_path>/", methods=["GET", "POST"])
def start_page(form_path):
    try:
        form_flow = get_form_flow(form_path)
    except FileNotFoundError:
        return render_template("errors/page_not_found.html"), 404
    except ValueError:
        current_app.logger.exception(f"Error loading form flow for '{form_path}'")
        return render_template("errors/server.html"), 500

    if not form_flow:
        return render_template("errors/page_not_found.html"), 404

    # if form_flow.has_complete_path():
    #     return redirect(form_flow.get_final_page().get_page_path())

    if form_flow.get_starting_path() != request.path:
        return redirect(form_flow.get_starting_path())

    return form_flow.get_starting_page().serve()


@bp.route("/<path:form_path>/reset/")
@limiter.exempt
def reset_form(form_path):
    try:
        form_flow = get_form_flow(form_path)
    except FileNotFoundError:
        return render_template("errors/page_not_found.html"), 404
    except ValueError:
        current_app.logger.exception(f"Error resetting form flow for '{form_path}'")
        return render_template("errors/server.html"), 500

    if not form_flow:
        return render_template("errors/page_not_found.html"), 404

    form_flow.reset()

    return redirect(form_flow.get_starting_path())


@bp.route("/<path:form_path>/<string:page_slug>/", methods=["GET", "POST"])
def page(form_path, page_slug):
    try:
        form_flow = get_form_flow(form_path)
    except FileNotFoundError:
        return start_page(f"{form_path}/{page_slug}")
    except ValueError:
        current_app.logger.exception(
            f"Error loading form flow page for '{form_path}/{page_slug}'"
        )
        return render_template("errors/server.html"), 500

    if not form_flow:
        return render_template("errors/page_not_found.html"), 404

    if form_page := form_flow.get_page_by_slug(page_slug):
        return form_page.serve()

    return render_template("errors/page_not_found.html"), 404
