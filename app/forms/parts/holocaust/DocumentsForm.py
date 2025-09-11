from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import TnaTextareaWidget
from wtforms import TextAreaField
from wtforms.validators import DataRequired


class DocumentsForm(FlaskForm):
    documents = TextAreaField(
        "What documents do you want to use?",
        validators=[
            DataRequired(message="Enter the details of the documents you want to use"),
        ],
        widget=TnaTextareaWidget(),
    )

    reason = TextAreaField(
        "Why do you want to use these documents and how will you use them?",
        validators=[
            DataRequired(
                message="Enter the details of why you want to use them and how"
            ),
        ],
        widget=TnaTextareaWidget(),
    )
