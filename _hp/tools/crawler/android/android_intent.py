import json
import argparse
import os
import sys

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(CURRENT_PATH, '../'))

from pathlib import Path
from utils import get_tests

import psutil
import subprocess
import requests
import time
import signal
import hashlib
import base64
import urllib
from multiprocessing import Pool
from itertools import repeat
# from cmd_emulators import start_emulators, install_apk, force_stop_all_emulators, get_installed_apps, grant_location_permission

HOME_PATH = str(Path.home())
PLATFORM_PATH = os.path.join(CURRENT_PATH, 'platform-tools')
MODE = 'basic'

def main(browser_config):
	browser_id = browser_config['id']
	test_urls = list()
	for scheme in ["http", "https"]:
		test_urls.extend(get_tests(resp_type=MODE, browser_id=browser_id, scheme=scheme))
	
	for url in test_urls:
		print(url)


if __name__ == '__main__':
	with open('android_config.json') as file:
		config_dict = json.load(file)
	
	ap = argparse.ArgumentParser(description='Tester for Android devices')
	ap.add_argument('-browser', '--browser', dest='browser', type=str, required=True, choices=config_dict.keys())
	args = ap.parse_args()
	
	main(config_dict[args.browser])
	