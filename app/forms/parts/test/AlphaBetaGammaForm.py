from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import TnaRadiosWidget
from wtforms import RadioField, SelectChoice
from wtforms.validators import DataRequired


class AlphaBetaGammaForm(FlaskForm):
    option = RadioField(
        "Select an option",
        choices=[
            SelectChoice("a", "Alpha"),
            SelectChoice("b", "Beta"),
            SelectChoice("g", "Gamma"),
        ],
        validators=[
            DataRequired(message="Select an option"),
        ],
        widget=TnaRadiosWidget(),
    )
