import datetime
from collections.abc import Callable
from typing import Optional, TypedDict

from altcha import verify_solution
from app.lib.cache import cache
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
from wtforms import FileField, FormField, MultipleFileField
from wtforms.validators import InputRequired

from .result_handlers import (
    APIResultHandler,
    EmailResultHandler,
    MongoDBResultHandler,
    PostgresResultHandler,
)


class ResultHandlerResult(TypedDict):
    type: str
    success: bool
    result: dict


class FormFlow:
    """
    Represents a collection of form pages in a flow.
    Each page can have requirements for completion and can redirect to another page when complete.
    """

    def __init__(
        self,
        slug: str,
        config_hash: Optional[str] = "",
        metadata: Optional[dict] = None,
    ):
        self.slug = slug
        self.pages: dict[str, "FormPage"] = {}
        self.starting_page_id: str = ""
        self.final_page_id: str = ""
        self.metadata: dict = metadata if metadata else {}
        self.result_handlers_config: Optional[list[dict]] = None
        if session.get("config_hash", "") != config_hash:
            current_app.logger.warning("Form configuration has changed, resetting flow")
            self.reset()
            session["config_hash"] = config_hash

    def meta(self, key: str, default=None):
        """
        Get metadata for the flow.
        """
        return self.metadata.get(key, default)

    def create_page(
        self,
        id: str,
        name: str,
        slug: str,
        content: dict = {},
        template: str = "",
        form: Optional[FlaskForm] = None,
        altcha: bool = False,
        yaml_config: dict = {},
    ):
        """
        Add a page to the flow.
        """
        new_page = FormPage(
            flow=self,
            id=id,
            name=name,
            slug=slug,
            content=content,
            template=template,
            form=form,
            altcha=altcha,
            yaml_config=yaml_config,
        )
        self.pages.update({id: new_page})
        return new_page

    def create_starting_page(
        self,
        id: str,
        name: str,
        slug: str = "/",
        content: dict = {},
        template: str = "",
        form: Optional[FlaskForm] = None,
        altcha: bool = False,
        yaml_config: dict = {},
    ):
        """
        Set the starting page of the flow.
        """
        starting_page = self.create_page(
            id=id,
            name=name,
            slug=slug,
            content=content,
            template=template,
            form=form,
            altcha=altcha,
            yaml_config=yaml_config,
        )
        self.starting_page_id = id
        return starting_page

    def create_final_page(
        self,
        id: str,
        name: str,
        slug: str = "/",
        content: dict = {},
        template: str = "",
        yaml_config: dict = {},
    ):
        """
        Set the final page of the flow.
        """
        final_page = self.create_page(
            id=id,
            name=name,
            slug=slug,
            content=content,
            template=template,
            form=None,
            yaml_config=yaml_config,
        )
        self.final_page_id = id
        if yaml_config and "resultHandlers" in yaml_config:
            self.result_handlers_config = yaml_config.get("resultHandlers", {})
        return final_page

    def get_all_pages(self) -> list["FormPage"]:
        """
        Retrieve all pages in the flow.
        """
        return list(self.pages.values())

    def get_page_by_id(self, id: str) -> "FormPage":
        """
        Retrieve a page by its id.
        """
        if not id:
            raise ValueError("Page id must be provided")
        if id in self.pages:
            return self.pages[id]
        if id == "startingPage":
            return self.get_starting_page()
        if id == "finalPage":
            return self.get_final_page()
        raise KeyError(f"Page with id '{id}' not found in flow")

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
        try:
            return self.get_page_by_id(self.starting_page_id)
        except KeyError:
            raise ValueError("Starting page is not found in this flow")

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
        try:
            return self.get_page_by_id(self.final_page_id)
        except KeyError:
            raise ValueError("Final page is not found in this flow")

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
        return self.get_earliest_incomplete_page() is None

    def get_earliest_incomplete_page(self) -> Optional["FormPage"]:  # noqa: C901
        """
        Working backwards through the flow, find a required page that is not complete.
        """
        if hasattr(self, "earliest_incomplete_page"):
            current_app.logger.debug(
                f"Using cached earliest_incomplete_page '{self.earliest_incomplete_page}'"
            )
            return self.earliest_incomplete_page

        def deep_completion_check(page: "FormPage") -> Optional["FormPage"]:
            current_app.logger.debug(f"Deep completion check for '{page.id}'")
            if page.form and not page.is_complete(temporary_validation=True):
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
            self.earliest_incomplete_page = failed_page
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
        return (
            all(result["success"] for result in self.get_completion_results())
            if len(self.get_completion_results())
            else False
        )

    def get_completion_results(self) -> list[ResultHandlerResult]:
        """
        Get the results of the completion handlers.
        """
        return session.get("completion_results", [])

    def get_completion_result_first_id(self) -> str:
        """
        Get the ID of the first completion result.
        """
        results = self.get_completion_results()
        if len(results) and "result" in results[0] and "id" in results[0]["result"]:
            return results[0]["result"]["id"]
        return ""

    def handle_completion(self) -> bool:
        if self.is_completion_handled():
            current_app.logger.debug("Completion logic has already been handled")
            return True

        if not self.has_complete_path():
            current_app.logger.error(
                "Flow does not have a complete path. Cannot handle completion"
            )
            raise Exception("Flow does not have a complete path")

        success = True

        handler_classes = {
            "email": EmailResultHandler,
            "postgres": PostgresResultHandler,
            "mongodb": MongoDBResultHandler,
            "api": APIResultHandler,
        }

        results = []

        if self.result_handlers_config:
            for result_handler in self.result_handlers_config:
                current_app.logger.debug(f"Processing result handler: {result_handler}")
                handler_type = result_handler.get("type", "")
                if handler_type not in handler_classes:
                    raise ValueError(f"Unsupported result handler type: {handler_type}")

                details = result_handler.get("details", {})
                if not details:
                    raise ValueError("Result handler details are not set for this flow")

                handler = None
                try:
                    handler = handler_classes[handler_type](**details.get("init", {}))
                    handler.process(data=self.get_data(), **details.get("process", {}))
                    handler_success = handler.send(**details.get("send", {}))
                    if handler_success:
                        results.append(
                            {
                                "type": handler_type,
                                "success": True,
                                "result": handler.result(),
                            }
                        )
                    else:
                        current_app.logger.error(
                            f"Result handler '{handler_type}' failed to send"
                        )
                        results.append(
                            {
                                "type": handler_type,
                                "success": False,
                                "result": handler.result(),
                            }
                        )
                except Exception as e:
                    current_app.logger.error(
                        f"Error handling form flow completion: {e}"
                    )
                    results.append(
                        {
                            "type": handler_type,
                            "success": False,
                            "result": handler.result() if handler is not None else {},
                        }
                    )

        success = all(result["success"] for result in results)

        if success:
            current_app.logger.debug("Form flow completion handled successfully")
        else:
            current_app.logger.error("Form flow completion handling failed")
        # session["completion_handled"] = success
        session["completion_results"] = results

        return success


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
        content: Optional[dict] = {},
        template: str = "",
        form: Optional[FlaskForm] = None,
        altcha: bool = False,
        yaml_config: Optional[dict] = None,
    ):
        self.flow: "FormFlow" = flow
        self.id: str = id
        self.name: str = name
        self.slug: str = slug
        self.content: Optional[dict] = content
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
                        f"Field '{field.name}' in page '{self.id}' uses 'InputRequired' validator which is not allowed. Use 'DataRequired' instead."
                    )
                if isinstance(field, FormField):
                    for sub_field in field:
                        if any(
                            [
                                isinstance(validator, InputRequired)
                                for validator in sub_field.validators
                            ]
                        ):
                            raise ValueError(
                                f"Form sub-field '{sub_field.name}' in page '{self.id}' uses 'InputRequired' validator which is not allowed. Use 'DataRequired' instead."
                            )
        self.altcha: bool = altcha
        self.yaml_config: Optional[dict] = yaml_config

    def __str__(self):
        return f"FormPage({self.id})"

    def get_page_path(self, external=False) -> str:
        """
        Get the path for this page.
        """
        if self.slug == "/":
            return url_for(
                "forms.start_page",
                form_slug=self.flow.slug,
                _scheme="https" if external else None,
                _external=external,
            )
        return url_for(
            "forms.page",
            form_slug=self.flow.slug,
            page_slug=self.slug,
            _scheme="https" if external else None,
            _external=external,
        )

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
        print(f"Saving form data for page '{self.id}': {form_data}")
        session[self.id] = form_data

    def altcha_verified(self) -> bool:
        """
        Check if the altcha solution is verified or has been verified in the past.
        """
        if not self.altcha:
            return True

        if request.method != "POST":
            return session.get(f"altcha_{self.id}", True)

        altcha_payload = request.form.to_dict().get("altcha", "")
        if not altcha_payload:
            session[f"altcha_{self.id}"] = False
            return False

        solved_altchas = cache.get("solved_altchas", [])
        if altcha_payload in solved_altchas:
            current_app.logger.warn("Previously solved altcha used")
            session[f"altcha_{self.id}"] = False
            return False

        try:
            alcha_verified, err = verify_solution(
                altcha_payload,
                current_app.config.get("ALTCHA_HMAC_KEY", "secret-hmac-key"),
                True,
            )
        except Exception as e:
            current_app.logger.error(f"Error verifying altcha: {e}")
            session[f"altcha_{self.id}"] = False
            return False

        session[f"altcha_{self.id}"] = alcha_verified
        if alcha_verified:
            solved_altchas.append(altcha_payload)
            cache.set("solved_altchas", solved_altchas)
        return alcha_verified

    def is_complete(self, temporary_validation=False) -> bool:
        """
        Check if the form is complete based on the data provided.
        """
        if self.form and not temporary_validation:
            vaild_form = self.form.validate()
            return vaild_form and self.altcha_verified()
        elif self.form_class:
            temp_form = self.form_class(data=self.get_saved_form_data())
            temp_form._fields.pop("csrf_token", None)
            # for field in temp_form._fields:
            #     if isinstance(field, FormField):
            #         for sub_field in field:
            #             sub_field.pop("csrf_token", None)
            is_complete = temp_form.validate()
            if not is_complete:
                current_app.logger.debug(temp_form.errors)
            return is_complete and self.altcha_verified()
        return True

    def process_file(self, file_field: FileField | MultipleFileField) -> str:
        """
        Process file uploads if the form contains file fields.
        """
        return "foobar.jpg"  # Placeholder value

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
            page, key, required_response = requires_responses
            data = page.get_saved_form_data()
            if data.get(key, None) != required_response:
                current_app.logger.warning(
                    f"Required response '{required_response}' not found for key '{key}' in page '{page.id}'"
                )
                return redirect(page.get_page_path())

        if self.flow.has_complete_path():
            self.flow.handle_completion()

        return self.validate_and_redirect()

    def validate_and_redirect(  # noqa: C901
        self,
    ) -> Response:  # TODO: Refactor this method
        """
        Validate the form data when the page is submitted and redirect based on completion status.
        """
        if self.flow.is_completion_handled() and self != self.flow.get_final_page():
            return redirect(self.flow.get_final_page().get_page_path())

        if self.form and request.method == "POST":
            form_data = self.form.data
            form_data.pop("csrf_token", None)
            for field in form_data:
                print()
                print(f"Processing field '{field}'")
                print(type(form_data[field]))
                if isinstance(form_data[field], (FileField, MultipleFileField)):
                    # TODO: Handle file saving
                    print(f"Removing file field '{field}' from saved data")
                    form_data.pop(field, None)
                    file = self.process_file(form_data[field])
                    form_data[field] = file
                # elif isinstance(form_data[field], FormField):
                #     form_data[field].pop("csrf_token", None)
                # TODO: Remove on next release of TNA Frontend Jinja which can handle datetime objects
                elif isinstance(form_data[field], datetime.date):
                    print("Date field")
                    form_data[field] = form_data[field].strftime("%d %m %Y")
            self.save_form_data(form_data)

            if self.is_complete():
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
                        if "page" in rule and rule["page"]:
                            current_app.logger.debug(
                                f"Redirecting to page: '{rule['page'].id}'"
                            )
                            return redirect(rule["page"].get_page_path())

                        if "flask_method" in rule and rule["flask_method"]:
                            current_app.logger.debug(
                                f"Redirecting to Flask method: '{rule['flask_method']}'"
                            )
                            return redirect(url_for(rule["flask_method"]))

                        if "url" in rule and rule["url"]:
                            current_app.logger.debug(
                                f"Redirecting to URL: {rule['url']}"
                            )
                            return redirect(rule["url"])

                raise Exception("No matching completion rule found")
        else:
            if self.altcha and f"altcha_{self.id}" in session:
                session.pop(f"altcha_{self.id}")

        # if not self.flow.has_complete_path() and self.flow.get_earliest_incomplete_page() != self:
        #     current_app.logger.warning(
        #         f"Flow does not have a complete path. Redirecting to earliest incomplete page"
        #     )
        #     return redirect(self.flow.get_earliest_incomplete_page().get_page_path())

        return render_template(
            self.template,
            flow=self.flow,
            pageTitle=self.name,
            content=self.content,
            altcha=self.altcha,
            altcha_verified=self.altcha_verified(),
            page_path=self.get_page_path(),
            form_reset_path=url_for("forms.reset_form", form_slug=self.flow.slug),
            form=self.form,
            has_complete_path=self.flow.has_complete_path(),
            earliest_incomplete_page=self.flow.get_earliest_incomplete_page(),
            handle_files="fileHandler" in self.yaml_config,
            completion_handled=self.flow.is_completion_handled(),
            completion_results=self.flow.get_completion_results(),
            get_completion_result_first_id=self.flow.get_completion_result_first_id(),
            pages=self.flow.get_all_pages(),
            get_page_by_id=self.flow.get_page_by_id,
            final_page=self.flow.get_final_page(),
        )
