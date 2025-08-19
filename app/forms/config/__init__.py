import importlib
import os.path
from pathlib import Path

import yaml
from app.forms.models import FormFlow


def load_config(form_slug: str) -> FormFlow:
    if not form_slug:
        raise ValueError("Form slug must be provided")

    config_path = os.path.join("/", "app", "app", "forms", "config", f"{form_slug}.yml")

    form_config = Path(config_path)
    if not form_config.is_file():
        raise FileNotFoundError(
            f"Form configuration file not found for form: {form_config}"
        )

    try:
        with open(config_path) as stream:
            return yaml.safe_load(stream)
    except yaml.YAMLError as e:
        raise ValueError(f"Error loading YAML configuration for form {form_slug}: {e}")


def form_flow_from_config(config: dict, slug: str) -> FormFlow:  # noqa: C901
    if not config:
        raise ValueError("Configuration cannot be empty")

    for expected_key in ["startingPage", "finalPage"]:
        if expected_key not in config:
            raise ValueError(f"Configuration must contain '{expected_key}'")

    form_flow = FormFlow(slug=slug, handle_files="fileHandler" in config)

    starting_page_config = config.get("startingPage", {})
    starting_page_id = starting_page_config.get("id", "")
    form_flow.create_starting_page(
        id=starting_page_id,
        name=starting_page_config.get("name", ""),
        slug=starting_page_config.get("slug", "/"),
        description=starting_page_config.get("description", ""),
        template=starting_page_config.get("template", ""),
        form=(
            getattr(
                importlib.import_module(
                    f"app.forms.parts.{starting_page_config.get('form')}"
                ),
                starting_page_config.get("form"),
            )
            if starting_page_config.get("form")
            else None
        ),
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
            description=page.get("description", ""),
            template=page.get("template", ""),
            form=(
                getattr(
                    importlib.import_module(f"app.forms.parts.{page.get('form')}"),
                    page.get("form"),
                )
                if page.get("form")
                else None
            ),
            yaml_config=page,
        )

    final_page_config = config.get("finalPage", {})
    final_page_id = final_page_config.get("id", "")
    form_flow.create_final_page(
        id=final_page_id,
        name=final_page_config.get("name", ""),
        slug=final_page_config.get("slug", "/"),
        description=final_page_config.get("description", ""),
        template=final_page_config.get("template", ""),
        yaml_config=final_page_config,
    )

    for page_id, page in form_flow.get_all_pages():
        page_config = page.yaml_config

        for redirection in page_config.get("redirectWhenComplete", []):
            redirect_page = form_flow.get_page_by_id(redirection.get("page", ""))
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
            required_page = form_flow.get_page_by_id(requirement.get("page"))
            if not required_page:
                raise ValueError(
                    f"Required page '{requirement.get('page')}' not found in form flow as a prerequisite to '{page.slug}'."
                )
            page.require_response(
                page=required_page,
                key=requirement.get("key"),
                response=requirement.get("value", None),
            )

        if require_completion_of := page_config.get("requireCompletionOf", []):
            required_pages = [
                form_flow.get_page_by_id(id) for id in require_completion_of
            ]
            if any([page is None for page in required_pages]):
                raise ValueError(
                    f"One or more required pages for 'requireCompletionOf' of '{page.slug}' not found in form flow."
                )
            page.require_completion_of(*required_pages)

        if require_completion_of_any := page_config.get("requireCompletionOfAny", []):
            required_pages = [
                form_flow.get_page_by_id(id) for id in require_completion_of_any
            ]
            if any([page is None for page in required_pages]):
                raise ValueError(
                    f"One or more required pages for 'requireCompletionOfAny' of '{page.slug}' not found in form flow."
                )
            fallback_page = form_flow.get_page_by_id(
                page_config.get("redirectIfNotComplete", None)
            )
            page.require_completion_of_any(
                pages=required_pages, fallback_page=fallback_page
            )

    return form_flow
