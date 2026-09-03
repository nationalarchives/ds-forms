import os

from flask import current_app, render_template, url_for

from app.main import bp


@bp.route("/")
def index():
    routes = [
        {"path": str(rule), "methods": [method for method in rule.methods]}
        for rule in current_app.url_map.iter_rules()
    ]
    routes.sort(key=lambda x: x["path"])
    forms_directory = os.path.join(current_app.root_path, "forms", "config")

    forms = []
    for root, _dirs, files in os.walk(forms_directory):
        for name in files:
            if name.endswith(".yml"):
                relative_path = os.path.relpath(
                    os.path.join(root, name), forms_directory
                )

                forms.append(
                    {
                        "slug": relative_path.replace(".yml", ""),
                        "config": f"{os.path.relpath(os.path.join(root, name), current_app.root_path)}",
                        "path": url_for(
                            "forms.start_page",
                            form_path=relative_path.replace(".yml", ""),
                        ),
                    }
                )

    return render_template("main/index.html", routes=routes, forms=forms)
