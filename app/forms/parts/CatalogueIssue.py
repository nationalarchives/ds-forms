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
        "What is the error?",
        validators=[
            DataRequired(message="Enter a description of the error"),
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


class ReporterDetailsFields(FlaskForm):
    class Meta:
        csrf = False

    name = StringField(
        "Full name (optional)",
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
        description="This is the unique identifier for the record you are reporting an issue with. It can be found in the URL of the record details page.",
        filters=[lambda x: x.strip() if isinstance(x, str) else x],
        validators=[
            DataRequired(message="Enter the record IAID"),
            RecordIAID(message="Enter a valid record IAID"),
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
