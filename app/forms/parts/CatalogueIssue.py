from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import (
    TnaEmailInputWidget,
    TnaFieldsetWidget,
    TnaTextareaWidget,
    TnaTextInputWidget,
)
from wtforms import EmailField, FormField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Optional

from app.lib.validators import RecordIAID


class IssueDetailFields(FlaskForm):
    class Meta:
        csrf = False

    error = TextAreaField(
        "What is the issue?",
        validators=[
            DataRequired(message="Enter a description of the issue"),
        ],
        widget=TnaTextareaWidget(),
        render_kw={"headingSize": "xs"},
    )

    expected = TextAreaField(
        "What is the correct information?",
        validators=[
            DataRequired(message="Enter the correct information"),
        ],
        widget=TnaTextareaWidget(),
        render_kw={"headingSize": "xs"},
    )

    additional_information = TextAreaField(
        "Any additional information? (optional)",
        validators=[
            Optional(),
        ],
        widget=TnaTextareaWidget(),
        render_kw={"headingSize": "xs"},
    )


class YourDetailsFields(FlaskForm):
    class Meta:
        csrf = False

    name = StringField(
        "Enter your name (optional)",
        validators=[Optional()],
        widget=TnaTextInputWidget(),
        render_kw={"headingSize": "xs", "autocomplete": "name"},
    )

    email = EmailField(
        "Email address (optional)",
        validators=[
            Optional(),
            Email(
                message="Enter an email address in the correct format, like name@example.com"
            ),
        ],
        widget=TnaEmailInputWidget(),
        render_kw={"headingSize": "xs", "autocomplete": "email"},
    )


class CatalogueIssue(FlaskForm):
    record_iaid = StringField(
        "Record IAID",
        filters=[lambda x: x.strip() if isinstance(x, str) else x],
        validators=[
            DataRequired(message="Enter the record IAID"),
            RecordIAID(message="Record IAID is not valid"),
        ],
        widget=TnaTextInputWidget(),
        render_kw={"headingSize": "l", "autocomplete": "off", "size": "m"},
    )

    issue_details = FormField(
        IssueDetailFields,
        label="Issue details",
        description="Please provide as much detail as possible.",
        widget=TnaFieldsetWidget(),
        render_kw={"headingLevel": 2, "headingSize": "l"},
    )

    reporter = FormField(
        YourDetailsFields,
        label="Your details",
        description="We need this to contact you about the issue.",
        widget=TnaFieldsetWidget(),
        render_kw={"headingLevel": 2, "headingSize": "l"},
    )
