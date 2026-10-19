from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import (
    TnaEmailInputWidget,
    TnaFieldsetWidget,
    TnaTextareaWidget,
    TnaTextInputWidget,
)
from wtforms import EmailField, FormField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Optional


class NameFields(FlaskForm):
    class Meta:
        csrf = False

    first_name = StringField(
        "First name",
        validators=[DataRequired(message="Enter your first name")],
        widget=TnaTextInputWidget(),
        render_kw={"headingSize": "xs", "autocomplete": "given-name"},
    )

    surname = StringField(
        "Surname",
        validators=[DataRequired(message="Enter your surname")],
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
            Email(
                message="Enter an email address in the correct format, like name@example.com"
            ),
        ],
        widget=TnaEmailInputWidget(),
        render_kw={"autocomplete": "email", "size": "l"},
    )

    country = StringField(
        "Country (optional)",
        validators=[Optional(), DataRequired(message="Enter your country")],
        widget=TnaTextInputWidget(),
        render_kw={"autocomplete": "country-name", "size": "m"},
    )

    enquiry = TextAreaField(
        "Enter your enquiry",
        description="Please provide specific details of the information you are looking for, including any relevant catalogue references.",
        validators=[
            DataRequired(message="Enter details of your enquiry"),
        ],
        widget=TnaTextareaWidget(),
    )
