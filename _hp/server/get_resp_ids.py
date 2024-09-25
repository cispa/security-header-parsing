from wptserve.handlers import json_handler
from hp.tools.models import Response, Session
from functools import lru_cache

@lru_cache(maxsize=None)
def get_resp_ids(label, resp_type):
    with Session() as session:
        try:
            responses = session.query(Response).filter_by(label=label, resp_type=resp_type).all()
            return [response.id for response in responses]
        except Exception as e:
            print(e)
            return []

# For testing only! Later the testrunners know the respids in advance!
@json_handler
def main(request, response):
    label = request.GET["label"]
    mode = request.GET["resp_type"]
    return get_resp_ids(label, mode)