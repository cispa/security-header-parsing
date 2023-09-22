from wptserve.handlers import json_handler
import json
from models import Result
from models import Session, SECRET

    
@json_handler
def main(request, response):
    with Session() as session:
        req = json.loads(request.body)
        print(req)
        browser_id = 1 # req["browser"]
        # req["status"]
        # req["message"]
        # req["stack"]

        # TODO: do something with the SECRET or remove it everywhere?
        # TODO: Save both outcome_type and outcome_value!
        # TODO: add error handling/sanity checking/...?
        for test in req["tests"]:
            # TODO: get browser_id, testcase_id and response_id from the test
            print(test)
            outcome_type = "String"
            outcome_value = test["outcome"]

            test_name = test["name"]
            test_status = test["status"]
            test_message = test["message"]
            test_stack = test["stack"]

            testcase_id = 1
            response_id = 1 # TODO get the id from the response
            res = Result(outcome_type=outcome_type, outcome_value=outcome_value, test_name=test_name, test_status=test_status, test_message=test_message, test_stack=test_stack, browser_id=browser_id, testcase_id=testcase_id, response_id=response_id)
            session.add(res)
            print("\n Stored Successfully \n")
        res = {'Status': 'Success'}
        session.commit()
        return res

