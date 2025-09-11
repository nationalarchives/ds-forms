import hashlib
import json
from collections.abc import Callable
from typing import Optional, TypedDict

from flask import (
    Response,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf import FlaskForm
from wtforms import FileField, MultipleFileField
from wtforms.validators import InputRequired

from .result_handlers import (
    APIResultHandler,
    EmailResultHandler,
    MongoDBResultHandler,
    PostgresResultHandler,
)


class FormFlow:
    """
    Represents a collection of form pages in a flow.
    Each page can have requirements for completion and can redirect to another page when complete.
    """

    def __init__(
        self,
        slug: str,
        config_hash: Optional[str] = "",
    ):
        self.slug = slug
        self.pages: dict[str:"FormPage"] = {}
        self.starting_page_id: str = ""
        self.final_page_id: str = ""
        self.result_handler_config: Optional[dict] = None
        print(f"Config hash: {config_hash}")
        print(f"Session config hash: {session.get('config_hash', '')}")
        if session.get("config_hash", "") != config_hash:
            current_app.logger.warn("Form configuration has changed, resetting flow")
            self.reset()
            session["config_hash"] = config_hash

    def create_page(
        self,
        id: str,
        name: str,
        slug: str,
        description: str = "",
        body: str = "",
        template: str = "",
        form: Optional[FlaskForm] = None,
        yaml_config: Optional[dict] = None,
    ):
        """
        Add a page to the flow.
        """
        new_page = FormPage(
            flow=self,
            id=id,
            name=name,
            slug=slug,
            description=description,
            body=body,
            template=template,
            form=form,
            yaml_config=yaml_config,
        )
        self.pages.update({id: new_page})
        return new_page

    def create_starting_page(
        self,
        id: str,
        name: str,
        slug: str = "/",
        description: str = "",
        body: str = "",
        template: str = "",
        form: Optional[FlaskForm] = None,
        yaml_config: Optional[dict] = None,
    ):
        """
        Set the starting page of the flow.
        """
        starting_page = self.create_page(
            id=id,
            name=name,
            slug=slug,
            description=description,
            body=body,
            template=template,
            form=form,
            yaml_config=yaml_config,
        )
        self.starting_page_id = id
        return starting_page

    def create_final_page(
        self,
        id: str,
        name: str,
        slug: str = "/",
        description: str = "",
        body: str = "",
        template: str = "",
        yaml_config: Optional[dict] = None,
    ):
        """
        Set the final page of the flow.
        """
        final_page = self.create_page(
            id=id,
            name=name,
            slug=slug,
            description=description,
            body=body,
            template=template,
            form=None,
            yaml_config=yaml_config,
        )
        self.final_page_id = id
        self.result_handler_config = yaml_config.get("resultHandler", {})
        return final_page

    def get_all_pages(self) -> list["FormPage"]:
        """
        Retrieve all pages in the flow.
        """
        return self.pages.values()

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
        if not self.starting_page_id:
            raise ValueError("Starting page is not set for this flow")
        return self.get_page_by_id(self.starting_page_id)

    def get_starting_path(self) -> str:
        """
        Get the starting page of the flow.
        """
        starting_page = self.get_starting_page()
        if starting_page.slug == "/":
            return url_for("forms.start_page", form_slug=self.slug)
        else:
            return url_for(
                "forms.page", form_slug=self.slug, page_slug=starting_page.slug
            )

    def get_final_page(self) -> "FormPage":
        """
        Get the final page of the flow.
        """
        if not self.final_page_id:
            raise ValueError("Final page is not set for this flow")
        return self.get_page_by_id(self.final_page_id)

    def get_data(self) -> dict:
        """
        Get the saved data for the flow.
        """
        data = {}
        for page in self.get_all_pages():
            data[page.id] = page.get_saved_form_data()
        return data

    def has_complete_path(self) -> bool:
        """
        Check if all pages in the flow are complete.
        """
        earliest_incomplete_page = self.get_earliest_incomplete_page()
        current_app.logger.debug(
            f"earliest_incomplete_page: {earliest_incomplete_page}"
        )
        return earliest_incomplete_page is None

    def get_earliest_incomplete_page(self) -> Optional["FormPage"]:  # noqa: C901
        """
        Working backwards through the flow, find a required page that is not complete.
        """

        def deep_completion_check(page: "FormPage") -> Optional["FormPage"]:
            current_app.logger.debug(f"=== Deep completion check for '{page.id}' ===")
            if not page.is_complete(temporary_validation=True):
                current_app.logger.debug(f"Page '{page.id}' is not complete")
                return page

            for required_page in page.requires_completion_of:
                failed_page = deep_completion_check(required_page)
                if failed_page is not None:
                    return failed_page

            any_required_pages_complete = []
            for required_page in page.requires_completion_of_any:
                if required_page.is_complete(temporary_validation=True):
                    any_required_pages_complete.append(required_page)
            if (
                len(page.requires_completion_of_any)
                and len(any_required_pages_complete) == 0
            ):
                current_app.logger.debug(
                    "No requires_completion_of_any pages are complete"
                )
                return page.requires_completion_of_any_fallback or page
            failed_page_any_required_page = None
            for required_page in any_required_pages_complete:
                failed_page = deep_completion_check(required_page)
                if failed_page:
                    failed_page_any_required_page = failed_page
            if failed_page_any_required_page is None:
                return failed_page_any_required_page

            for required_page, key, response in page.requires_responses:
                data = required_page.get_saved_form_data()
                if data.get(key, None) != response:
                    current_app.logger.debug(
                        f"requires_responses page '{required_page.id}' key '{key}' does not match expected value '{response}'"
                    )
                    return required_page
                failed_page = deep_completion_check(required_page)
                if failed_page is not None:
                    return failed_page

            return None

        final_page = self.get_final_page()
        failed_page = deep_completion_check(final_page)
        if failed_page is not None:
            return failed_page

        return None

    # TODO
    def set_file_handler(self):
        pass

    def reset(self):
        """
        Reset the flow by clearing all session data related to this flow.
        """
        current_app.logger.debug(f"Resetting form flow for '{self.slug}'")
        session.clear()

    def is_completion_handled(self) -> bool:
        """
        Check if the completion logic has been handled.
        """
        return session.get("completion_handled", False)

    def handle_completion(self) -> bool:
        if self.is_completion_handled():
            current_app.logger.debug("Completion logic has already been handled")
            return True

        if not self.has_complete_path():
            current_app.logger.error(
                "Flow does not have a complete path. Cannot handle completion"
            )
            raise Exception("Flow does not have a complete path")

        success = False

        handler_classes = {
            "email": EmailResultHandler,
            "postgres": PostgresResultHandler,
            "mongodb": MongoDBResultHandler,
            "api": APIResultHandler,
        }
        handler_type = self.result_handler_config.get("type", "")
        if handler_type not in handler_classes:
            raise ValueError(f"Unsupported result handler type: {handler_type}")

        details = self.result_handler_config.get("details", {})
        if not details:
            raise ValueError("Result handler details are not set for this flow")

        try:
            handler = handler_classes[handler_type](**details.get("init", {}))
            handler.process(data=self.get_data(), **details.get("process", {}))
            success = handler.send(**details.get("send", {}))
        except Exception as e:
            current_app.logger.error(f"Error handling form flow completion: {e}")

        if success:
            current_app.logger.debug("Form flow completion handled successfully")
        else:
            current_app.logger.error("Form flow completion handling failed")
        session["completion_handled"] = success


class PageCompletionRule(TypedDict):
    condition: Optional[Callable]
    when: Optional[tuple[str, str]]


class PageCompletionRuleFormPage(PageCompletionRule):
    page: "FormPage"


class PageCompletionRuleFlaskMethod(PageCompletionRule):
    flask_method: str


class PageCompletionRuleURL(PageCompletionRule):
    url: str


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
        body: str = "",
        template: str = "",
        form: Optional[FlaskForm] = None,
        yaml_config: Optional[dict] = None,
    ):
        self.flow: "FormFlow" = flow
        self.id: str = id
        self.name: str = name
        self.slug: str = slug
        self.description: str = description
        self.body: str = body
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
        if self.form_class:
            temp_form = self.form_class()
            for field in temp_form:
                if any(
                    [
                        isinstance(validator, InputRequired)
                        for validator in field.validators
                    ]
                ):
                    raise ValueError(
                        f"Form field '{field.name}' in page '{self.id}' uses 'InputRequired' validator which is not allowed. Use 'DataRequired' instead."
                    )
        self.yaml_config: Optional[dict] = yaml_config

    def __str__(self):
        return f"FormPage({self.id})"

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
            raise ValueError("Either 'page', 'url' or 'flask_method' must be provided")
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

    def is_complete(self, temporary_validation=False) -> bool:
        """
        Check if the form is complete based on the data provided.
        """
        if self.form and not temporary_validation:
            return self.form.validate()
        elif self.form_class:
            temp_form = self.form_class(data=self.get_saved_form_data())
            temp_form._fields.pop("csrf_token", None)
            is_complete = temp_form.validate()
            # if temp_form.errors:
            #     current_app.logger.warning(
            #         f"Form '{self.id}' has errors: {temp_form.errors}"
            #     )
            return is_complete
        return True

    def serve(self) -> Response:
        """
        Start the flow by loading the form data and checking completion status.
        """
        if self.form_class and not self.form:
            self.form = self.form_class(data=self.get_saved_form_data())

        for page in self.requires_completion_of:
            if not page.is_complete():
                current_app.logger.warning(f"Required page '{page.id}' is not complete")
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
                    f"None of the any required pages are complete for '{self.id}'"
                )
                if self.requires_completion_of_any_fallback:
                    current_app.logger.warning(
                        f"Redirecting to fallback page: {self.requires_completion_of_any_fallback.id}"
                    )
                    return redirect(
                        self.requires_completion_of_any_fallback.get_page_path()
                    )
                else:
                    redirect_to_page = next(
                        (
                            p
                            for p in self.requires_completion_of_any
                            if not p.is_complete()
                        ),
                        self.requires_completion_of_any[0],
                    )
                    current_app.logger.warning(
                        f"Redirecting to first required incomplete page: {redirect_to_page.id}"
                    )
                    return redirect(redirect_to_page.get_page_path())

        for requires_responses in self.requires_responses:
            (page, key, required_response) = requires_responses
            data = page.get_saved_form_data()
            if data.get(key, None) != required_response:
                current_app.logger.warning(
                    f"Required response '{required_response}' not found for key '{key}' in page '{page.id}'"
                )
                return redirect(page.get_page_path())

        if self.flow.has_complete_path():
            self.flow.handle_completion()

        return self.validate_and_redirect()

    def process_file(self, file_field: FileField | MultipleFileField) -> str:
        """
        Process file uploads if the form contains file fields.
        """
        return "foobar.jpg"  # Placeholder value

    def validate_and_redirect(  # noqa: C901
        self,
    ) -> Response:  # TODO: Refactor this method
        """
        Validate the form data when the page is submitted and redirect based on completion status.
        """
        if request.method == "POST" and self.is_complete():
            form_data = self.form.data
            form_data.pop("csrf_token", None)
            for field in self.form.data:
                if isinstance(self.form[field], FileField) or isinstance(
                    self.form[field], MultipleFileField
                ):
                    # TODO: Handle file saving
                    print(f"Removing file field '{field}' from saved data")
                    form_data.pop(field, None)
                    file = self.process_file(self.form[field])
                    form_data[field] = file
            self.save_form_data(form_data)

        if self.flow.is_completion_handled() and self != self.flow.get_final_page():
            return redirect(self.flow.get_final_page().get_page_path())

        if request.method == "POST" and self.is_complete():
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

            raise Exception("No matching completion rule found")

        # if not self.flow.has_complete_path() and self.flow.get_earliest_incomplete_page() != self:
        #     current_app.logger.warning(
        #         f"Flow does not have a complete path. Redirecting to earliest incomplete page"
        #     )
        #     return redirect(self.flow.get_earliest_incomplete_page().get_page_path())

        return render_template(
            self.template,
            flow=self.flow,
            pageTitle=self.name,
            description=self.description,
            body=self.body,
            page_path=self.get_page_path(),
            form_reset_path=url_for("forms.reset_form", form_slug=self.flow.slug),
            form=self.form,
            has_complete_path=self.flow.has_complete_path(),
            earliest_incomplete_page=self.flow.get_earliest_incomplete_page(),
            handle_files="fileHandler" in self.yaml_config,
            completion_handled=self.flow.is_completion_handled(),
            pages=self.flow.get_all_pages(),
        )
