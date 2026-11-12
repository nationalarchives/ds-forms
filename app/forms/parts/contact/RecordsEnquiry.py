from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import (
    TnaEmailInputWidget,
    TnaFieldsetWidget,
    TnaSelectWidget,
    TnaTextareaWidget,
    TnaTextInputWidget,
)
from wtforms import (
    EmailField,
    FormField,
    SelectChoice,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, Optional

from app.forms.validators.Characters import Characters
from app.lib.constants import COUNTRIES


class NameFields(FlaskForm):
    class Meta:
        csrf = False

    first_name = StringField(
        "First name",
        validators=[
            DataRequired(message="Enter your first name"),
            Length(max=1000, message="First name must be %(max)d characters or fewer"),
        ],
        widget=TnaTextInputWidget(),
        render_kw={"headingSize": "xs", "autocomplete": "given-name"},
    )

    surname = StringField(
        "Surname",
        validators=[
            DataRequired(message="Enter your surname"),
            Length(max=1000, message="Surname must be %(max)d characters or fewer"),
        ],
        widget=TnaTextInputWidget(),
        render_kw={"headingSize": "xs", "autocomplete": "family-name"},
    )


class RecordsEnquiry(FlaskForm):
    name = FormField(
        NameFields,
        label="Full name",
        widget=TnaFieldsetWidget(),
        render_kw={"headingSize": "m"},
    )

    email = EmailField(
        "Email address",
        validators=[
            DataRequired(message="Enter your email address"),
            Length(max=1000, message="Email must be %(max)d characters or fewer"),
            Email(
                message="Enter an email address in the correct format, like name@example.com"
            ),
        ],
        widget=TnaEmailInputWidget(),
        render_kw={"autocomplete": "email", "size": "l"},
    )

    country = SelectField(
        "Country (optional)",
        choices=[
            SelectChoice("", "Select country"),
            SelectChoice("GB", "United Kingdom"),
        ]
        + [SelectChoice(code, name) for code, name in COUNTRIES if code != "GB"],
        validators=[
            Optional(),
            DataRequired(message="Enter your country"),
        ],
        widget=TnaSelectWidget(),
        render_kw={"autocomplete": "country-name", "size": "m"},
    )

    enquiry = TextAreaField(
        "Your enquiry",
        description="Please provide specific details of the information you are looking for, including any relevant catalogue references.",
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
        render_kw={"characterCount": {"max": 1000, "countType": "characters"}},
    )
