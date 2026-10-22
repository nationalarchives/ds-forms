import os
import uuid
from abc import ABC, abstractmethod
from functools import reduce
from typing import TypedDict

import boto3
from flask import current_app, render_template
from jinja2 import Template
from requests import codes, get, post
from tna_utilities.api import SimpleJsonApiClient


def deep_get(dictionary, keys, default=None):
    return reduce(
        lambda d, key: d.get(key, default) if isinstance(d, dict) else default,
        keys.split("."),
        dictionary,
    )


class ResultHandlerResult(TypedDict):
    type: str
    success: bool
    result: dict


class ResultHandler(ABC):
    """
    Base class for result handlers.
    This class should be extended to implement specific result handling logic.
    """

    @abstractmethod
    def __init__(self, **kwargs):
        raise NotImplementedError(
            "Subclasses must implement the __init__ dunder method"
        )

    def id(self) -> str:
        # ------------------------------------------
        # These IDs are not guaranteed to be unique,
        # but are sufficient for our purposes - on a
        # list of 10 million generated IDs, the rate
        # of collision is about 0.01%, or about 1 in
        # 10,000
        # ------------------------------------------
        return str(uuid.uuid4())[:8]

    @abstractmethod
    def process(self, data: dict, **kwargs):
        raise NotImplementedError("Subclasses must implement the process method")

    @abstractmethod
    def send(self, **kwargs) -> bool:
        raise NotImplementedError("Subclasses must implement the send method")

    @abstractmethod
    def result(self) -> dict:
        raise NotImplementedError("Subclasses must implement the result method")


class EmailResultHandler(ResultHandler):
    """
    Handles the result of a form submission by sending an email.
    """

    def __init__(self, **kwargs):
        self.client = boto3.client(
            "ses",
            region_name=current_app.config["AWS_REGION"],
            endpoint_url=current_app.config.get("SES_ENDPOINT", None),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", None),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", None),
        )
        self.template: str = ""
        self.template_string: str = ""
        self.data: dict = {}
        self.processed = False
        self.content: str = ""
        self.result_data: dict = {}

    def process(self, data: dict, **kwargs):
        self.template = kwargs.get("template", "")
        self.template_string = kwargs.get("templateString", "")
        self.data = {
            k: v for k, v in kwargs.items() if k != "template" and k != "templateString"
        }
        self.data.update(data)
        current_app.logger.debug(f"Processing email with data: {self.data}")
        current_app.logger.debug(f"Template: {self.template}")
        current_app.logger.debug(f"Template string: {self.template_string}")
        self.processed = True

    def send(self, **kwargs) -> bool:
        current_app.logger.debug("Sending email")
        if not self.processed:
            raise ValueError("Email not processed. Call process() with data first.")
        if self.template:
            self.content = render_template(self.template, data=self.data)
        elif self.template_string:
            self.content = Template(self.template_string).render(
                **self.data, autoescape=True
            )
        else:
            raise ValueError("No template or template string provided")
        to_email = kwargs.get("to", "")
        if not to_email and (to_email_var := kwargs.get("toVar", "")):
            to_email = deep_get(self.data, to_email_var, "")
            if not to_email and isinstance(self.data, dict):
                to_email = deep_get(self.data.get("data", {}), to_email_var, "")
        if not to_email and (to_email_config_var := kwargs.get("toConfigVar", "")):
            to_email = current_app.config.get(to_email_config_var, "")
        if not to_email and (to_email_function := kwargs.get("toFunction", "")):
            try:
                import_path, function_name = to_email_function.rsplit(".", 1)
                current_app.logger.debug(
                    f"Importing {function_name} from {import_path}"
                )
                module = __import__(import_path, fromlist=[function_name])
                to_email = getattr(module, function_name)(self.data)
            except Exception:
                current_app.logger.exception(
                    f"Error calling function {to_email_function}"
                )
        if not to_email:
            to_email = current_app.config["DEFAULT_INBOX"]
        subject = kwargs.get("subject", "Form Submission")
        from_email = kwargs.get("from", current_app.config["DEFAULT_FROM_EMAIL"])
        try:
            response = self.client.send_email(
                Source=from_email,
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {"Html": {"Charset": "UTF-8", "Data": self.content}},
                },
            )
            id = response.get("MessageId")
            current_app.logger.debug(f"Email sent with ID {id}")
            self.result_data = {"id": id}
            return True
        except Exception:
            current_app.logger.exception("EmailResultHandler error")
            return False

    def result(self) -> dict:
        return self.result_data


