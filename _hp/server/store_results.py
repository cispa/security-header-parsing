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
        # req["status"]
        # req["message"]
        # req["stack"]

        for test in req["tests"]:
            print(test)
            outcome_type = str(type(test["outcome"]))  # Not useful if test["outcome"] always is a JSON dict
            outcome_value = test["outcome"]

            test_name = test["name"]
            test_status = test["status"]
            test_message = test["message"]
            test_stack = test["stack"]

            testcase_id = 1 # TODO: get testcase ID from the test; see models.py for challenges (test needs to know it's own id?)
            response_id = test["name"].split("|")[-1]
            res = Result(outcome_type=outcome_type, outcome_value=outcome_value, test_name=test_name, test_status=test_status, test_message=test_message, test_stack=test_stack, browser_id=browser_id, testcase_id=testcase_id, response_id=response_id, status='FINISHED')
            session.add(res)
            print("\n Stored Successfully \n")
        res = {'Status': 'Success'}
        session.commit()
        return res

