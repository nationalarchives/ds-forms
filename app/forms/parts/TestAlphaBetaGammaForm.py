from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import TnaRadiosWidget
from wtforms import RadioField
from wtforms.validators import DataRequired


class TestAlphaBetaGammaForm(FlaskForm):
    option = RadioField(
        "Select an option",
        choices=[
            ("a", "Alpha"),
            ("b", "Beta"),
            ("g", "Gamma"),
        ],
        validators=[
            DataRequired(message="Select an option"),
        ],
        widget=TnaRadiosWidget(),
    )
