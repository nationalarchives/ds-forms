from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import (
    TnaEmailInputWidget,
    TnaTelInputWidget,
    TnaTextInputWidget,
)
from wtforms import EmailField, StringField, TelField
from wtforms.validators import DataRequired, Email, Optional, Regexp


class YourDetailsForm(FlaskForm):
    full_name = StringField(
        "Full name",
        validators=[
            DataRequired(message="Enter your full name"),
        ],
        widget=TnaTextInputWidget(),
        render_kw={"autocomplete": "name"},
    )

    email_address = EmailField(
        "Enter your email address",
        validators=[
            DataRequired(message="Enter an email address"),
            Email(message="Enter a valid email address"),
        ],
        widget=TnaEmailInputWidget(),
        render_kw={"autocomplete": "email"},
    )

    organisation = StringField(
        "Company (optional)",
        validators=[
            Optional(),
        ],
        widget=TnaTextInputWidget(),
        render_kw={"autocomplete": "organization"},
    )

    job_title = StringField(
        "Job title (optional)",
        validators=[
            Optional(),
        ],
        widget=TnaTextInputWidget(),
        render_kw={"autocomplete": "organization-title"},
    )

    phone_number = TelField(
        "Phone number (optional)",
        validators=[
            Optional(),
            Regexp(regex="^[0-9 ()-+]{11,}$", message="Enter a valid phone number"),
        ],
        widget=TnaTelInputWidget(),
    )
