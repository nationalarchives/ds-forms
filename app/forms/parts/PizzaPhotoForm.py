from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileSize
from tna_frontend_jinja.wtforms import TnaDroppableFileInputWidget
from wtforms import FileField


class PizzaPhotoForm(FlaskForm):
    photo = FileField(
        "Upload a photo of your favorite pizza (optional)",
        description="Upload a JPEG or PNG file no larger than 5 MB.",
        validators=[
            FileAllowed(
                upload_set=["jpg", "jpeg", "png"],
                message="File type not allowed.",
            ),
            FileSize(
                max_size=5 * 1024 * 1024, message="File size must be less than 5 MB."
            ),
        ],
        widget=TnaDroppableFileInputWidget(),
    )
