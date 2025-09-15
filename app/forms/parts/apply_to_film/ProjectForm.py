from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import (
    TnaCheckboxWidget,
    TnaDateField,
    TnaFieldsetWidget,
    TnaTextareaWidget,
    TnaTextInputWidget,
)
from tna_frontend_jinja.wtforms import validators as tna_frontend_validators
from wtforms import BooleanField, FormField, StringField, TextAreaField, TimeField
from wtforms.validators import DataRequired, Optional


class InterviewStaffForm(FlaskForm):
    interview = BooleanField(
        "I want to interview a member of staff",
        validators=[
            Optional(),
        ],
        widget=TnaCheckboxWidget(),
        render_kw={"headingSize": "s"},
    )

    interview_staff = StringField(
        "Enter the name of the staff member you want to interview (optional)",
        validators=[
            Optional(),
        ],
        widget=TnaTextInputWidget(),
        render_kw={"headingSize": "s"},
    )


class ProjectForm(FlaskForm):
    date = TnaDateField(
        "Preferred date of filming",
        description="Enter date in the format DD MM YYYY",
        validators=[
            DataRequired(message="Enter your preferred date of filming"),
            tna_frontend_validators.FutureDate(
                message="Date of birth must be in the future"
            ),
        ],
    )

    time = TimeField(
        "Preferred time of filming (optional)",
        validators=[
            Optional(),
        ],
        # widget=TnaTextInputWidget(),
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

    interview = FormField(
        InterviewStaffForm,
        label="Interviews",
        widget=TnaFieldsetWidget(),
    )

    terms_and_conditions = BooleanField(
        "I have read and agreed to the filming terms and conditions, including the charges and cancellation policy",
        validators=[
            DataRequired("You must agree to the terms and conditions"),
        ],
        widget=TnaCheckboxWidget(),
        render_kw={"label": "Terms and conditions"},
    )
