import os

from app.main import bp
from flask import current_app, render_template, url_for


@bp.route("/")
def index():
    routes = [
        {"path": str(rule), "methods": [method for method in rule.methods]}
        for rule in current_app.url_map.iter_rules()
    ]
    routes.sort(key=lambda x: x["path"])
    forms_directory = os.path.join(current_app.root_path, "forms", "config")
    forms = [
        {
            "slug": name.replace(".yml", ""),
            "config": f"{forms_directory.replace("/app/app", "app")}/{name}",
            "path": url_for("forms.start_page", form_slug=name.replace(".yml", "")),
        }
        for name in os.listdir(forms_directory)
        if name.endswith(".yml")
    ]
    return render_template("main/index.html", routes=routes, forms=forms)
