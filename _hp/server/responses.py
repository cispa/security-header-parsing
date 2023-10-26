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
            print("Header:", response.raw_header, os.getpid(),
                  threading.current_thread().ident)
        except Exception as e:
            print(e)
            # TODO how to handle this?
        return response


@lru_cache(maxsize=None)
def get_body(feature_group, resp):
    print("Body:", feature_group, os.getpid(),
          threading.current_thread().ident)
    
    if feature_group in ['pp']:
        file = open(f"_hp/common/frame-fullscreen-pp.html", "rb")
    elif feature_group in ['coop']:
        file = open("_hp/common/swag.jpg", "rb") # Empty file triggers download in FF
    elif feature_group in ['hsts']:
        return ""  # Empty body
    elif feature_group in ["rp"]:
        file = open("_hp/common/frame-referrer.html", "rb")
    elif feature_group in ['corp']:
        if resp == 1:
            file = open("_hp/common/swag.jpg", "rb")
        else:
            file = open("_hp/common/frame-corp.html", "rb")
    elif feature_group in ["tao"]:
        file = open("_hp/common/swag.jpg", "rb")
    elif feature_group in ["framing"]:
        file = open("_hp/common/iframes.html", "rb")
    elif feature_group in ["oac"]:
        file = open("_hp/common/frame-oac.html", "rb")
    elif feature_group in ["csp-xss"]:
        file = open("_hp/common/frame-script-csp.html", "rb")
    else:
        print(f"Invalid feature_group: {feature_group}")
        return ""
    return file.read()

@handler
def main(request, response):
    params = request.GET
    # print(params)
    # Get the correct response based on resp_id (headers + status code, without body)
    resp = int(params["resp"])
    # Only set the response if resp=1, if resp=0 set a default response with code 200 and no special headers
    if resp == 1:
        response = get_response(params["resp_id"])
    else:
        response.status_code = 200
        response.raw_header = []
    # Get the correct response body based on the current test/feature group
    file = get_body(params['feature_group'], resp=resp)
    return response.status_code, response.raw_header, file
