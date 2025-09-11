from app.forms.parts.AddressForm import AddressFormFields
from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import (
    TnaEmailInputWidget,
    TnaFieldsetWidget,
    TnaTextInputWidget,
)
from wtforms import EmailField, FormField, StringField
from wtforms.validators import DataRequired, Email


class YourDetailsForm(FlaskForm):
    full_name = StringField(
        "Full name",
        validators=[
            DataRequired(message="Enter your full name"),
        ],
        widget=TnaTextInputWidget(),
        render_kw={"autocomplete": "name"},
    )

    address = FormField(
        AddressFormFields,
        label="Enter your address",
        widget=TnaFieldsetWidget(),
    )

    organisation = StringField(
        "Organisation",
        validators=[
            DataRequired(message="Enter your organisation name"),
        ],
        widget=TnaTextInputWidget(),
        render_kw={"autocomplete": "organization"},
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
