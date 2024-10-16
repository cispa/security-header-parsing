from typing import List
from wptserve.handlers import json_handler
from hp.tools.models import Response, Session
from functools import lru_cache

@lru_cache(maxsize=None)
def get_resp_ids(label: str, resp_type: str) -> List[int]:
    """Get all responses associated to a given response_type and label.
    Caches all results until restart of the server.

    Args:
        label (str): Label fo responses e.g., "COEP", "XFO"
        resp_type (str): Type of responses "debug", "basic", or "parsing"

    Returns:
        List[int]: All responses associated to the label and resp_type, or an empty list if there was an error
    """
    with Session() as session:
        try:
            responses = session.query(Response).filter_by(label=label, resp_type=resp_type).all()
            return [response.id for response in responses]
        except Exception as e:
            print(e)
            return []

@json_handler
def main(request, response):
    """Return all tests for a given label and resp_type

    Args:
        request: GET request containing label and resp_type
        response: response to be generated

    Returns:
        JSON: Containing the list of test IDs for the given lable and resp_type
    """
    label = request.GET["label"]
    mode = request.GET["resp_type"]
    return get_resp_ids(label, mode)
