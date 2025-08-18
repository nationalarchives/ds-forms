from app.lib.validators import UKPostcode
from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import TnaTextInputWidget
from wtforms import StringField
from wtforms.validators import DataRequired


class AddressForm(FlaskForm):
    address_line_1 = StringField(
        "Address line 1",
        validators=[
            DataRequired(
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
            DataRequired(message="Enter town or city"),
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
            DataRequired(message="Enter postcode"),
            UKPostcode(message="Enter a full UK postcode"),
        ],
        widget=TnaTextInputWidget(),
    )
