from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import TnaEmailInputWidget
from wtforms import EmailField
from wtforms.validators import DataRequired, Email


class EmailForm(FlaskForm):
    email_address = EmailField(
        "Email address",
        validators=[
            DataRequired(message="Enter an email address"),
            Email(
                message="Enter an email address in the correct format, like name@example.com"
            ),
        ],
        widget=TnaEmailInputWidget(),
        render_kw={"size": "l", "autocomplete": "email"},
    )
