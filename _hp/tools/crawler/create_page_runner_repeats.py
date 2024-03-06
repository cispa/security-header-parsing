import json
from utils import create_test_page_runner, generate_short_uuid
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convert repeats for pagerunner.")
    parser.add_argument("--browser_id", type=int, required=True)
    args = parser.parse_args()

    with open("../repeat.json", "r") as f:
        d = json.load(f)
    
    browser_id = str(args.browser_id)

    rand_token = generate_short_uuid()
    print(d[browser_id])
    r = create_test_page_runner(browser_id, f"{rand_token}-0", d[browser_id])
    print(r)