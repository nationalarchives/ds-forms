from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import TnaTextareaWidget
from wtforms import TextAreaField
from wtforms.validators import DataRequired


class UsageForm(FlaskForm):
    duration = TextAreaField(
        "How long do you wish to use the information for?",
        validators=[
            DataRequired(
                message="Enter the details of how long you wish to use the information for"
            ),
        ],
        widget=TnaTextareaWidget(),
    )

    dignity = TextAreaField(
        "What steps will you take to maintain the dignity of participants?",
        validators=[
            DataRequired(
                message="Enter the details of what steps you'll take to maintain the dignity of participants"
            ),
        ],
        widget=TnaTextareaWidget(),
    )

    mitigations = TextAreaField(
        "What mitigations will you put in place for third party use?",
        validators=[
            DataRequired(
                message="Enter the details of what mitigations you'll put in place for third party use"
            ),
        ],
        widget=TnaTextareaWidget(),
    )
