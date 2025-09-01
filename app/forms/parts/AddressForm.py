from app.lib.validators import UKPostcode
from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import TnaFieldsetWidget, TnaTextInputWidget
from wtforms import FormField, StringField
from wtforms.validators import DataRequired


class AddressFormFields(FlaskForm):
    address_line_1 = StringField(
        "Address line 1",
        description="Typically the building and street",
        validators=[
            DataRequired(
                message="Enter address line 1, typically the building and street"
            ),
        ],
        widget=TnaTextInputWidget(),
        render_kw={"headingSize": "xs", "autocomplete": "address-line1"},
    )

    address_line_2 = StringField(
        "Address line 2 (optional)",
        widget=TnaTextInputWidget(),
        render_kw={"headingSize": "xs", "autocomplete": "address-line2"},
    )

    town_city = StringField(
        "Town or city",
        validators=[
            DataRequired(message="Enter town or city"),
        ],
        widget=TnaTextInputWidget(),
        render_kw={"headingSize": "xs", "size": "m", "autocomplete": "address-level2"},
    )

    county = StringField(
        "County (optional)",
        widget=TnaTextInputWidget(),
        render_kw={"headingSize": "xs", "size": "m", "autocomplete": "address-level1"},
    )

    postcode = StringField(
        "Postcode",
        validators=[
            DataRequired(message="Enter postcode"),
            UKPostcode(message="Enter a full UK postcode"),
        ],
        widget=TnaTextInputWidget(),
        render_kw={"headingSize": "xs", "size": "s", "autocomplete": "postal-code"},
    )


class AddressForm(FlaskForm):
    field = FormField(
        AddressFormFields,
        label="Enter your address",
        description="We need this to deliver your pizza or chocolate.",
        widget=TnaFieldsetWidget(),
    )
