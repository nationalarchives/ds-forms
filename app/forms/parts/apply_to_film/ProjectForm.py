from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import (
    TnaCheckboxWidget,
    TnaDateField,
    TnaRadiosWidget,
    TnaTextareaWidget,
)
from tna_frontend_jinja.wtforms import validators as tna_frontend_validators
from wtforms import BooleanField, RadioField, TextAreaField
from wtforms.validators import DataRequired, Optional


class ProjectForm(FlaskForm):
    date = TnaDateField(
        "Preferred date of filming",
        description="Enter date in the format DD MM YYYY",
        validators=[
            DataRequired(message="Enter your preferred date of filming"),
            tna_frontend_validators.FutureDate(
                message="Filming date of must be in the future"
            ),
        ],
    )

    time = RadioField(
        "Preferred time of filming (optional)",
        choices=[
            ("morning", "Morning (9am to 11am)"),
            ("midday", "Midday (11am to 1pm)"),
            ("afternoon", "Afternoon (1pm to 3pm)"),
            ("evening", "Late afternoon/evening (3pm to 5pm)"),
        ],
        validators=[
            Optional(),
        ],
        widget=TnaRadiosWidget(),
        render_kw={"headingSize": "s"},
    )

    broadcast = TextAreaField(
        "How will it be broadcast and when will it be transmitted? Is it part of a series? (optional)",
        validators=[
            Optional(),
        ],
        widget=TnaTextareaWidget(),
    )

    documents = TextAreaField(
        "List the documents you would like to film, providing full references (optional)",
        validators=[
            Optional(),
        ],
        widget=TnaTextareaWidget(),
    )

    interview = TextAreaField(
        "Enter the names of the staff member you want to interview (optional)",
        validators=[
            Optional(),
        ],
        widget=TnaTextareaWidget(),
    )

    terms_and_conditions = BooleanField(
        "Terms and conditions",
        description="I have read and agreed to the filming terms and conditions, including the charges and cancellation policy",
        validators=[
            DataRequired("You must agree to the terms and conditions"),
        ],
        widget=TnaCheckboxWidget(),
    )
