from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import (
    TnaEmailInputWidget,
    TnaFieldsetWidget,
    TnaTextInputWidget,
)
from wtforms import EmailField, FormField, StringField
from wtforms.validators import DataRequired, Email

from app.forms.parts.AddressForm import AddressFormFields


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
        "Email address",
        validators=[
            DataRequired(message="Enter an email address"),
            Email(
                message="Enter an email address in the correct format, like name@example.com"
            ),
        ],
        widget=TnaEmailInputWidget(),
        render_kw={"size": "l", "autocomplete": "email"},
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
