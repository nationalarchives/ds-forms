from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import (
    TnaCheckboxWidget,
    TnaEmailInputWidget,
    TnaTelInputWidget,
    TnaTextareaWidget,
    TnaTextInputWidget,
)
from wtforms import BooleanField, EmailField, StringField, TelField, TextAreaField
from wtforms.validators import DataRequired, Email, Optional, Regexp


class DiscoveryApiKeyForm(FlaskForm):
    full_name = StringField(
        "Full name",
        validators=[
            DataRequired(message="Enter your full name"),
        ],
        widget=TnaTextInputWidget(),
        render_kw={"autocomplete": "name"},
    )

    email_address = EmailField(
        "Enter your email",
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

    phone_number = TelField(
        "Phone number (optional)",
        validators=[
            Optional(),
            Regexp(regex="^[0-9 ()-+]{11,}$", message="Enter a valid phone number"),
        ],
        widget=TnaTelInputWidget(),
        render_kw={"autocomplete": "tel"},
    )

    intention = TextAreaField(
        "How do you plan to use the Discovery API?",
        validators=[
            DataRequired(message="Enter your intention for using the Discovery API"),
        ],
        widget=TnaTextareaWidget(),
    )
    user_research = BooleanField(
        "User research",
        description="I am happy for The National Archives to contact me for research purposes",
        validators=[
            Optional(),
        ],
        widget=TnaCheckboxWidget(),
    )
