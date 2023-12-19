import json
import argparse
import os
import sys
import time

from pathlib import Path
import numpy as np

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
HOME_PATH = str(Path.home())
MODE = 'basic'
sys.path.append(os.path.join(CURRENT_PATH, '../'))

APK_DIR = os.path.join(HOME_PATH, 'develop/cispa/apk-browsers')


from utils import get_tests, TIMEOUT
from android_emulators import cmd_emulators as emulators
from multiprocessing import Pool


class PARAMETER:
	def __init__(self, app_list):
		self.app_list = app_list

class APP:
	def __init__(self, package_name, activity_name, test_url):
		self.package_name = package_name
		self.activity_name = activity_name
		self.device_id = None			
		self.test_url = test_url
	
	def set_test_device(self, device_id):
		self.device_id = device_id

def run_test(parameter):
	for app in parameter.app_list:		
		print(f'Testing: {app.package_name}, on device ID: {app.device_id}, with URL: {app.test_url}')				
		
		# starting the browser to create init profile
		emulators.send_url_intent(app.device_id, app.package_name, app.activity_name, 'www.google.com')
		time.sleep(5)		
		
		encoded_test_url = app.test_url.replace('&','\&')
		
		emulators.send_url_intent(app.device_id, app.package_name, app.activity_name, encoded_test_url)
		time.sleep(TIMEOUT*1000)				
		

def main(browser_list, config_dict):
	app_list = list()
	for browser_name in browser_list:
		browser_config = config_dict[browser_name]

		print(browser_config)
		return
		browser_id = browser_config['id']
		test_urls = list()
		for scheme in ["http", "https"]:
			test_urls.extend(get_tests(resp_type=MODE, browser_id=browser_id, scheme=scheme))
	
		device_ids = emulators.get_available_device()	
		for url in test_urls:
			app_list.append(APP(browser_config['package_name'], browser_config['intent'], url))

	chunked_app_lists = np.array_split(app_list, len(device_ids))
	
	for index, working_list in enumerate(chunked_app_lists):
		device_id = device_ids[index]
		for app in working_list:
			app.set_test_device(device_id)

	parameters = []
	for working_list in chunked_app_lists:
		parameters.append(PARAMETER(working_list))

	pool = Pool()
	pool.map(run_test, parameters)

if __name__ == '__main__':
	with open('android_config.json') as file:
		config_dict = json.load(file)

	browser_list = list(config_dict.keys())
	browser_list.append('all')

	ap = argparse.ArgumentParser(description='Tester for Android devices')
	ap.add_argument('-browsers', '--browsers', dest='browsers', type=str, required=True, nargs='+', choices=browser_list)
	args = ap.parse_args()

	print(f'Starting test on {args.browsers} ...')	
	
	main(args.browsers, config_dict)