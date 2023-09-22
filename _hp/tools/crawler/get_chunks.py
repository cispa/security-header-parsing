import requests
import os
import json
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

proj_config= json.load(open("../config.json"))
SAME_ORIGIN = proj_config['SAME_ORIGIN']
CROSS_ORIGIN =proj_config['CROSS_ORIGIN']
SERVER_URL=f"https://{SAME_ORIGIN}"

def calc_offsets(count, limit):
  return [i for i in range(0, count, limit)]

def get_testcases(header_name):
    result = requests.get(f"{SERVER_URL}/get_count?header={header_name}",verify=False)
    count = result.json()['count']
    print(count)
    limit =10
    offsets = calc_offsets(count,limit)
    print(offsets)
    for offset in offsets:
        # !!! Drive the Browser to this URL to run the test chunks !!!
        resp=requests.get(f"{SERVER_URL}/{header_name}/{header_name}.html?limit={limit}&offset={offset}",verify=False)
        print("\n\n")
        print(resp.content)

get_testcases('xfo')