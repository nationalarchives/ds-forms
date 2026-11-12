from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import (
    TnaEmailInputWidget,
    TnaFieldsetWidget,
    TnaRadiosWidget,
    TnaTextareaWidget,
    TnaTextInputWidget,
)
from wtforms import (
    EmailField,
    FormField,
    RadioField,
    SelectChoice,
    StringField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, Optional

from app.forms.validators.Characters import Characters


class YourDetailsFields(FlaskForm):
    class Meta:
        csrf = False

    name = StringField(
        "Full name (optional)",
        validators=[
            Optional(),
            Length(max=1000, message="Full name must be %(max)d characters or fewer"),
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


class YourViews(FlaskForm):
    details = FormField(
        YourDetailsFields,
        label="Your details",
        widget=TnaFieldsetWidget(),
        render_kw={"headingSize": "m"},
    )

    reason = RadioField(
        "Reason for contact",
        choices=[
            SelectChoice("compliment", "Compliment"),
            SelectChoice("records", "Suggestion or comment"),
            SelectChoice("criticism", "Criticism or concern"),
            SelectChoice("complaint", "Complaint"),
        ],
        invalid_choice_message="Select a reason for contact",
        validators=[
            DataRequired(message="Select a reason for contact"),
        ],
        widget=TnaRadiosWidget(),
        render_kw={"headingSize": "m"},
    )

    enquiry = TextAreaField(
        "Your enquiry",
        validators=[
            DataRequired(message="Enter details of your enquiry"),
            # Limit the enquiry to a maximum of 1000 logical characters
            Characters(max=1000, message="Enquiry must be {max:,} characters or fewer"),
            # Limit the enquiry to a maximum of 100000 raw characters to account for multi-byte characters
            Length(
                max=100000,
                message="Enquiry must be %(max)d characters or fewer, including emojis and non-Latin characters",
            ),
        ],
        widget=TnaTextareaWidget(),
        render_kw={
            "headingSize": "m",
            "characterCount": {"max": 1000, "countType": "characters"},
        },
    )

    additional = StringField(
        "Order number or catalogue reference (optional)",
        validators=[
            Optional(),
            Length(
                max=100,
                message="Order number or catalogue reference must be %(max)d characters or fewer",
            ),
        ],
        widget=TnaTextInputWidget(),
        render_kw={"headingSize": "m", "size": "m"},
    )
