import re

from flask import current_app

from app.forms.result_handlers import deep_get
from app.lib.records_api import record_details


def report_catalogue_issue_email(data: dict) -> str:
    """
    Function to determine the recipient email address for reporting a catalogue issue.
    This function can be used in the 'toFunction' field of the email result handler configuration.
    """

    iaid = deep_get(data, "info.record_iaid", "")
    if not iaid:
        raise ValueError("IAID not found in the provided data.")

    details = record_details(iaid)
    if not details:
        raise ValueError(f"No record details found for IAID: {iaid}")

    is_parliamentary_archive_record = False
    guid_regex = r"^(?:\\{{0,1}(?:[0-9a-fA-F]){8}-(?:[0-9a-fA-F]){4}-(?:[0-9a-fA-F]){4}-(?:[0-9a-fA-F]){4}-(?:[0-9a-fA-F]){12}\\}{0,1})$"

    emails = current_app.config.get("FORM_REPORT_A_CATALOGUE_ISSUE_INBOXES", {})

    default_email = current_app.config["DEFAULT_INBOX"]

    email = emails.get("DIGITAL_DOWNLOADS", default_email)
    if re.match(guid_regex, iaid) and not is_parliamentary_archive_record:
        if "-" in iaid:
            email = emails.get("FINDING_ARCHIVES_PROJECT", default_email)
        else:
            email = emails.get("DIGITAL_PRESERVATION", default_email)
    elif iaid.startswith("C") or is_parliamentary_archive_record:
        email = emails.get("CATALOGUE_AMENDMENTS", default_email)
    elif iaid.startswith("N"):
        email = emails.get("FINDING_ARCHIVES_PROJECT", default_email)

    return email
