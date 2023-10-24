from wptserve.handlers import handler
from _hp.tools.models import Response, Session, SECRET
from functools import lru_cache
import os
import threading

@lru_cache(maxsize=5000)
def get_response(resp_id):
    with Session() as session:
        try:
            response = session.query(Response).filter_by(id=resp_id).first()
            print("Header:", response.raw_header, os.getpid(), threading.current_thread().ident)
        except Exception as e:
            print(e)
            # TODO how to handle this?
        return response
    
@lru_cache(maxsize=None)
def get_body(feature_group, nest):
    print("Body:", feature_group, os.getpid(), threading.current_thread().ident)
    # Default: iframes.html
    file = open("_hp/common/iframes.html", "rb")
    # Other body for other tests
    if feature_group in ['accessapi']:
        file = open(f"_hp/common/iframe-api.html", "rb")
    if feature_group in ['rp','pp','coop']:
        file = open(f"_hp/common/{feature_group}.html", "rb")
    elif feature_group in ['coep','oac']:
        file = open(f"_hp/common/{feature_group}test.html", "rb")
    elif feature_group=='corp':
        if nest == 0:
            file = open("_hp/common/swag.jpg", "rb")
        else:
            file = open("_hp/common/frame-corp.html", "rb")
    return file.read()

#@handler
def main(request, response):
    params = request.GET
    # print(params)
    # Get the correct response based on resp_id (headers + status code, without body)
    nest = int(params["nest"]) 
    if nest == 0:
        response = get_response(params["resp_id"])
    else:
        response.status_code = 200
        response.raw_header = []
    # Get the correct response body based on the current test/feature group
    file = get_body(params['feature_group'], nest=nest)
    return response.status_code, response.raw_header, file