import json
import re
from analysis.utils import get_data, Config

# Create a json with all tests to redo (either timed out or completely missing)
# Idea: group by test and count number of unique browser_ids
# Get the maximum count
# For all tests that do not have the maximum count, compute which ones are missing
# Save them (unique page loads) to a file
# Caveat1: easy way will usually also result in the duplication of other tests (e.g., 5/10 tests on a page load timed out -> 10 tests will be repeated)
# However this should not matter too much as test results should be stable (see stability analysis below)
# Question: how to increase the TIMEOUT in these reruns to make the chances of additional time outs as low as possible?

def calc_repeat():
    # Load all data
    initial_data = """
    SELECT "Result".*, 
    "Response".raw_header, "Response".status_code, "Response".label, "Response".resp_type,
    "Browser".name, "Browser".version, "Browser".headless_mode, "Browser".os, "Browser".automation_mode, "Browser".add_info
    FROM "Result"
    JOIN "Response" ON "Result".response_id = "Response".id JOIN "Browser" ON "Result".browser_id = "Browser".id
    WHERE "Browser".name != 'Unknown' and "Response".resp_type != 'debug';
    """
    df = get_data(Config(), initial_data)
    
    def clean_url(url):
        url = re.sub(r"browser_id=(\d+)", "browser_id=1", url)
        url = re.sub(r"&first_popup=(\d+)&last_popup=(\d+)&run_no_popup=(yes|no)", "", url)
        url = re.sub(r"timeout=(\d+)&", "", url)
        return url
    df["clean_url"] = df["full_url"].apply(clean_url)

    all_browsers = set(df["browser_id"].unique()) 
    def get_missing(browser_list):
        return all_browsers - set(browser_list)
    
    browser_count = df.loc[df["test_status"] == 0].groupby(["test_name", "relation_info", "org_scheme", "org_host", "resp_scheme", "resp_host", "response_id", "clean_url"])["browser_id"].unique()
    max_c = browser_count.apply(len).max()
    missing = browser_count.loc[browser_count.apply(len) != max_c].apply(get_missing)
    to_repeat = {}
    for (test_name, relation_info, org_scheme, org_host, resp_scheme, resp_host, response_id, clean_url), row in missing.to_frame().iterrows():
        browser_ids = row.iloc[0]
        for browser_id in browser_ids:
            browser_id = str(browser_id)
            try:
                d = to_repeat[browser_id]
            except KeyError:
                d = set()
            # TODO: for mobile browsers the first_popup, last_popup, run_no_popup has to be added again?
            d.add(re.sub("browser_id=(\d+)", f"browser_id={browser_id}", clean_url))
            to_repeat[browser_id] = d
    with open("repeat.json", "w") as f:
        json.dump(to_repeat, f, default=list)

if __name__ == '__main__':
    calc_repeat()