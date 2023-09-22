# These need to be called in this specific order... as there are conflicting functions in both the classes
from wptserve.handlers import handler
from _hp.tools.models import Response, Session, SECRET

def get_response(params):
    with Session() as session:
        uid_header = params['pair']
        header_name = params['test']
        print(uid_header)
        try:
            response = session.query(Response).filter_by(id=uid_header).first()
            print(response.raw_header)
        except Exception as e:
            print(e)
            # TODO how to handle this?
        return response

@handler
def main(request, response):
    params = request.GET
    print(params)
    response = get_response(params)
    header_name = params['test']

    file = open("_hp/common/iframes.html","rb")
    if header_name in ['rp','pp','coop']:
        file = open(f"{header_name}/{header_name}.html","rb")
    elif header_name in ['coep','oac']:
        file = open(f"{header_name}/{header_name}test.html","rb")
    elif header_name=='corp':
        file = open("corp/swag.jpg","rb")
    return response.status_code, response.raw_header, file