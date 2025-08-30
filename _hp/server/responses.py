import json
from wptserve.handlers import handler
from hp.tools.models import Response, Session
from functools import lru_cache
import os
import threading

try:
	wpt_config = json.load(open("/app/_hp/wpt-config.json"))
except OSError:
	try:
		wpt_config = json.load(open("../../wpt-config.json"))
	except OSError:
		wpt_config = json.load(open("../../../wpt-config.json"))

base_host = wpt_config["browser_host"]

@lru_cache(maxsize=500000)
def get_response(resp_id):
    """Load the response entry from the database

    Args:
        resp_id (int): ID of the response in the database

    Returns:
        Response: Response object belonging to the ID
    """
    with Session() as session:
        try:
            response = session.query(Response).filter_by(id=resp_id).first()
            response.raw_header = json.loads(response.raw_header.decode("utf-8"))
            print("Header:", response.raw_header, os.getpid(),
                  threading.current_thread().ident)
        except Exception as e:
            print(e)
        return response


@lru_cache(maxsize=None)
def get_body(feature_group, resp):
    """Load the body for a given feature_group and resp

    Args:
        feature_group (str): Name of the feature of which to load the
        resp (int): Only relevant for feature_group='corp', returns an image if 1 otherwise returns another frame

    Returns:
        bytes: Body as bytes
    """
    print("Body:", feature_group, os.getpid(),
          threading.current_thread().ident)

    if feature_group in ['pp']:
        file = open(f"/app/_hp/common/frame-fullscreen-pp.html", "rb")
    elif feature_group in ['coop']:
        file = open("/app/_hp/common/swag.jpg", "rb") # Empty file triggers download in FF
    elif feature_group in ['hsts', "cors"]:
        return ""  # Empty body
    elif feature_group in ["rp"]:
        file = open("/app/_hp/common/frame-referrer.html", "rb")
    elif feature_group in ['corp']:
        if resp == 1:
            file = open("/app/_hp/common/swag.jpg", "rb")
        else:
            file = open("/app/_hp/common/frame-corp.html", "rb")
    elif feature_group in ["tao"]:
        file = open("/app/_hp/common/swag.jpg", "rb")
    elif feature_group in ["framing"]:
        file = open("/app/_hp/common/iframes.html", "rb")
    elif feature_group in ["csp-script"]:
        file = open("/app/_hp/common/frame-script-csp.html", "rb")
        content = file.read()
        file.close()
        # decode -> replace -> encode back to bytes
        content = content.decode("utf-8").replace("{base_host}", base_host).encode("utf-8")
        return content
    elif feature_group in ["csp-img"]:
        file = open("/app/_hp/common/frame-img-csp.html", "rb")
    elif feature_group in ["coep"]:
        file = open("/app/_hp/common/frame-coep.html", "rb")
    elif feature_group in ["xcto"]:
        file = open("/app/_hp/common/script-xcto.js", "rb")
    else:
        print(f"Invalid feature_group: {feature_group}")
        return ""
    return file.read()

@handler
def main(request, response):
    """Generate the correct response for the given parameters

    Args:
        request: GET request with resp_id, count, and resp as parameters
        response: Response to generate

    Returns:
        response: HTTP response with correct headers and body
    """
    params = request.GET
    resp = int(params["resp"])
    # Only set the response if resp=1, if resp=0 set a default response with code 200 and no special headers
    if resp == 1:
        # Get the correct response based on resp_id (headers + status code, without body)
        response = get_response(params["resp_id"])
    else:
        response.status_code = 200
        response.raw_header = []
    # Get the correct response body based on the current test/feature group
    file = get_body(params['feature_group'], resp=resp)
    # Dynamically replace some information for xcto
    if params['feature_group'] == "xcto":
        file = file.replace(b"<replace-id>", bytes(params['count'], encoding="utf-8"))
    return response.status_code, response.raw_header, file
