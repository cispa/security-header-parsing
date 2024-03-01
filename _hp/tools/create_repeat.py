import json
import re
from analysis.utils import get_data, Config
from crawler.utils import GLOBAL_TEST_TIMEOUT

# Create a json with all tests to redo (either timed out or completely missing in one or more of the 5 runs)
# Idea: group by test and count how many outcomes for each browser were observed
# For all tests that have less than 5 results, save them (unique page loads) to a file
# Caveat: easy way will usually also result in the duplication of other tests (e.g., 5/10 tests on a page load timed out -> 10 tests will be repeated)
# However this should not matter too much as test results should be stable and we perform majority voting on the results

def calc_repeat():
    # Load all data
    initial_data = """
    SELECT "Result".*, 
    "Response".raw_header, "Response".status_code, "Response".label, "Response".resp_type,
    "Browser".name, "Browser".version, "Browser".headless_mode, "Browser".os, "Browser".automation_mode, "Browser".add_info
    FROM "Result"
    JOIN "Response" ON "Result".response_id = "Response".id JOIN "Browser" ON "Result".browser_id = "Browser".id
    WHERE "Browser".name != 'Unknown' and "Response".resp_type != 'debug'
    and "Browser".os != 'Android 11'; -- For now ignore Android
    """
    df = get_data(Config(), initial_data)
    
    def clean_url(url):
        url = re.sub(r"browser_id=(\d+)", "browser_id=1", url)
        url = re.sub(r"&first_popup=(\d+)&last_popup=(\d+)&run_no_popup=(yes|no)", "", url)
        url = re.sub(r"timeout=(\d+)&", "", url)
        return url
    df["clean_url"] = df["full_url"].apply(clean_url)
   
    def create_test_id(row):
        return f'{row["test_name"]}_{row["relation_info"]}_{row["org_scheme"]}_{row["org_host"]}_{row["resp_scheme"]}_{row["resp_host"]}_{row["response_id"]}_{row["resp_type"]}'
    df["browser_id"] = df["browser_id"].astype("category")
    # Takes a while (500s+) (might be faster to already do it with postgres but not too important)
    df["test_id"] = df.apply(create_test_id, axis=1)
    df["test_id"] = df["test_id"].astype("category")
    
    test_counts = df.groupby(["test_id"], observed=True)["browser_id"].value_counts()
    tests_to_repeat = test_counts.loc[test_counts < 5].reset_index()
    print(tests_to_repeat[["browser_id", "count"]].value_counts())

    rep = tests_to_repeat.merge(df.drop_duplicates(subset=["test_id"]), on=["test_id"], how="left", suffixes=["", "_ignore"])
    to_repeat = {}
    for _, row in rep.iterrows():
        browser_id = str(row["browser_id"])
        response_id = row["response_id"]
        try:
            d = to_repeat[browser_id]
        except KeyError:
            d = set()
        base_url = row["clean_url"]
        repeat_url = re.sub("browser_id=(\d+)", f"browser_id={browser_id}", base_url)
       
        # For repetition runs, always only have one response_id per URL!
        repeat_url = re.sub("first_id=(\d+)", f"first_id={response_id}", repeat_url)
        repeat_url = re.sub("last_id=(\d+)", f"last_id={response_id}", repeat_url)
        # Increase the TIMEOUT to make additional issues due to timeouts less likely
        repeat_url = re.sub("\?", f"?timeout={3*GLOBAL_TEST_TIMEOUT}&", repeat_url, count=1)
        
        # TODO: for mobile browsers the first_popup, last_popup, run_no_popup has to be added again?

        d.add(repeat_url)
        to_repeat[browser_id] = d
    with open("repeat.json", "w") as f:
        json.dump(to_repeat, f, default=list)

if __name__ == '__main__':
    calc_repeat()