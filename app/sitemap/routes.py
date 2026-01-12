import os

from app.forms.config import form_flow_from_config, load_config
from app.sitemap import bp
from flask import current_app, make_response, render_template


@bp.route("/sitemap.xml")
def index():
    forms_directory = os.path.join(current_app.root_path, "forms", "config")
    forms = []
    for file in os.listdir(forms_directory):
        if file.endswith(".yml"):
            name = file.replace(".yml", "")
            config = load_config(name)
            form_flow = form_flow_from_config(config, name)
            if not form_flow.meta("exclude_from_sitemap", False):
                forms.append(form_flow.get_starting_page().get_page_path(external=True))

    xml_sitemap_index = render_template("sitemap.xml", forms=forms)
    response = make_response(xml_sitemap_index)
    response.headers["Content-Type"] = "application/xml; charset=utf-8"
    return response
