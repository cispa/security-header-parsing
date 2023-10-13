from wptserve.handlers import json_handler
from _hp.tools.models import Response, Session

# For testing only! Later the testrunners know the respids in advance!
@json_handler
def main(request, response):
    label = request.GET["label"]
    with Session() as session:
        try:
            responses = session.query(Response).filter_by(label=label).all()
            return [response.id for response in responses]
        except Exception as e:
            return []