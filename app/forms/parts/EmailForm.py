from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import TnaEmailInputWidget
from wtforms import EmailField
from wtforms.validators import DataRequired, Email


class EmailForm(FlaskForm):
    email_address = EmailField(
        "Enter your email",
        validators=[
            DataRequired(message="Enter an email"),
            Email(message="Enter a valid email"),
        ],
        widget=TnaEmailInputWidget(),
        render_kw={"size": "l", "autocomplete": "email"},
    )
