import json
import os
from abc import ABC

from flask import current_app, render_template
from requests import codes, get, post


class ResultHandler(ABC):
    """
    Base class for result handlers.
    This class should be extended to implement specific result handling logic.
    """

    def __init__(self, **kwargs):
        raise NotImplementedError(
            "Subclasses must implement the __init__ dunder method"
        )

    def process(self, data: dict, **kwargs):
        raise NotImplementedError("Subclasses must implement the process method")

    def send(self, **kwargs) -> bool:
        raise NotImplementedError("Subclasses must implement the send method")


class EmailResultHandler(ResultHandler):
    """
    Handles the result of a form submission by sending an email.
    """

    def __init__(self, **kwargs):
        self.smtpServer: str = os.environ.get(kwargs.get("smtpServer"), "")
        self.smtpPort: int = os.environ.get(kwargs.get("smtpPort"), 25)
        self.smtpUser: str = os.environ.get(kwargs.get("smtpUser"), "")
        self.smtpPassword: str = os.environ.get(kwargs.get("smtpPassword"), "")
        if not any([self.smtpServer, self.smtpUser, self.smtpPassword]):
            raise ValueError("SMTP configuration is not set properly")
        self.content: str = ""

    def process(self, data: dict, **kwargs):
        if template := kwargs.get("template"):
            self.content = render_template(
                template,
                responses=data,
            )
        else:
            self.content = json.dumps({"foo": "bar"}, indent=2)

    def send(self, **kwargs) -> bool:
        if not self.content:
            raise ValueError("Email content is empty. Call process() first.")
        to_email = kwargs.get("to", "")
        subject = kwargs.get("subject", "Form Submission")
        from_email = kwargs.get("from", "noreply@nationalarchives.gov.uk")
        if not to_email:
            raise ValueError("Recipient email address must be provided")
        # TODO: Implement actual email sending logic
        return True


class APIResultHandler(ResultHandler):
    """
    Handles the result of a form submission by sending it to an external API.
    """

    def __init__(self, **kwargs):
        self.url = kwargs.get("url", "")
        self.method = kwargs.get("method", "").upper()
        self.headers = kwargs.get("headers", "")
        self.params = kwargs.get("params", {})

        if not any([self.url, self.method]):
            raise ValueError("API URL and method must be provided")

    def process(self, data: dict, **kwargs):
        self.content = data
        pass

    def send(self, **kwargs) -> bool:
        if not self.content:
            raise ValueError("Email content is empty. Call process() first.")

        try:
            if self.method == "GET":
                response = get(self.url, headers=self.headers, params=self.params)
                return response.status_code == codes.ok
            elif self.method == "POST":
                response = post(
                    self.url,
                    json=self.content,
                    headers=self.headers,
                    params=self.params,
                )
                return response.status_code == codes.ok
            else:
                raise ValueError(f"Unsupported HTTP method: {self.method}")
        except Exception as e:
            current_app.logger.error(f"APIResultHandler error: {e}")
            return False


class PostgresResultHandler(ResultHandler):
    """
    Handles the result of a form submission by saving it to a PostgreSQL database.
    """

    def __init__(self, **kwargs):
        pass

    def process(self, data: dict, **kwargs):
        pass

    def send(self, **kwargs) -> bool:
        pass


class MongoDBResultHandler(ResultHandler):
    """
    Handles the result of a form submission by saving it to MongoDB.
    """

    def __init__(self, **kwargs):
        pass

    def process(self, data: dict, **kwargs):
        pass

    def send(self, **kwargs) -> bool:
        pass
