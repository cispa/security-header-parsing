import json
from wptserve.handlers import json_handler
from hp.tools.models import Result, Session


@json_handler
def main(request, response):
    """Store tests result in the database

    Args:
        request: POST request with JSON body containing test results
        response: Response to generate

    Returns:
        response: JSON response which is either {'Status': 'Success'} or {'Error': str(e)}
    """
    with Session() as session:
        try:
            req = json.loads(request.body)
            browser_id = req["browser_id"]
            org_scheme = req["org_scheme"]
            org_host = req["org_host"]
            full_url = req["full_url"]

            for test in req["tests"]:
                outcome_type = str(type(test["outcome"]))
                outcome_value = test["outcome"]

                test_name = test["name"].split("|")[0]
                test_status = test["status"]
                test_message = test["message"]
                test_stack = test["stack"]

                testcase_id = 1  # Always 1; test are identified by name, relation, resp_scheme and resp_host, ...
                response_id = test["name"].split("|")[-1]

                resp_scheme = test["resp_scheme"]
                resp_host = test["resp_host"]
                relation = test["relation"]

                res = Result(outcome_type=outcome_type, outcome_value=outcome_value,
                            test_name=test_name, test_status=test_status, test_message=test_message, test_stack=test_stack,
                            browser_id=browser_id, testcase_id=testcase_id, response_id=response_id, status='FINISHED',
                            resp_scheme=resp_scheme, resp_host=resp_host, relation_info=relation,
                            org_host=org_host, org_scheme=org_scheme, full_url=full_url)
                session.add(res)
            res = {'Status': 'Success'}
            session.commit()
            return res
        except Exception as e:
            print(e)
            return {'Error': str(e)}

