TIMEOUT = 11 # Seconds; test timeout is 10000 miliseconds and we want to make sure we wait long enough to save the results

base_host = "sub.headers.websec.saarland"
base_dir = "_hp/tests"

tests = ["fetch-cors.sub.html",
         "framing.sub.html", # labels: XFO, CSP-FA, CSPvsXFO
         "fullscreen-api-pp.sub.html",
         "originAgentCluster-oac.sub.html",
         "perfAPI-tao.sub.html",
         "referrer-access-rp.sub.html",
         "script-execution-csp.sub.html",
         "subresource-loading-coep.sub.html",
         "subresource-loading-corp.sub.html",
         "subresource-loading-csp.sub.html", 
         "upgrade-hsts.sub.html", # HTTP only
         "window-references-coop.sub.html"
         ]

def get_tests(resp_type, browser_id, scheme):
    test_urls = []
    for url in tests:
        if "framing" in url:
            for label in ["XFO", "CSP-FA", "CSPvsXFO"]:
                test_urls.append(f"{scheme}://{base_host}/{base_dir}/{url}?resp_type={resp_type}&browser_id={browser_id}&label={label}")
        if "upgrade" in url and scheme == "https":
            continue
        else:
            test_urls.append(f"{scheme}://{base_host}/{base_dir}/{url}?resp_type={resp_type}&browser_id={browser_id}")
    return test_urls


# TODO: implement resp_ids fetching and chunking for parsing tests here!