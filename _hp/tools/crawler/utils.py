import httpx

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
GLOBAL_TEST_TIMEOUT = 5 # Also known as test_timeout in testharness.sub.js

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

# [(test_file_name, label_name, number_of_response_ids)]
# Comment: Num tests per resp_id: <basic/debug>, parsing (for one base URL; x2 as most tests are loaded from both HTTP and HTTPS)
test_info = [
    ("fetch-cors.sub.html", "CORS", 1, 0, 0),  # Tests: 32 (8*4), 4
    ("framing.sub.html", "XFO", 1, 0, 0),  # Tests:  72 (8*9), 2
    ("framing.sub.html", "CSP-FA", 1, 0, 0),  # Tests:  72 (8*9), 2
    ("framing.sub.html", "CSPvsXFO", 1, 0, 0),  # Tests:  72 (8*9), 2
    ("fullscreen-api-pp.sub.html", "PP", 1, 0, 0),  # Tests: 32 (8*4), 2
    ("originAgentCluster-oac.sub.html", "OAC", 1, 1, 8),  # Tests: 24 (8*3), 1
    ("perfAPI-tao.sub.html", "TAO", 1, 0, 0),  # Tests: 8 (8*1), 1
    ("referrer-access-rp.sub.html", "RP", 1, 0, 8),  # Tests: 16 (8*2), 1
    ("script-execution-csp.sub.html", "CSP-SCRIPT", 1, 0, 0),  # Tests: 16 (8*2), 1
    ("subresource-loading-coep.sub.html", "COEP", 1, 0, 0),  # Tests: 16 (8*2), 1
    ("subresource-loading-corp.sub.html", "CORP", 1, 0, 0),  # Tests: 32 (8*4), 1
    ("subresource-loading-csp.sub.html", "CSP-IMG", 1, 0, 0),  # Tests: 8 (8*1), 1
    ("window-references-coop.sub.html", "COOP", 1, 1, 8),  # Tests: 8 (8*1), 1
    # HTTP only
    ("upgrade-hsts.sub.html", "HSTS", 1, 0, 0),    # Tests: 4 (2*2), 4 (2*2)
]


def get_tests(resp_type, browser_id, scheme, max_popups=1000):
    test_urls = []
    for url, label, num_resp_ids, popup_parsing, popup_basic in test_info:
        num_popups = popup_parsing if resp_type == "parsing" else popup_basic
        if "upgrade" in url and scheme == "https":
            continue
        else:
            for first_id, last_id in get_resp_ids(label, resp_type, num_resp_ids):
                # If there are more popups than max_popups add URLs for each popup count, only add run_no_popups to the first one
                if num_popups > max_popups:
                    buckets = [list(range(start, min(start + max_popups, num_popups + 1))) for start in range(1, num_popups + 1, max_popups)]
                    run_no_popup = "yes"
                    for bucket in buckets:
                        first_popup = bucket[0]
                        last_popup = bucket[-1]
                        test_urls.append(
                            f"{scheme}://{base_host}/{base_dir}/{url}?timeout={GLOBAL_TEST_TIMEOUT}&resp_type={resp_type}&browser_id={browser_id}&label={label}&first_id={first_id}&last_id={last_id}&scheme={scheme}&first_popup={first_popup}&last_popup={last_popup}&run_no_popup={run_no_popup}")
                        run_no_popup = "no"
                    print(buckets)
                # Otherwise run all tests
                else:
                    test_urls.append(
                        f"{scheme}://{base_host}/{base_dir}/{url}?timeout={GLOBAL_TEST_TIMEOUT}&resp_type={resp_type}&browser_id={browser_id}&label={label}&first_id={first_id}&last_id={last_id}&scheme={scheme}")
    return test_urls


def get_resp_ids(label, resp_type, num_resp_ids):
    resp_ids = httpx.get(
        f"https://{base_host}/_hp/server/get_resp_ids.py?label={label}&resp_type={resp_type}", verify=False).json()
    # TODO: use num_resp_ids to return continuous chunks of resp_ids with a maximum length of num_resp_ids
    # For now: each chunk is always size 1, regardless of parameter
    return [(resp_id, resp_id) for resp_id in resp_ids]


def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement))
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        session.commit()
        return instance, True

def get_or_create_browser(name, version, os, headless_mode, automation_mode, add_info):
    with Session() as session:
        try:
            # Using the get_or_create function
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