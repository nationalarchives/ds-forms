# import datetime
import hashlib
from collections.abc import Callable
from typing import Optional

from altcha import verify_solution
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

from app.lib.cache import cache

from .result_handlers import (
    RESULT_HANDLER_CLASSES,
    ResultHandlerResult,
)


class FormFlow:
    """
    Represents a collection of form pages in a flow.
    Each page can have requirements for completion and can redirect to another page when complete.
    """

    def __init__(
        self,
        path: str,
        config_hash: str | None = "",
        metadata: dict | None = None,
    ):
        self.path = path
        self.pages: dict[str, FormPage] = {}
        self.starting_page_id: str = ""
        self.final_page_id: str = ""
        self.metadata: dict = metadata if metadata else {}
        self.result_handlers_config: list[dict] | None = None
        if session.get(self.path, {}).get("config_hash", "") != config_hash:
            current_app.logger.warning("Form configuration has changed, resetting flow")
            self.reset()
            session.setdefault(self.path, {})["config_hash"] = config_hash
        self.reference_number: str = hashlib.md5(
            session.sid.encode("utf-8")
        ).hexdigest()[:8]

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
        content: dict | None = None,
        template: str = "",
        form: FlaskForm | None = None,
        altcha: bool = False,
        yaml_config: dict | None = None,
    ):
        """
        Add a page to the flow.
        """
        if yaml_config is None:
            yaml_config = {}
        if content is None:
            content = {}
        new_page = FormPage(
            flow=self,
            id=id,
            name=name,
            slug=slug,
            content=content,
            template=template,
            form=form,
            form_path=self.path,
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
        content: dict | None = None,
        template: str = "",
        form: FlaskForm | None = None,
        altcha: bool = False,
        yaml_config: dict | None = None,
    ):
        """
        Set the starting page of the flow.
        """
        if yaml_config is None:
            yaml_config = {}
        if content is None:
            content = {}
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
        content: dict | None = None,
        template: str = "",
        yaml_config: dict | None = None,
    ):
        """
        Set the final page of the flow.
        """
        if yaml_config is None:
            yaml_config = {}
        if content is None:
            content = {}
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
        except KeyError as e:
            raise ValueError("Starting page is not found in this flow") from e

    def get_starting_path(self) -> str:
        """
        Get the starting page of the flow.
        """
        starting_page = self.get_starting_page()
        if starting_page.slug == "/":
            return url_for("forms.start_page", form_path=self.path)
        return url_for("forms.page", form_path=self.path, page_slug=starting_page.slug)

    def get_final_page(self) -> "FormPage":
        """
        Get the final page of the flow.
        """
        if not self.final_page_id:
            raise ValueError("Final page is not set for this flow")
        try:
            return self.get_page_by_id(self.final_page_id)
        except KeyError as e:
            raise ValueError("Final page is not found in this flow") from e

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

    def get_earliest_incomplete_page(self) -> Optional["FormPage"]:
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
        current_app.logger.debug(f"Resetting form flow for '{self.path}'")
        session.pop(self.path, None)

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
        return session.get(self.path, {}).get("completion_results", [])

    def handle_completion(self) -> bool:
        if self.is_completion_handled():
            current_app.logger.debug("Completion logic has already been handled")
            return True

        if not self.has_complete_path():
            current_app.logger.warning(
                "Flow does not have a complete path. Cannot handle completion"
            )
            raise ValueError("Flow does not have a complete path")

        success = True
        results = []

        if self.result_handlers_config:
            for result_handler in self.result_handlers_config:
                current_app.logger.debug(f"Processing result handler: {result_handler}")
                handler_type = result_handler.get("type", "")
                if handler_type not in RESULT_HANDLER_CLASSES:
                    raise ValueError(f"Unsupported result handler type: {handler_type}")

                details = result_handler.get("details", {})
                if not details:
                    raise ValueError("Result handler details are not set for this flow")

                handler = None
                try:
                    handler = RESULT_HANDLER_CLASSES[handler_type](
                        **details.get("init", {})
                    )
                    handler.process(
                        data={
                            "data": self.get_data(),
                            "reference_number": self.reference_number,
                        },
                        **details.get("process", {}),
                    )
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
                except Exception:
                    current_app.logger.exception("Error handling form flow completion")
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
        session.setdefault(self.path, {})["completion_results"] = results

        return success


class CompletionRedirectRule:
    """
    Base class for a redirect target that applies once a page is completed.
    Subclasses provide the actual redirect destination via `resolve`.
    """

    def __init__(
        self,
        when: tuple[str, str] | None = None,
        condition: Callable | None = None,
    ):
        self.when = when
        self.condition = condition

    def matches(self, form_data: dict) -> bool:
        """
        Determine whether this rule applies to the given submitted form data.
        """
        if self.when is None and self.condition is None:
            return True
        if self.when and form_data.get(self.when[0], None) == self.when[1]:
            return True
        return bool(self.condition and self.condition(form_data))

    def resolve(self) -> str:
        """
        Get the URL to redirect to when this rule matches.
        """
        raise NotImplementedError("Subclasses must implement the resolve method")


