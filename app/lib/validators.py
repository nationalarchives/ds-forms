import re

from wtforms import ValidationError

from app.lib.records_api import is_iaid_valid


class UKPostcode:
    """
    Validates a postcode in the UK format.

    :param message:
        Error message to raise in case of a validation error.
    """

    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        message = self.message
        if message is None:
            message = field.gettext("Date must be in the future")
        try:
            if not field.data:
                raise ValidationError(message)
            postcode = field.data.strip().replace(" ", "")
            if not re.match(
                r"^([Gg][Ii][Rr] 0[Aa]{2})|((([A-Za-z][0-9]{1,2})|(([A-Za-z][A-Ha-hJ-Yj-y][0-9]{1,2})|(([A-Za-z][0-9][A-Za-z])|([A-Za-z][A-Ha-hJ-Yj-y][0-9]?[A-Za-z])))) ?[0-9][A-Za-z]{2})$",
                postcode,
            ):
                raise ValueError(message)
        except ValueError as exc:
            raise ValidationError(message) from exc


class RecordIAID:
    """
    Validates a record IAID by checking if it exists in the records API.

    :param message:
        Error message to raise in case of a validation error.
    """

    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        message = self.message
        if message is None:
            message = field.gettext("Record IAID is not valid")
        try:
            if not field.data:
                raise ValidationError(message)
            iaid = field.data.strip()
            if not is_iaid_valid(iaid):
                print(f"Record IAID is not valid: {iaid}")
                raise ValueError(message)
        except ValueError as exc:
            raise ValidationError(message) from exc

        print(f"Record IAID is valid: {iaid}")
