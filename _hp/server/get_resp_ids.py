from wptserve.handlers import json_handler
from _hp.tools.models import Response, Session
from functools import lru_cache

@lru_cache(maxsize=None)
def get_resp_ids(label):
    with Session() as session:
        try:
            responses = session.query(Response).filter_by(label=label).all()
            return [response.id for response in responses]
        except Exception as e:
            print(e)
            return []

# For testing only! Later the testrunners know the respids in advance!
@json_handler
def main(request, response):
    label = request.GET["label"]
    return get_resp_ids(label)