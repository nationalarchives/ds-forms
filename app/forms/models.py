from collections.abc import Callable
from typing import Optional, TypedDict

from flask import current_app, redirect, render_template, request, session, url_for
from flask_wtf import FlaskForm


class FormFlow:
    """
    Represents a collection of form pages in a flow.
    Each page can have requirements for completion and can redirect to another page when complete.
    """

    def __init__(self, slug: str):
        self.slug = slug
        self.pages: dict[str:"FormPage"] = {}
        self.starting_page_slug: str = "/"

    def create_starting_page(
        self,
        id: str,
        name: str,
        slug: str = "/",
        description: str = "",
        template: str = "",
        form: Optional[FlaskForm] = None,
        yaml_config: Optional[dict] = None,
    ):
        """
        Set the starting page of the flow.
        """
        starting_page = self.create_page(
            id, name, slug, description, template, form, yaml_config
        )
        self.starting_page_slug = slug
        return starting_page

    def create_page(
        self,
        id: str,
        name: str,
        slug: str,
        description: str = "",
        template: str = "",
        form: Optional[FlaskForm] = None,
        yaml_config: Optional[dict] = None,
    ):
        """
        Add a page to the flow.
        """
        new_page = FormPage(
            self, id, name, slug, description, template, form, yaml_config
        )
        self.pages.update({id: new_page})
        return new_page

    def get_all_pages(self) -> list[tuple[str, "FormPage"]]:
        """
        Retrieve all pages in the flow.
        """
        return self.pages.items()

    def get_page_by_id(self, id: str) -> Optional["FormPage"]:
        """
        Retrieve a page by its id.
        """
        if id and id in self.pages:
            return self.pages[id]
        return None

    def get_page_by_slug(self, slug: str) -> Optional["FormPage"]:
        """
        Retrieve a page by its slug.
        """
        return next((page for page in self.pages.values() if page.slug == slug), None)

    def get_starting_page(self) -> "FormPage":
        """
        Get the starting page of the flow.
        """
        if not self.starting_page_slug:
            raise ValueError("Starting page is not set for this flow.")
        return self.get_page_by_slug(self.starting_page_slug)

    def get_starting_path(self) -> str:
        """
        Get the starting page of the flow.
        """
        if not self.starting_page_slug:
            raise ValueError("Starting page is not set for this flow.")
        if self.starting_page_slug == "/":
            return url_for("forms.start_page", form_slug=self.slug)
        else:
            return url_for(
                "forms.page", form_slug=self.slug, page_slug=self.starting_page_slug
            )

    def set_file_handler(self):
        # TODO
        pass


class PageCompletionRuleFormPage(TypedDict):
    page: "FormPage"
    condition: Optional[Callable]
    when: Optional[tuple[str, str]]


class PageCompletionRuleFlaskMethod(TypedDict):
    flask_method: str
    condition: Optional[Callable]
    when: Optional[tuple[str, str]]


class PageCompletionRuleURL(TypedDict):
    url: str
    condition: Optional[Callable]
    when: Optional[tuple[str, str]]


