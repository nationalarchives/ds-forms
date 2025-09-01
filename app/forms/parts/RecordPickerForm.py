from app.lib.api import JSONAPIClient
from flask import current_app
from flask_wtf import FlaskForm
from tna_frontend_jinja.wtforms import (
    TnaRadiosWidget,
)
from wtforms import RadioField
from wtforms.validators import DataRequired


class RecordPickerForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        all_data = kwargs.get("all_data", {})
        search_form = kwargs.get("search_form")
        search_key = kwargs.get("search_key")
        search_term = ""
        if all_data and search_form and search_key:
            search_term = all_data.get(search_form, {}).get(search_key, "")
        if search_term:
            api = JSONAPIClient("https://rosetta-staging.k-int.com/rosetta/data")
            api.add_parameter("q", search_term)
            try:
                results = api.get("search").get("data", [])
            except Exception as e:
                current_app.logger.error(f"Error fetching search results: {e}")
            if results:
                self.iaid.choices = []
                for results in results:
                    details = results.get("@template", {}).get("details", {})
                    iaid = details.get("iaid")
                    title = details.get("summaryTitle", "No title")
                    # description = details.get("description", "")
                    if iaid and title:
                        self.iaid.choices.append(
                            (str(iaid), f"<strong>{iaid}</strong><br>{title}")
                        )
            else:
                self.iaid.choices = [("", "No records found")]

    iaid = RadioField(
        "Pick a record",
        description="Select one of the records found by your search.",
        choices=[
            ("", "Please perform a search to see records"),
        ],
        validators=[
            DataRequired(message="Select a record"),
        ],
        widget=TnaRadiosWidget(),
    )
