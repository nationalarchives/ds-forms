from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import TnaRadiosWidget
from wtforms import RadioField
from wtforms.validators import DataRequired


class TypeOfChocolateForm(FlaskForm):
    chocolate_preference = RadioField(
        "Which type of chocolate do you prefer?",
        description="Select your favourite type of chocolate",
        choices=[
            ("dark", "Dark Chocolate"),
            ("milk", "Milk Chocolate"),
            ("white", "White Chocolate"),
        ],
        validators=[
            DataRequired(message="Select your favourite type of chocolate"),
        ],
        widget=TnaRadiosWidget(),
    )
