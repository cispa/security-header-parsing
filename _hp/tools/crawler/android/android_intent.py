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
	def __init__(self, package_name, activity_name, apk_file, test_url):
		self.package_name = package_name
		self.activity_name = activity_name
		self.device_id = None	
		self.apk_file = apk_file
		self.test_url = test_url
	
	def set_test_device(self, device_id):
		self.device_id = device_id

def run_test(parameter):
	browser_factor = 1	

	for app in parameter.app_list:		
		print(f'Testing: {app.package_name}, on device ID: {app.device_id}, with URL: {app.test_url}')		
		emulators.install_app(app.package_name, app.apk_file, app.device_id)		
		if app.package_name == 'com.UCMobile.intl':
			browser_factor = 2

		time.sleep(5*browser_factor)
		
		# starting the browser to create init profile
		emulators.send_url_intent(app.device_id, app.package_name, app.activity_name, 'www.google.com')
		time.sleep(2*browser_factor)
		emulators.enable_popup(app.device_id, app.package_name)
		
		encoded_test_url = app.test_url.replace('&','\&')
		
		emulators.send_url_intent(app.device_id, app.package_name, app.activity_name, encoded_test_url)
		time.sleep(TIMEOUT*1000)
		
		emulators.uninstall_app(app.package_name, app.device_id)
		time.sleep(5*browser_factor)

def main(browser_config):
	browser_id = browser_config['id']
	test_urls = list()
	for scheme in ["http", "https"]:
		test_urls.extend(get_tests(resp_type=MODE, browser_id=browser_id, scheme=scheme))
	
	device_ids = emulators.get_available_device()
	apk_file = os.path.join(APK_DIR, browser_config['apk_file'])
	
	app_list = list()
	for url in test_urls:
		app_list.append(APP(browser_config['package_name'], browser_config['intent'], apk_file, url))

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
	
	ap = argparse.ArgumentParser(description='Tester for Android devices')
	ap.add_argument('-browser', '--browser', dest='browser', type=str, required=True, choices=config_dict.keys())
	args = ap.parse_args()
	
	main(config_dict[args.browser])