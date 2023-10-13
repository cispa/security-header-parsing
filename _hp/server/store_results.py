import json
from wptserve.handlers import json_handler
from _hp.tools.models import Result, Session, SECRET


@json_handler
def main(request, response):
    with Session() as session:
        # TODO: add error handling/sanity checking/...?
        # TODO: do something with the SECRET or remove it everywhere?
        req = json.loads(request.body)
        print(req)
        browser_id = req["browser_id"]
        org_scheme = req["org_scheme"]
        org_host = req["org_host"]


        for test in req["tests"]:
            # print(test)
            outcome_type = str(type(test["outcome"]))  # Not useful if test["outcome"] always is a JSON dict
            outcome_value = test["outcome"]

            test_name = test["name"].split("|")[0]
            test_status = test["status"]
            test_message = test["message"]
            test_stack = test["stack"]

            # TODO: get testcase ID from the test; see models.py for challenges (test needs to know it's own id?)
            # Or ignore testcase ID? every test has a name (e.g., simple_framing_test)
            # Other properties of the test are saved in relation, resp_scheme and resp_host (to differentiate between same-org/cross-org framing and similar)
            testcase_id = 1 
            response_id = test["name"].split("|")[-1]

            resp_scheme = test["resp_scheme"]
            resp_host = test["resp_host"]
            relation = test["relation"]

            res = Result(outcome_type=outcome_type, outcome_value=outcome_value,
                         test_name=test_name, test_status=test_status, test_message=test_message, test_stack=test_stack,
                         browser_id=browser_id, testcase_id=testcase_id, response_id=response_id, status='FINISHED',
                         resp_scheme=resp_scheme, resp_host=resp_host, relation_info=relation,
                         org_host=org_host, org_scheme=org_scheme)
            session.add(res)
            print("\n Stored Successfully \n")
        res = {'Status': 'Success'}
        session.commit()
        return res

