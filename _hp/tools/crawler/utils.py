import httpx
import json
import uuid

from sqlalchemy import ClauseElement
from sqlalchemy.exc import IntegrityError

try:
    from models import Session, Browser
except:
    import sys
    from pathlib import Path
    file = Path(__file__).resolve()
    parent, root = file.parent, file.parents[1]
    sys.path.append(str(root))
    from models import Session, Browser


# Time until all tests on a page have to be finished (called done())
# TODO: make configurable for different tests and/or browsers! (or e.g., higher timeouts for repeats)
# TODO: the upgrade-hsts.sub.html tests should use a higher timeout?! (as each request is done one after another and each individual request has a timeout of TIMEOUT/5)
GLOBAL_TEST_TIMEOUT = 5  # Also known as test_timeout in testharness.sub.js

# Time after a single test marks itself as "no message received"
# SINGLE_TEST_TIMEOUT = 0.9 * GLOBAL_TEST_TIMEOUT # 0.9 is hardcoded in the tests (0.9 * test_timeout)

# Time it takes to open the browser and perform the inital request to the test page
# TODO: this is different for different browsers, some mobile browsers are really slow; use a dict?
BROWSER_START_TIMEOUT = 1
# Time to wait for the final request to finish
FINAL_REQ_TIMEOUT = 1

# Note: in desktop_selenium we currently have a max_page_load of 2xTIMEOUT and wait for a maximum of TIMEOUT after the page is loaded; we can't replicate this behavior in mobile?
# Also we finish early when we see the #finished div in the page with Selenium which we cannot do on mobile
TIMEOUT = BROWSER_START_TIMEOUT + GLOBAL_TEST_TIMEOUT + FINAL_REQ_TIMEOUT


base_host = "sub.headers.websec.saarland"
base_dir = "_hp/tests"
HSTS_DEACTIVATE = f"https://{base_host}/_hp/common/empty.html?pipe=header(strict-transport-security,max-age=0)|status(200)"


test_info = [
    # Only for basic tests!
    
    # [(test_file_name, label_name, number_of_response_ids, num_popup_parsing, num_popup_basic)]
    # number_of_response_ids is the maxium number of response_ids allowed for parsing tests
    ("fetch-cors.sub.html", "CORS", 1, 0, 0),  # Tests: 32 (8*4), 4 
    # Comment: Num tests per resp_id: <basic/debug> (Origin relations x NumTests), parsing (for one base URL; x2 as most tests are loaded from both HTTP and HTTPS)

    # Only for parsing tests!
    # For parsing tests, run more than one response at a time (maximum of ten included frames/images or 40 fetches or 1 popup or 4 promise tests)
    # Empirically reduced fetch, COEP, and CSP-IMG (as there were a couple of tests with different/timeout results)
    ("fetch-cors.sub.html", "CORS-ACAO", 5, 0, 0),  # Tests: 32 (8*4), 4
    ("fetch-cors.sub.html", "CORS-ACAC", 5, 0, 0),  # Tests: 32 (8*4), 4
    ("fetch-cors.sub.html", "CORS-ACAM", 5, 0, 0),  # Tests: 32 (8*4), 4
    ("fetch-cors.sub.html", "CORS-ACAH", 5, 0, 0),  # Tests: 32 (8*4), 4
    ("fetch-cors.sub.html", "CORS-ACEH", 5, 0, 0),  # Tests: 32 (8*4), 4
    
    # All tests!
    ("framing.sub.html", "XFO", 5, 0, 0),  # Tests:  72 (8*9), 2
    ("framing.sub.html", "CSP-FA", 5, 0, 0),  # Tests:  72 (8*9), 2
    ("framing.sub.html", "CSPvsXFO", 5, 0, 0),  # Tests:  72 (8*9), 2
    ("fullscreen-api-pp.sub.html", "PP", 5, 0, 0),  # Tests: 32 (8*4), 2
    ("originAgentCluster-oac.sub.html", "OAC", 1, 1, 8),  # Tests: 24 (8*3), 1
    ("perfAPI-tao.sub.html", "TAO", 10, 0, 0),  # Tests: 8 (8*1), 1
    ("referrer-access-rp.sub.html", "RP", 10, 0, 8),  # Tests: 16 (8*2), 1
    ("script-execution-csp.sub.html", "CSP-SCRIPT", 10, 0, 0),  # Tests: 16 (8*2), 1
    ("subresource-loading-coep.sub.html", "COEP", 5, 0, 0),  # Tests: 16 (8*2), 1
    ("subresource-loading-corp.sub.html", "CORP", 10, 0, 0),  # Tests: 32 (8*4), 1
    ("subresource-loading-csp.sub.html", "CSP-IMG", 5, 0, 0),  # Tests: 8 (8*1), 1
    ("window-references-coop.sub.html", "COOP", 1, 1, 8),  # Tests: 8 (8*1), 1
   
    # HTTP only
    ("upgrade-hsts.sub.html", "HSTS", 1, 0, 0),    # Tests: 4 (2*2), 4 (2*2) # Promise tests thus only one resp_id
]


