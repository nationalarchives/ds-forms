from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import (
    TnaEmailInputWidget,
    TnaFieldsetWidget,
    TnaTextareaWidget,
    TnaTextInputWidget,
)
from wtforms import EmailField, FormField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional

from app.lib.validators import RecordIAID


class IssueDetailFields(FlaskForm):
    class Meta:
        csrf = False

    error = TextAreaField(
        "What is the error?",
        validators=[
            DataRequired(message="Enter a description of the error"),
            Length(
                max=1000,
                message="Error description must be %(max)d characters or fewer",
            ),
        ],
        widget=TnaTextareaWidget(),
        render_kw={"headingSize": "xs", "characterCount": {"max": 1000}},
    )

    expected = TextAreaField(
        "What is the correct information?",
        validators=[
            DataRequired(message="Enter the correct information"),
            Length(
                max=1000,
                message="Correct information must be %(max)d characters or fewer",
            ),
        ],
        widget=TnaTextareaWidget(),
        render_kw={"headingSize": "xs", "characterCount": {"max": 1000}},
    )

    additional_information = TextAreaField(
        "Any additional information? (optional)",
        validators=[
            Optional(),
            Length(
                max=1000,
                message="Additional information must be %(max)d characters or fewer",
            ),
        ],
        widget=TnaTextareaWidget(),
        render_kw={"headingSize": "xs", "characterCount": {"max": 1000}},
    )


class ReporterDetailsFields(FlaskForm):
    class Meta:
        csrf = False

    name = StringField(
        "Full name (optional)",
        validators=[
            Optional(),
            Length(max=1000, message="Name must be %(max)d characters or fewer"),
        ],
        widget=TnaTextInputWidget(),
        render_kw={"headingSize": "xs", "autocomplete": "name"},
    )

    email = EmailField(
        "Email address (optional)",
        validators=[
            Optional(),
            Length(max=1000, message="Email must be %(max)d characters or fewer"),
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
        description="This is the unique identifier for the record you are reporting an issue with. It can be found in the URL of the record details page.",
        filters=[lambda x: x.strip() if isinstance(x, str) else x],
        validators=[
            DataRequired(message="Enter the record IAID"),
            RecordIAID(message="Enter a valid record IAID"),
            Length(max=100, message="Record IAID must be %(max)d characters or fewer"),
        ],
        widget=TnaTextInputWidget(),
        render_kw={"headingSize": "l", "autocomplete": "off", "size": "m"},
    )

    error_details = FormField(
        IssueDetailFields,
        label="Error details",
        description="Please provide as much information as possible.",
        widget=TnaFieldsetWidget(),
        render_kw={"headingLevel": 2, "headingSize": "l"},
    )

    reporter = FormField(
        ReporterDetailsFields,
        label="Contact information",
        description="We may contact you if we need more information.",
        widget=TnaFieldsetWidget(),
        render_kw={"headingLevel": 2, "headingSize": "l"},
    )
