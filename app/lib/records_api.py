from flask import current_app
from tna_utilities.api import SimpleJsonApiClient

from app.lib.cache import cache


class RosettaUrlNotSetError(Exception):
    def __init__(self, message="ROSETTA_API_URL not set"):
        super().__init__(message)


def is_iaid_valid(iaid):
    """
    Check if the requested IAID is valid.
    """

    try:
        data = record_details(iaid)
    except:  # noqa: E722
        current_app.logger.warning(f"IAID {iaid} is not valid")
        return False
    return bool(data)


def record_details(iaid):
    """
    Get the details of a record by IAID.
    """

    iaid = iaid.strip()
    cache_key = f"record_details_{iaid}"

    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    api_url = current_app.config["ROSETTA_API_URL"]
    if not api_url:
        current_app.logger.critical("ROSETTA_API_URL not set")
        raise RosettaUrlNotSetError
    client = SimpleJsonApiClient(api_url, default_headers={})

    data = client.get("get", {"id": iaid})
    data_list = data.get("data", [{}])
    if len(data_list) > 0:
        data_to_return = (data_list[0] or {}).get("@template", {}).get("details", {})
        if data_to_return:
            cache.set(cache_key, data_to_return)
        return data_to_return

    return {}
