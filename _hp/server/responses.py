# These need to be called in this specific order... as there are conflicting functions in both the classes
from wptserve.handlers import handler
from _hp.tools.models import Response, Session, SECRET

def get_response(resp_id):
    with Session() as session:
        try:
            response = session.query(Response).filter_by(id=resp_id).first()
            print(response.raw_header)
        except Exception as e:
            print(e)
            # TODO how to handle this?
        return response

@handler
def main(request, response):
    params = request.GET
    print(params)
    response = get_response(params["resp_id"])
    # Which response content to load?
    feature_group = params['feature_group']

    file = open("_hp/common/iframes.html","rb")
    if feature_group in ['rp','pp','coop']:
        file = open(f"{feature_group}/{feature_group}.html","rb")
    elif feature_group in ['coep','oac']:
        file = open(f"{feature_group}/{feature_group}test.html","rb")
    elif feature_group=='corp':
        file = open("corp/swag.jpg","rb")
    return response.status_code, response.raw_header, file