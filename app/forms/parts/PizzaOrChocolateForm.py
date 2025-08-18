from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import TnaRadiosWidget
from wtforms import RadioField
from wtforms.validators import DataRequired


class PizzaOrChocolateForm(FlaskForm):
    food = RadioField(
        "Do you prefer pizza or chocolate?",
        choices=[
            ("pizza", "Pizza"),
            ("chocolate", "Chocolate"),
            ("neither", "I don't like either"),
            ("cats", "Take me to see cats!"),
        ],
        validators=[
            DataRequired(message="Select your favourite food"),
        ],
        widget=TnaRadiosWidget(),
    )
