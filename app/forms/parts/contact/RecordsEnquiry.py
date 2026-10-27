from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import (
    TnaEmailInputWidget,
    TnaFieldsetWidget,
    TnaTextareaWidget,
    TnaTextInputWidget,
)
from wtforms import EmailField, FormField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional

from app.forms.validators.Characters import Characters


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

    country = StringField(
        "Country (optional)",
        validators=[
            Optional(),
            DataRequired(message="Enter your country"),
            Length(max=1000, message="Country must be %(max)d characters or fewer"),
        ],
        widget=TnaTextInputWidget(),
        render_kw={"autocomplete": "country-name", "size": "m"},
    )

    enquiry = TextAreaField(
        "Enter your enquiry",
        description="Please provide specific details of the information you are looking for, including any relevant catalogue references.",
        validators=[
            DataRequired(message="Enter details of your enquiry"),
            Characters(max=1000, message="Enquiry must be {max:,} characters or fewer"),
        ],
        widget=TnaTextareaWidget(),
        render_kw={"characterCount": {"max": 1000, "threshold": 90}},
    )
