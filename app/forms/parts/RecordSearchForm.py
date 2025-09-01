from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import (
    TnaTextInputWidget,
)
from wtforms import StringField
from wtforms.validators import DataRequired


class RecordSearchForm(FlaskForm):
    search = StringField(
        "Search for a record",
        description="Enter a search term to find records.",
        validators=[
            DataRequired(message="Enter a search term"),
        ],
        widget=TnaTextInputWidget(),
    )
