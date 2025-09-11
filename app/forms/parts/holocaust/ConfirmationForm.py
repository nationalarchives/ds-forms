from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import TnaCheckboxWidget
from wtforms import BooleanField
from wtforms.validators import DataRequired


class ConfirmationForm(FlaskForm):
    confirm = BooleanField(
        "I confirm that the details I have provided are correct",
        validators=[
            DataRequired(
                message="Confirm that the details you have provided are correct"
            ),
        ],
        widget=TnaCheckboxWidget(),
    )