class PageRedirectRule(CompletionRedirectRule):
    def __init__(self, page: "FormPage", **kwargs):
        super().__init__(**kwargs)
        self.page = page

    def __str__(self):
        return f"PageRedirectRule(page={self.page.id})"

    def resolve(self) -> str:
        return self.page.get_page_path()


class FlaskMethodRedirectRule(CompletionRedirectRule):
    def __init__(self, flask_method: str, **kwargs):
        super().__init__(**kwargs)
        self.flask_method = flask_method

    def __str__(self):
        return f"FlaskMethodRedirectRule(flask_method={self.flask_method})"

    def resolve(self) -> str:
        return url_for(self.flask_method)


class URLRedirectRule(CompletionRedirectRule):
    def __init__(self, url: str, **kwargs):
        super().__init__(**kwargs)
        self.url = url

    def __str__(self):
        return f"URLRedirectRule(url={self.url})"

    def resolve(self) -> str:
        return self.url


class AltchaVerifier:
    """
    Verifies altcha proof-of-work solutions, independent of any particular form page.
    """

    def __init__(self, hmac_key_config: str = "ALTCHA_HMAC_KEY"):
        self.hmac_key_config = hmac_key_config

    def verify(self, payload: str) -> bool:
        """
        Verify an altcha payload, rejecting empty or previously-solved payloads.
        """
        if not payload:
            return False

        if payload in (cache.get("solved_altchas") or []):
            current_app.logger.warning("Previously solved altcha used")
            return False

        try:
            verified, _err = verify_solution(
                payload,
                current_app.config.get(self.hmac_key_config, "secret-hmac-key"),
                True,
            )
        except Exception:
            current_app.logger.exception("Error verifying altcha")
            return False

        return verified

    def mark_solved(self, payload: str):
        """
        Record a payload as solved so it cannot be reused.
        """
        solved_altchas = cache.get("solved_altchas") or []
        solved_altchas.append(payload)
        cache.set("solved_altchas", solved_altchas)


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
        content: dict | None = None,
        template: str = "",
        form: FlaskForm | None = None,
        form_path: str = "",
        altcha: bool = False,
        yaml_config: dict | None = None,
        altcha_verifier: "AltchaVerifier | None" = None,
    ):
        self.flow: FormFlow = flow
        self.id: str = id
        self.name: str = name
        self.slug: str = slug
        self.content: dict | None = content if content is not None else {}
        self.template: str = template if template else "forms/form_page.html"
        self.requires_completion_of: list[FormPage] = []
        self.requires_completion_of_any: list[FormPage] = []
        self.requires_completion_of_any_fallback: FormPage | None = None
        self.requires_responses: list[tuple[FormPage, str, str]] = []
        self.when_complete: list[CompletionRedirectRule] = []
        # self.clear_pages_on_completion: list[FormPage] = []
        self.form: FlaskForm | None = None
        self.form_class: FlaskForm | None = form if form else None
        self.form_path: str = form_path
        if self.form_class:
            temp_form = self.form_class()
            for field in temp_form:
                if any(
                    isinstance(validator, InputRequired)
                    for validator in field.validators
                ):
                    raise ValueError(
                        f"Field '{field.name}' in page '{self.id}' uses 'InputRequired' validator which is not allowed. Use 'DataRequired' instead."
                    )
                if isinstance(field, FormField):
                    for sub_field in field:
                        if any(
                            isinstance(validator, InputRequired)
                            for validator in sub_field.validators
                        ):
                            raise ValueError(
                                f"Form sub-field '{sub_field.name}' in page '{self.id}' uses 'InputRequired' validator which is not allowed. Use 'DataRequired' instead."
                            )
        self.altcha: bool = altcha
        self.yaml_config: dict = yaml_config if yaml_config is not None else {}
        self.altcha_verifier: AltchaVerifier = altcha_verifier or AltchaVerifier()

    def __str__(self):
        return f"FormPage({self.id})"

    def _get_response_field(self, key: str, default=None):
        """
        Get a single field from this page's saved response data.
        """
        return self.get_saved_form_data().get(key, default)

    def _set_response_field(self, key: str, value):
        """
        Set a single field on this page's saved response data.
        """
        session.setdefault(self.form_path, {}).setdefault("responses", {}).setdefault(
            self.id, {}
        )[key] = value

    def get_page_path(self, external=False) -> str:
        """
        Get the path for this page.
        """
        if self.slug == "/":
            return url_for(
                "forms.start_page",
                form_path=self.flow.path,
                _scheme="https" if external else None,
                _external=external,
            )
        return url_for(
            "forms.page",
            form_path=self.flow.path,
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
        flask_method: str | None = "",
        url: str | None = "",
        when: tuple[str, str] | None = None,
        condition: Callable | None = None,
    ):
        """
        Set the page to redirect to when this page is completed.
        """
        if not (page or flask_method or url):
            raise ValueError("Either 'page', 'url' or 'flask_method' must be provided")
        if page:
            rule = PageRedirectRule(page=page, when=when, condition=condition)
        elif flask_method:
            rule = FlaskMethodRedirectRule(
                flask_method=flask_method, when=when, condition=condition
            )
        else:
            rule = URLRedirectRule(url=url, when=when, condition=condition)
        self.when_complete.append(rule)
        return self

    # def clear_on_completion(self, *pages: "FormPage"):
    #     """
    #     Specify which pages should be cleared from the session when this page is completed.
    #     """
    #     self.clear_pages_on_completion.extend(pages)
    #     return self

    def get_saved_form_data(self):
        """
        Get the form data from the session or other storage.
        """
        return session.get(self.form_path, {}).get("responses", {}).get(self.id, {})

    def save_form_data(self, form_data: dict):
        """
        Save the form data to the session.
        """
        current_app.logger.debug(f"Saving form data for page '{self.id}'")
        session.setdefault(self.form_path, {}).setdefault("responses", {})[self.id] = (
            form_data
        )

    def altcha_verified(self, save_result: bool = True) -> bool:
        """
        Check if the altcha solution is verified or has been verified in the past.
        """
        if not self.altcha:
            return True

        if request.method != "POST":
            return self._get_response_field("altcha", True)

        altcha_payload = request.form.to_dict().get("altcha", "")
        verified = self.altcha_verifier.verify(altcha_payload)
        self._set_response_field("altcha", verified)
        if verified and save_result:
            self.altcha_verifier.mark_solved(altcha_payload)
        return verified

    def is_complete(self, temporary_validation=False) -> bool:
        """
        Check if the form is complete based on the data provided.
        """
        if self.form and not temporary_validation:
            valid_form = self.form.validate()
            return valid_form and self.altcha_verified(save_result=False)
        if self.form_class:
            temp_form = self.form_class(data=self.get_saved_form_data())
            temp_form._fields.pop("csrf_token", None)
            # TODO: Nested forms with CSRF
            # for field in temp_form._fields:
            #     if isinstance(field, FormField):
            #         for sub_field in field:
            #             sub_field.pop("csrf_token", None)
            is_complete = temp_form.validate()
            if not is_complete:
                current_app.logger.debug(temp_form.errors)
            return is_complete and self.altcha_verified(save_result=False)
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
                redirect_to_page = next(
                    (p for p in self.requires_completion_of_any if not p.is_complete()),
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

        if self.flow.has_complete_path() and self.flow.get_final_page() == self:
            self.flow.handle_completion()

        return self.validate_and_redirect()

    def validate_and_redirect(
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
                current_app.logger.debug(f"Processing field '{field}'")
                if isinstance(form_data[field], (FileField, MultipleFileField)):
                    # TODO: Handle file saving
                    # current_app.logger.debug(f"Removing file field '{field}' from saved data")
                    form_data.pop(field, None)
                    file = self.process_file(form_data[field])
                    form_data[field] = file
                # elif isinstance(form_data[field], FormField):
                #     form_data[field].pop("csrf_token", None)
                # TODO: Remove on next release of TNA Frontend Jinja which can handle datetime objects
                # elif isinstance(form_data[field], datetime.date):
                #     form_data[field] = form_data[field].strftime("%d %m %Y")
            self.save_form_data(form_data)

            if self.is_complete() and self.altcha_verified(save_result=True):
                # for page in self.clear_pages_on_completion:
                #     if page.id in session.get(self.form_path, {}).get("responses", {}):
                #         current_app.logger.debug(f"Clearing page data for: {page.id}")
                #         session[self.form_path]["responses"].pop(page.id, None)

                for rule in self.when_complete:
                    current_app.logger.debug(f"Checking completion rule: {rule}")
                    if rule.matches(form_data):
                        current_app.logger.debug(
                            f"Completion rule matched for page: '{self.id}'"
                        )
                        return redirect(rule.resolve())

                raise ValueError("No matching completion rule found")
        elif self.altcha and f"altcha_{self.id}" in session.get(self.form_path, {}).get(
            "responses", {}
        ):
            session[self.form_path]["responses"].pop(f"altcha_{self.id}")

        # if not self.flow.has_complete_path() and self.flow.get_earliest_incomplete_page() != self:
        #     current_app.logger.warning(
        #         f"Flow does not have a complete path. Redirecting to earliest incomplete page"
        #     )
        #     return redirect(self.flow.get_earliest_incomplete_page().get_page_path())

        view = render_template(
            self.template,
            flow=self.flow,
            pageTitle=self.name,
            content=self.content,
            altcha=self.altcha,
            altcha_verified=self.altcha_verified(save_result=False),
            page_path=self.get_page_path(),
            form_reset_path=url_for("forms.reset_form", form_path=self.flow.path),
            form=self.form,
            has_complete_path=self.flow.has_complete_path(),
            earliest_incomplete_page=self.flow.get_earliest_incomplete_page(),
            handle_files="fileHandler" in self.yaml_config,
            completion_handled=self.flow.is_completion_handled(),
            completion_results=self.flow.get_completion_results(),
            reference_number=self.flow.reference_number,
            pages=self.flow.get_all_pages(),
            get_page_by_id=self.flow.get_page_by_id,
            final_page=self.flow.get_final_page(),
        )

        # if self.flow.is_completion_handled() and self == self.flow.get_final_page():
        #     self.flow.reset()

        return view
