import grapheme
from wtforms import ValidationError


class Characters:
    """
    Counts the number of logical characters in a string.

    :param message:
        Error message to raise in case of a validation error.
    """

    def __init__(self, min=-1, max=-1, message=None):
        assert min != -1 or max != -1, (
            "At least one of `min` or `max` must be specified."
        )
        assert max == -1 or min <= max, "`min` cannot be more than `max`."
        self.min = min
        self.max = max
        self.message = message

    def __call__(self, form, field):
        data = field.data or ""
        length = grapheme.length(data) or 0

        if length < self.min or self.max != -1 and length > self.max:
            message = self.message
            if message is None:
                if self.max == -1:
                    message = field.ngettext(
                        "Field must be at least {min:,} character long.",
                        "Field must be at least {min:,} characters long.",
                        self.min,
                    )
                elif self.min == -1:
                    message = field.ngettext(
                        "Field cannot be longer than {max:,} character.",
                        "Field cannot be longer than {max:,} characters.",
                        self.max,
                    )
                elif self.min == self.max:
                    message = field.ngettext(
                        "Field must be exactly {max:,} character long.",
                        "Field must be exactly {max:,} characters long.",
                        self.max,
                    )
                else:
                    message = field.gettext(
                        "Field must be between {min:,} and {max:,} characters long."
                    )

            raise ValidationError(
                message.format_map({"min": self.min, "max": self.max, "length": length})
            )
