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
    print(len(d[browser_id]))
    
    safari_special = False
    if safari_special:
        test_urls = d[browser_id]
        url_chunks = [test_urls[i:i + 1000] for i in range(0, len(test_urls), 1000)]
        url_list = []
        chunk_id = 0
        for url_chunk in url_chunks:
            url_list.append(create_test_page_runner(browser_id, f"{rand_token}-{chunk_id}", url_chunk))
            chunk_id += 1

        print(f"URLs to visit: {url_list}")
        with open(f"parsing-MaxURLs1000-MaxResps10-MaxPopups100-{rand_token}.json", "w") as f:
                json.dump(url_list, f)
    else:
        r = create_test_page_runner(browser_id, f"{rand_token}-0", d[browser_id])
        print(r)