def get_tests(resp_type, browser_id, scheme, max_popups=1000, max_resps=1000):
    test_urls = []
    for url, label, num_resp_ids, popup_parsing, popup_basic in test_info:
        num_popups = popup_parsing if resp_type == "parsing" else popup_basic
        # HSTS test are not executed for HTTPS
        if "upgrade" in url and scheme == "https":
            continue
        # CORS tests are different for parsing/basic mode
        if label.startswith("CORS"):
            if label != "CORS" and resp_type != "parsing":
                continue
            if label == "CORS" and resp_type == "parsing":
                continue
        
        # Allow more than one response_id per test for parsing tests
        if resp_type == "parsing":
            max_resp_ids = min(num_resp_ids, max_resps)
        else:
            max_resp_ids = 1

        for first_id, last_id in get_resp_ids(label, resp_type, max_resp_ids):
            # All popups are the number of popups (per response_id) * the number of response_ids
            all_popups = num_popups * (last_id - first_id + 1)
            # If there are more popups than max_popups add URLs for each popup count
            if all_popups > max_popups:
                buckets = [list(range(start, min(start + max_popups, all_popups + 1)))
                           for start in range(1, all_popups + 1, max_popups)]
                # Only add run_no_popups to the first one
                run_no_popup = "yes"
                for bucket in buckets:
                    first_popup = bucket[0]
                    last_popup = bucket[-1]
                    test_urls.append(
                        f"{scheme}://{base_host}/{base_dir}/{url}?timeout={GLOBAL_TEST_TIMEOUT}&resp_type={resp_type}&browser_id={browser_id}&label={label}&first_id={first_id}&last_id={last_id}&scheme={scheme}&first_popup={first_popup}&last_popup={last_popup}&run_no_popup={run_no_popup}")
                    run_no_popup = "no"
                # print(buckets)
            # Otherwise run all tests
            else:
                test_urls.append(
                    f"{scheme}://{base_host}/{base_dir}/{url}?timeout={GLOBAL_TEST_TIMEOUT}&resp_type={resp_type}&browser_id={browser_id}&label={label}&first_id={first_id}&last_id={last_id}&scheme={scheme}")
    return test_urls


def get_resp_ids(label, resp_type, num_resp_ids):
    assert num_resp_ids >= 1

    resp_ids = httpx.get(
        f"https://{base_host}/_hp/server/get_resp_ids.py?label={label}&resp_type={resp_type}", verify=False).json()
    if num_resp_ids == 1:
        return [(resp_id, resp_id) for resp_id in resp_ids]
    # Use num_resp_ids to return continuous chunks of resp_ids with a maximum length of num_resp_ids
    else:
        splits = []
        start = cur = count = None
        for next in resp_ids:
            if start is None:
                start = cur = next
                count = 1
            elif next - cur != 1:
                splits.append((start, cur))
                start = cur = next
                count = 1
            else:
                count += 1
                cur = next
                if count == num_resp_ids:
                    splits.append((start, cur))
                    start = cur = count = None
        if start != None:
            splits.append((start, cur))
        return splits


def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.items()
                      if not isinstance(v, ClauseElement))
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        session.commit()
        return instance, True


def get_or_create_browser(name, version, os, headless_mode, automation_mode, add_info):
    with Session() as session:
        try:
            browser, created = get_or_create(
                session,
                Browser,
                defaults=dict(),
                name=name,
                version=version,
                os=os,
                headless_mode=headless_mode,
                automation_mode=automation_mode,
                add_info=add_info
            )
            if created:
                print("New Browser created")
            return browser.id

        except IntegrityError as e:
            session.rollback()
            print("IntegrityError", e)


def create_test_page_runner(browser_id, identifier, test_urls):
    """Create a test-page runner page for a given browser_id and a list of test_urls."""
    test_runner_page = f"test-page-runner-{browser_id}_{identifier}.html"
    test_runner_url = f"https://{base_host}/_hp/tests/{test_runner_page}"
    with open("test-page-runner.html") as file:
        html_template = file.read()
        html_template = html_template.replace(
            '$$$URLS$$$', json.dumps(test_urls))
        html_template = html_template.replace(
            '$$$TIMEOUT$$$', str(TIMEOUT*1000))
        with open(f'../../tests/{test_runner_page}', 'w') as file:
            file.write(html_template)
    return test_runner_url

def generate_short_uuid(length=6):
    if length <= 0:
        raise ValueError("Length must be a positive integer")
    
    # Generate a UUID
    full_uuid = uuid.uuid4()
    # Convert it to a string and extract the specified number of characters
    short_uuid = str(full_uuid)[:length]
    return short_uuid