class APIResultHandler(ResultHandler):
    """
    Handles the result of a form submission by sending it to an external API.
    """

    def __init__(self, **kwargs):
        self.url = kwargs.get("url", "")
        self.method = kwargs.get("method", "").upper()
        self.headers = kwargs.get("headers", "")
        self.params = kwargs.get("params", {})
        self.content: dict | None = None

        if not any([self.url, self.method]):
            raise ValueError("API URL and method must be provided")

    def process(self, data: dict, **kwargs):
        self.content = data

    def send(self, **kwargs) -> bool:
        if not self.content:
            raise ValueError("API content is empty. Call process() first.")
        try:
            if self.method == "GET":
                response = get(self.url, headers=self.headers, params=self.params)
                return response.status_code == codes.ok
            if self.method == "POST":
                response = post(
                    self.url,
                    json=self.content,
                    headers=self.headers,
                    params=self.params,
                )
                return response.status_code == codes.ok
            raise ValueError(f"Unsupported HTTP method: {self.method}")
        except Exception:
            current_app.logger.exception("APIResultHandler error")
            return False

    def result(self) -> dict:
        return {}


class MicrosoftDynamicsResultHandler(ResultHandler):
    """
    Handles the result of a form submission by saving it to Microsoft Dynamics.
    """

    def __init__(self, **kwargs):
        self.api_url = current_app.config.get("DYNAMICS_ENTRA_ORG_URL", "")
        if not self.api_url:
            raise ValueError("API URL must be provided")
        self.processed = False
        self.dynamics_api = SimpleJsonApiClient(
            api_url=self.api_url,
            default_headers={
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
            },
        )

        tenant_id = current_app.config.get("DYNAMICS_ENTRA_TENANT_ID", "")
        client_id = current_app.config.get("DYNAMICS_ENTRA_CLIENT_ID", "")
        client_secret = current_app.config.get("DYNAMICS_ENTRA_CLIENT_SECRET", "")
        scope = current_app.config.get("DYNAMICS_ENTRA_SCOPE", "")
        if not tenant_id or not client_id or not client_secret or not scope:
            raise ValueError(
                "Tenant ID, Client ID, Client Secret, and Scope must be provided"
            )

        dynamics_oauth = SimpleJsonApiClient(
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/"
        )
        current_app.logger.debug("Requesting access token from Microsoft Dynamics")
        dynamics_token_response = dynamics_oauth.post(
            "token",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": scope,
            },
        )
        current_app.logger.debug("Access token response received")
        access_token = dynamics_token_response.json().get("access_token")
        current_app.logger.debug("Obtained access token")

        if not access_token:
            raise ValueError("Failed to obtain access token")

        self.dynamics_api.add_default_header("Authorization", f"Bearer {access_token}")

        self.result_data = {}

    def process(self, data: dict, **kwargs):
        current_app.logger.debug("Preparing data for Microsoft Dynamics")
        self.data = {
            "title": "Website enquiry",
            "description": f"New post from {data.get('title')}",
            "caseorigincode": 3,
            "objecttypecode": 4212,  # Task
        }
        print("=========================")
        print(data)
        print(self.data)

        self.processed = True

    def send(self, **kwargs) -> bool:
        current_app.logger.debug("Sending to Microsoft Dynamics")
        if not self.processed:
            raise ValueError("Data not processed. Call process() with data first.")

        try:
            response = self.dynamics_api.post(
                "incidents", json=self.data, headers={"Prefer": "return=representation"}
            )
            status_code = response.status_code
            print(status_code)
            print(response.text)
            print(response.json())
            if status_code == 204:
                self.result_data = {
                    "status_code": status_code,
                    "new_item_id": response.json().get("QueueItemId"),
                }
                print(self.result_data)
            return status_code == codes.ok
        except Exception:
            current_app.logger.exception("MicrosoftDynamicsResultHandler error")
            return False

    def result(self) -> dict:
        return self.result_data


class PostgresResultHandler(ResultHandler):
    """
    Handles the result of a form submission by saving it to a PostgreSQL database.
    """

    def __init__(self, **kwargs):
        pass

    def process(self, data: dict, **kwargs):
        pass

    def send(self, **kwargs) -> bool:
        return False

    def result(self) -> dict:
        return {}


class MongoDBResultHandler(ResultHandler):
    """
    Handles the result of a form submission by saving it to MongoDB.
    """

    def __init__(self, **kwargs):
        pass

    def process(self, data: dict, **kwargs):
        pass

    def send(self, **kwargs) -> bool:
        return False

    def result(self) -> dict:
        return {}


# Registry of available result handlers, keyed by the "type" used in form YAML config.
# New handler types are added here rather than requiring changes to code that consumes them.
RESULT_HANDLER_CLASSES: dict[str, type[ResultHandler]] = {
    "email": EmailResultHandler,
    "postgres": PostgresResultHandler,
    "mongodb": MongoDBResultHandler,
    "api": APIResultHandler,
    "dynamics": MicrosoftDynamicsResultHandler,
}
