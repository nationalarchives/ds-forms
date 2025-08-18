from app.lib.validators import UKPostcode
from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import TnaTextInputWidget
from wtforms import StringField
from wtforms.validators import InputRequired


class AddressForm(FlaskForm):
    address_line_1 = StringField(
        "Address line 1",
        validators=[
            InputRequired(
                message="Enter address line 1, typically the building and street"
            ),
        ],
        widget=TnaTextInputWidget(),
    )

    address_line_2 = StringField(
        "Address line 2 (optional)",
        widget=TnaTextInputWidget(),
    )

    town_city = StringField(
        "Town or city",
        validators=[
            InputRequired(message="Enter town or city"),
        ],
        widget=TnaTextInputWidget(),
    )

    county = StringField(
        "County (optional)",
        widget=TnaTextInputWidget(),
    )

    postcode = StringField(
        "Postcode",
        validators=[
            InputRequired(message="Enter postcode"),
            UKPostcode(message="Enter a full UK postcode"),
        ],
        widget=TnaTextInputWidget(),
    )
