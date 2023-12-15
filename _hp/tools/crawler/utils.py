import httpx

TIMEOUT = 6  # Seconds; test timeout is 5000 miliseconds and we want to make sure we wait long enough to save the results

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
                            f"{scheme}://{base_host}/{base_dir}/{url}?resp_type={resp_type}&browser_id={browser_id}&label={label}&first_id={first_id}&last_id={last_id}&scheme={scheme}&first_popup={first_popup}&last_popup={last_popup}&run_no_popup={run_no_popup}")
                        run_no_popup = "no"
                    print(buckets)
                # Otherwise run all tests
                else:
                    test_urls.append(
                        f"{scheme}://{base_host}/{base_dir}/{url}?resp_type={resp_type}&browser_id={browser_id}&label={label}&first_id={first_id}&last_id={last_id}&scheme={scheme}")
    return test_urls


def get_resp_ids(label, resp_type, num_resp_ids):
    resp_ids = httpx.get(
        f"https://{base_host}/_hp/server/get_resp_ids.py?label={label}&resp_type={resp_type}").json()
    # TODO: use num_resp_ids to return continuous chunks of resp_ids with a maximum length of num_resp_ids
    # For now: each chunk is always size 1, regardless of parameter
    return [(resp_id, resp_id) for resp_id in resp_ids]
