import os

from flask import current_app, make_response, render_template

from app.forms.config import form_flow_from_config, load_config
from app.sitemap import bp


@bp.route("/sitemap.xml")
def index():
    forms_directory = os.path.join(current_app.root_path, "forms", "config")
    forms = []

    for root, _dirs, files in os.walk(forms_directory):
        for file in files:
            if file.endswith(".yml"):
                form_config_path = os.path.relpath(
                    os.path.join(root, file), forms_directory
                )
                config = load_config(form_config_path)
                form_path = form_config_path.replace(".yml", "")
                form_flow = form_flow_from_config(config, form_path)
                if not form_flow.meta("exclude_from_sitemap", False):
                    forms.append(
                        form_flow.get_starting_page().get_page_path(external=True)
                    )

    xml_sitemap_index = render_template("sitemap.xml", forms=forms)
    response = make_response(xml_sitemap_index)
    response.headers["Content-Type"] = "application/xml; charset=utf-8"
    return response
