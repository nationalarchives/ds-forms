import hashlib
import importlib
import json
import os.path
import re
from pathlib import Path

import yaml
from flask import current_app
from flask_wtf import FlaskForm

from app.forms.models import FormFlow

FORM_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)*$")


def _load_form_class(form_name: str | None) -> type[FlaskForm] | None:
    """
    Import a form part by name, e.g. 'YourDetailsForm' or 'apply_to_film.YourDetailsForm'.
    Only permits valid FlaskForm subclasses residing under 'app.forms.parts'.
    """
    if not form_name:
        return None

    if not isinstance(form_name, str):
        raise TypeError("Form name must be a string")

    form_name = form_name.strip()
    if not form_name:
        return None

    if not FORM_NAME_PATTERN.match(form_name):
        raise ValueError(f"Invalid form class name format: '{form_name}'")

    module_path = f"app.forms.parts.{form_name}"
    try:
        module = importlib.import_module(module_path)
    except (ImportError, ModuleNotFoundError, AttributeError, ValueError) as e:
        raise ValueError(f"Could not import form module '{module_path}'") from e

    if not module.__name__.startswith("app.forms.parts."):
        raise ValueError(
            f"Form module '{module.__name__}' is outside allowed package 'app.forms.parts'"
        )

    class_name = form_name.split(".")[-1]
    form_class = getattr(module, class_name, None)

    if form_class is None:
        raise ValueError(
            f"Form class '{class_name}' not found in module '{module_path}'"
        )

    if not isinstance(form_class, type):
        raise TypeError(
            f"Object '{class_name}' in module '{module_path}' is not a class"
        )

    if not issubclass(form_class, FlaskForm):
        raise TypeError(
            f"Form class '{class_name}' in module '{module_path}' is not a valid FlaskForm subclass"
        )

    return form_class


def load_config(form_path: str) -> dict:
    if not form_path:
        raise ValueError("Form path must be provided")

    config_path = os.path.join(
        current_app.root_path, "forms", "config", f"{form_path}.yml"
    )

    form_config = Path(config_path)
    print("!!!!!!!!!!!!!!")
    print(f"Loading form configuration from: {form_config}")
    if not form_config.is_file():
        raise FileNotFoundError(
            f"Form configuration file not found for form: {form_path}"
        )

    try:
        with open(config_path) as stream:
            return yaml.safe_load(stream)
    except yaml.YAMLError as e:
        raise ValueError(
            f"Error loading YAML configuration for form {form_path}"
        ) from e
    except Exception as e:
        raise ValueError(
            f"Unexpected error loading configuration for form {form_path}"
        ) from e


def form_flow_from_config(config: dict, path: str) -> FormFlow:  # noqa: C901
    if not config:
        raise ValueError("Configuration cannot be empty")

    for expected_key in ["startingPage", "finalPage"]:
        if expected_key not in config:
            raise ValueError(f"Configuration must contain '{expected_key}'")

    config_hash = hashlib.sha256(
        json.dumps(config, sort_keys=True).encode("utf-8")
    ).hexdigest()

    form_flow = FormFlow(
        path=path,
        config_hash=config_hash,
        metadata=config.get("meta"),
    )

    starting_page_config = config.get("startingPage", {})
    starting_page_id = starting_page_config.get("id", "")
    form_flow.create_starting_page(
        id=starting_page_id,
        name=starting_page_config.get("name", ""),
        slug=starting_page_config.get("slug", "/"),
        content=starting_page_config.get("content", ""),
        template=starting_page_config.get("template", ""),
        form=_load_form_class(starting_page_config.get("form")),
        altcha=starting_page_config.get("altcha", False),
        yaml_config=starting_page_config,
    )

    pages_config = {starting_page_id: starting_page_config}

    for page in config.get("pages", []):
        id = page.get("id", "")
        if not id or id in pages_config:
            raise ValueError("Each page must have a unique 'id'")
        pages_config.update({id: page})
        form_flow.create_page(
            id=id,
            name=page.get("name", ""),
            slug=page.get("slug", ""),
            content=page.get("content", {}),
            template=page.get("template", ""),
            form=_load_form_class(page.get("form")),
            altcha=page.get("altcha", False),
            yaml_config=page,
        )

    final_page_config = config.get("finalPage", {})
    final_page_id = final_page_config.get("id", "")
    pages_config.update({final_page_id: final_page_config})
    form_flow.create_final_page(
        id=final_page_id,
        name=final_page_config.get("name", ""),
        slug=final_page_config.get("slug", "/"),
        content=final_page_config.get("content", {}),
        template=final_page_config.get("template", ""),
        yaml_config=final_page_config,
    )

    for page in form_flow.get_all_pages():
        page_config = page.yaml_config

        if not page_config:
            continue

        for redirection in page_config.get("redirectWhenComplete", []):
            redirect_page_id = redirection.get("page", "")
            redirect_page = None
            if redirect_page_id:
                try:
                    redirect_page = form_flow.get_page_by_id(
                        redirection.get("page", "")
                    )
                except KeyError:
                    # Page not found
                    pass
            redirect_url = redirection.get("url", "")
            redirect_flask_method = redirection.get("flaskMethod", "")
            if not (redirect_page or redirect_url or redirect_flask_method):
                raise ValueError(
                    f"Redirect target page or URL/flaskMethod must be provided for page '{page.slug}'."
                )
            when = None
            if when_data := redirection.get("when", {}):
                key = when_data.get("key", "")
                value = when_data.get("value", "")
                if key and value:
                    when = (key, value)
            page.redirect_when_complete(
                page=redirect_page,
                flask_method=redirect_flask_method,
                url=redirect_url,
                when=when,
                # condition=TODO
            )

        for requirement in page_config.get("requireResponse", []):
            try:
                required_page = form_flow.get_page_by_id(requirement.get("page"))
            except KeyError:
                required_page = None
            if not required_page:
                raise ValueError(
                    f"Required page '{requirement.get('page')}' not found in form flow as a prerequisite to '{page.slug}'."
                )
            page.require_response(
                page=required_page,
                key=requirement.get("key"),
                response=requirement.get("value", None),
            )

        if require_completion_of := page_config.get("requires", []):
            required_pages = []
            for id in require_completion_of:
                try:
                    required_page = form_flow.get_page_by_id(id)
                    required_pages.append(required_page)
                except KeyError:
                    # Page not found
                    pass
            if any(page is None for page in required_pages):
                raise ValueError(
                    f"One or more required pages for 'requires' of '{page.slug}' not found in form flow."
                )
            page.require_completion_of(*required_pages)

        if require_completion_of_any := page_config.get("requiresAny", []):
            required_pages = []
            for id in require_completion_of_any:
                required_page = form_flow.get_page_by_id(id)
                required_pages.append(required_page)
            if any(page is None for page in required_pages):
                raise ValueError(
                    f"One or more required pages for 'requiresAny' of '{page.slug}' not found in form flow."
                )
            fallback_page_id = page_config.get("redirectIfNotComplete", None)
            fallback_page = (
                form_flow.get_page_by_id(fallback_page_id) if fallback_page_id else None
            )
            page.require_completion_of_any(
                pages=required_pages, fallback_page=fallback_page
            )

    return form_flow