class FormPage:
    """
    Represents a page in the flow that contains a form.
    Each page has requirements for completion.
    """

    def __init__(
        self,
        flow: "FormFlow",
        id: str,
        name: str,
        slug: str = "/",
        description: str = "",
        template: str = "",
        form: Optional[FlaskForm] = None,
        yaml_config: Optional[dict] = None,
    ):
        self.flow: "FormFlow" = flow
        self.id: str = id
        self.name: str = name
        self.slug: str = slug
        self.description: str = description
        self.template: str = template if template else "forms/form_page.html"
        self.requires_completion_of: list["FormPage"] = []
        self.requires_completion_of_any: list["FormPage"] = []
        self.requires_completion_of_any_fallback: Optional["FormPage"] = None
        self.requires_responses: list[tuple["FormPage", str, str]] = []
        self.when_complete: list[
            PageCompletionRuleFormPage
            | PageCompletionRuleFlaskMethod
            | PageCompletionRuleURL
        ] = []
        self.clear_pages_on_completion: list["FormPage"] = []
        self.form: Optional[FlaskForm] = None
        self.form_class: Optional[FlaskForm] = form if form else None
        self.yaml_config: Optional[dict] = yaml_config

    def get_page_path(self) -> str:
        """
        Get the path for this page.
        """
        if self.slug == "/":
            return url_for("forms.start_page", form_slug=self.flow.slug)
        return url_for("forms.page", form_slug=self.flow.slug, page_slug=self.slug)

    def require_completion_of(self, *pages: "FormPage"):
        """
        Specify which pages must be completed before this page can be accessed.
        """
        self.requires_completion_of.extend(pages)
        return self

    def require_completion_of_any(
        self, pages: list["FormPage"], fallback_page: Optional["FormPage"] = None
    ):
        """
        Specify that at least one of the provided pages must be completed before this page can be accessed.
        If none are completed, redirect to the fallback page.
        """
        self.requires_completion_of_any = pages
        if fallback_page:
            self.requires_completion_of_any_fallback = fallback_page
        return self

    def require_response(self, page: "FormPage", key: str, response: str):
        """
        Specify that a response from the given page is required before this page can be accessed.
        """
        self.requires_responses.append((page, key, response))
        return self

    def redirect_when_complete(
        self,
        page: Optional["FormPage"] = None,
        flask_method: Optional[str] = "",
        url: Optional[str] = "",
        when: Optional[tuple[str, str]] = None,
        condition: Optional[Callable] = None,
    ):
        """
        Set the page to redirect to when this page is completed.
        """
        if not (page or flask_method or url):
            raise ValueError("Either 'page', 'url' or 'flask_method' must be provided.")
        self.when_complete.append(
            {
                "page": page,
                "url": url,
                "flask_method": flask_method,
                "when": when,
                "condition": condition,
            }
        )
        return self

    def clear_on_completion(self, *pages: "FormPage"):
        """
        Specify which pages should be cleared from the session when this page is completed.
        """
        self.clear_pages_on_completion.extend(pages)
        return self

    def get_saved_form_data(self):
        """
        Get the form data from the session or other storage.
        """
        return session[self.id] if self.id in session else {}

    def save_form_data(self, form_data: dict):
        """
        Save the form data to the session.
        """
        session[self.id] = form_data

    def is_complete(self) -> bool:
        """
        Check if the form is complete based on the data provided.
        """
        if self.form:
            return self.form.validate()
        elif self.form_class:
            temp_form = self.form_class(data=self.get_saved_form_data())
            temp_form._fields.pop("csrf_token", None)
            is_complete = temp_form.validate()
            if temp_form.errors:
                current_app.logger.warning(
                    f"Form '{self.id}' has errors: {temp_form.errors}"
                )
            return is_complete
        return True

    def serve(self, **kwargs):
        """
        Start the flow by loading the form data and checking completion status.
        """
        if self.form_class and not self.form:
            self.form = self.form_class(data=self.get_saved_form_data())

        for page in self.requires_completion_of:
            if not page.is_complete():
                current_app.logger.warning(
                    f"Required page '{page.id}' is not complete."
                )
                return redirect(page.get_page_path())

        if len(self.requires_completion_of_any):
            any_complete = False

            for page in self.requires_completion_of_any:
                current_app.logger.debug(
                    f"Checking completion for any required page: {page.id}"
                )
                if page.is_complete():
                    any_complete = True
                    break

            if not any_complete:
                current_app.logger.warning(
                    f"None of the any required pages are complete for '{self.id}'."
                )
                if self.requires_completion_of_any_fallback:
                    current_app.logger.warning(
                        f"Redirecting to fallback page: {self.requires_completion_of_any_fallback.id}"
                    )
                    return redirect(
                        self.requires_completion_of_any_fallback.get_page_path()
                    )
                else:
                    current_app.logger.warning(
                        f"Redirecting to first required page: {self.requires_completion_of_any[0].id}"
                    )
                    return redirect(self.requires_completion_of_any[0].get_page_path())

        for requires_responses in self.requires_responses:
            (page, key, required_response) = requires_responses
            data = page.get_saved_form_data()
            if data.get(key, None) != required_response:
                current_app.logger.warning(
                    f"Required response '{required_response}' not found for key '{key}' in page '{page.id}'."
                )
                return redirect(page.get_page_path())

        return self.validate_and_redirect(**kwargs)

    def validate_and_redirect(self, **kwargs):
        """
        Validate the form data when the page is submitted and redirect based on completion status.
        """
        if request.method == "POST" and self.is_complete():
            form_data = self.form.data
            form_data.pop("csrf_token", None)
            self.save_form_data(form_data)

            for page in self.clear_pages_on_completion:
                if page.id in session:
                    current_app.logger.debug(f"Clearing page data for: {page.id}")
                    session.pop(page.id, None)

            for rule in self.when_complete:
                current_app.logger.debug(f"Checking completion rule: {rule}")
                if (
                    (rule["when"] is None and rule["condition"] is None)
                    or (
                        rule["when"]
                        and form_data.get(rule["when"][0], None) == rule["when"][1]
                    )
                    or (rule["condition"] and rule["condition"](form_data))
                ):
                    current_app.logger.debug(
                        f"Completion rule matched for page: '{self.id}'"
                    )
                    if rule["page"]:
                        current_app.logger.debug(
                            f"Redirecting to page: '{rule['page'].id}'"
                        )
                        return redirect(rule["page"].get_page_path())

                    if rule["flask_method"]:
                        current_app.logger.debug(
                            f"Redirecting to Flask method: '{rule['flask_method']}'"
                        )
                        return redirect(url_for(rule["flask_method"]))

                    if rule["url"]:
                        current_app.logger.debug(f"Redirecting to URL: {rule['url']}")
                        return redirect(rule["url"])

            raise Exception("No matching completion rule found.")
        return render_template(
            self.template,
            flow=self.flow,
            pageTitle=self.name,
            description=self.description,
            page_path=self.get_page_path(),
            form_reset_path=url_for("forms.reset_form", form_slug=self.flow.slug),
            form=self.form,
            **kwargs,
        )
