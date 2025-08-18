from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import TnaRadiosWidget
from wtforms import RadioField
from wtforms.validators import DataRequired


class PizzaToppingsForm(FlaskForm):
    topping = RadioField(
        "What pizza topping is best?",
        choices=[
            ("plain", "Plain cheese"),
            ("pepperoni", "Pepperoni"),
            ("vegetarian", "Vegetarian"),
            ("hawaiian", "Hawaiian"),
            ("meat_lovers", "Meat Lovers"),
            ("bbq_chicken", "BBQ Chicken"),
            ("other", "Other"),
        ],
        validators=[
            DataRequired(message="Select your favourite pizza topping"),
        ],
        widget=TnaRadiosWidget(),
    )
