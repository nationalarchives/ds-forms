import uuid
from abc import ABC
from functools import reduce

import boto3
from flask import current_app, render_template, render_template_string
from requests import codes, get, post


def deep_get(dictionary, keys, default=None):
    return reduce(
        lambda d, key: d.get(key, default) if isinstance(d, dict) else default,
        keys.split("."),
        dictionary,
    )


class ResultHandler(ABC):
    """
    Base class for result handlers.
    This class should be extended to implement specific result handling logic.
    """

    def __init__(self, **kwargs):
        raise NotImplementedError(
            "Subclasses must implement the __init__ dunder method"
        )

    def id(self) -> str:
        return uuid.uuid4().hex

    def process(self, data: dict, **kwargs):
        raise NotImplementedError("Subclasses must implement the process method")

    def send(self, **kwargs) -> bool:
        raise NotImplementedError("Subclasses must implement the send method")

    def result(self) -> dict:
        raise NotImplementedError("Subclasses must implement the result method")


class EmailResultHandler(ResultHandler):
    """
    Handles the result of a form submission by sending an email.
    """

    def __init__(self, **kwargs):
        aws_access_key_id = current_app.config.get("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = current_app.config.get("AWS_SECRET_ACCESS_KEY")
        aws_session_token = current_app.config.get("AWS_SESSION_TOKEN")
        region_name = current_app.config.get("AWS_DEFAULT_REGION")
        if not any([aws_access_key_id, aws_secret_access_key, aws_session_token]):
            raise ValueError("SMTP configuration is not set properly")
        self.client = boto3.client(
            "ses",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=region_name,
        )
        self.data: dict = {}
        self.content: dict = {}
        self.result_data: dict = {}

    def process(self, data: dict, **kwargs):
        print("----------- Processing email content with data:", data)
        self.data = data
        self.data["reference_number"] = self.id()
        print(self.data)
        self.content = {
            "template": kwargs.get("template") or "layouts/email.html",
            "content": render_template_string(kwargs.get("content", ""), **self.data),
            "cta_buttons": kwargs.get("cta_buttons", []),
            "signoff": render_template_string(kwargs.get("signoff", ""), **self.data),
        }
        if "panel" in kwargs:
            self.content["panel"] = {
                "title": kwargs["panel"].get("title", ""),
                "body": render_template_string(
                    kwargs["panel"].get("body", ""), **self.data
                ),
            }

        print(self.content)

    def send(self, **kwargs) -> bool:
        print("==========================EMAIL CONTENT START==========================")
        current_app.logger.debug("Sending email")
        if not self.data or not self.content:
            raise ValueError("Email not processed. Call process() with the data first.")
        content = render_template(self.content["template"], **self.content)
        to_email = kwargs.get("to", "")
        if not to_email:
            if to_email_var := kwargs.get("toVar", ""):
                to_email = deep_get(self.data, to_email_var, "")
        if not to_email:
            raise ValueError("Recipient email address must be provided")
        subject = kwargs.get("subject", "Form Submission")
        from_email = kwargs.get("from", "noreply@nationalarchives.gov.uk")
        try:
            response = self.client.send_email(
                Source=from_email,
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {"Html": {"Charset": "UTF-8", "Data": content}},
                },
            )
            id = response.get("MessageId")
            current_app.logger.debug(f"Email sent with ID {id}")
            self.result_data = {"id": id}
            return True
        except Exception as e:
            current_app.logger.error(f"EmailResultHandler error: {e}")
            return False
        self.result_data = {"id": self.id()}
        print(content)
        print(self.content)
        print(self.data)
        # print(f"Email content: {content[20000:]}")
        return True

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

    def result(self) -> dict:
        return {}


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
