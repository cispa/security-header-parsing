"""
# Create a json with all tests to redo (either timed out or completely missing in one or more of the 5 runs)
# Method: group by test and count how many outcomes for each browser were observed
# For all tests that have less than 5 results, save them (unique page loads) to a file
# Caveat: easy way will usually also result in the duplication of other tests (e.g., 5/10 tests on a page load timed out -> 10 tests will be repeated)
# However this does not matter too much as test results should be stable and we perform majority voting on the results
"""

import argparse
import json
import re
from hp.tools.analysis.utils import get_data, Config

def calc_repeat(selection_str, mult_resp_ids):
    """Generates repeat.json with all tests that have to be repeated in all browsers (if they currently have less than 5 runs recorded)

    Args:
        selection_str (str): Postgres WHERE statement to only get a subset of data (e.g., only one OS)
        mult_resp_ids (bool): If true multiple response IDs are included in the same test URL, if false each response ID gets a unique test URL

    Returns:
        None
    """
    # Load all data
    initial_data = f"""
    SELECT "Result".*,
    "Response".raw_header, "Response".status_code, "Response".label, "Response".resp_type,
    "Browser".name, "Browser".version, "Browser".headless_mode, "Browser".os, "Browser".automation_mode, "Browser".add_info
    FROM "Result"
    JOIN "Response" ON "Result".response_id = "Response".id JOIN "Browser" ON "Result".browser_id = "Browser".id
    WHERE "Browser".name != 'Unknown' and "Response".resp_type != 'debug' and test_status = 0
    and {selection_str};
    """
    df = get_data(Config(), initial_data)

    def clean_url(url):
        """Remove irrelevant data from URLs

        Args:
            url (str): full URL

        Returns:
            str: URL without browser_id, timeout, run_id, popup information
        """
        url = re.sub(r"browser_id=(\d+)", "browser_id=1", url)
        url = re.sub(r"&first_popup=(\d+)&last_popup=(\d+)&run_no_popup=(yes|no)", "", url)
        url = re.sub(r"&run_id=(\w+)", "", url)
        url = re.sub(r"timeout=(\d+)&", "", url)
        return url
    df["clean_url"] = df["full_url"].apply(clean_url)

    def create_test_id(row):
        """Create the test_id of a given row

        Args:
            row (pd.Series): One row of the Result DataFrame

        Returns:
            str: TestID consisting of test_name_relation_info_org_scheme_org_host_resp_scheme_resp_host_response_id_resp_type
        """
        return f'{row["test_name"]}_{row["relation_info"]}_{row["org_scheme"]}_{row["org_host"]}_{row["resp_scheme"]}_{row["resp_host"]}_{row["response_id"]}_{row["resp_type"]}'
    df["browser_id"] = df["browser_id"].astype("category")
    # Takes a while (500s+)
    df["test_id"] = df.apply(create_test_id, axis=1)
    df["test_id"] = df["test_id"].astype("category")

    test_counts = df.groupby(["test_id"], observed=True)["browser_id"].value_counts()
    # All tests that have less than 5 occurrences in a browser have to be repreated
    tests_to_repeat = test_counts.loc[test_counts < 5].reset_index()
    print(tests_to_repeat[["browser_id", "count"]].value_counts())

    rep = tests_to_repeat.merge(df.drop_duplicates(subset=["test_id"]), on=["test_id"], how="left", suffixes=["", "_ignore"])
    to_repeat = {}
    # Generate a dict with all tests to repeat
    # Insert the TIMEOUT information, browser_id, and co. again
    for _, row in rep.iterrows():
        browser_id = str(row["browser_id"])
        response_id = row["response_id"]
        try:
            d = to_repeat[browser_id]
        except KeyError:
            d = set()
        base_url = row["clean_url"]
        repeat_url = re.sub("browser_id=(\d+)", f"browser_id={browser_id}", base_url)

        # For repetition runs, only have one response_id per URL unless specified differently
        if not mult_resp_ids:
            f_id = re.search(r"first_id=(\d+)", repeat_url)
            l_id = re.search(r"last_id=(\d+)", repeat_url)
            repeat_url = re.sub("first_id=(\d+)", f"first_id={response_id}", repeat_url)
            repeat_url = re.sub("last_id=(\d+)", f"last_id={response_id}", repeat_url)
        # Increase the TIMEOUT (x2) to make additional issues due to timeouts less likely
        full_url = row["full_url"]
        old_timeout = int(re.findall(r"timeout=(\d+)", full_url)[0])
        repeat_url = re.sub("\?", f"?timeout={2*old_timeout}&", repeat_url, count=1)
        first_popup = re.search(r"first_popup=(\d+)", full_url)
        last_popup = re.search(r"last_popup=(\d+)", full_url)
        run_no_popup = re.search(r"run_no_popup=(\w+)", full_url)
        # This assumes that all rows in the initial df had the same max_popups settings (Thus limit to only Android or only non-Android with the selection_str)
        if first_popup:
            if int(l_id[1]) - int(f_id[1]) != 0:
                raise Exception(f"Not possible to set correct first/last popup: {full_url} ")
            repeat_url += f"&{first_popup[0]}&{last_popup[0]}&{run_no_popup[0]}"

        d.add(repeat_url)
        to_repeat[browser_id] = d
    # Safe all tests to repeat in a JSON file
    with open("repeat.json", "w") as f:
        json.dump(to_repeat, f, default=list)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Create repeat runs.")
    parser.add_argument("--selection_str", type=str, default='"Browser".os = \'Android 11\' and "Browser".os = \'Android 11\'',
                        help="Postgres selection string")
    parser.add_argument("--mult_resp_ids", action="store_true", help="Activate multiple resp_ids per URL.")
    args = parser.parse_args()

    calc_repeat(args.selection_str, args.mult_resp_ids)
