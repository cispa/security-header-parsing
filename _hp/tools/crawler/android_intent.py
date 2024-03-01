import json
import argparse
import time
import subprocess
import numpy as np

MODE = 'basic'

from utils import get_tests, get_or_create_browser, TIMEOUT
from multiprocessing import Pool
import psycopg
import uuid    


# Setup the config
try:
	proj_config = json.load(open("config.json"))
except OSError:
	try:
		proj_config = json.load(open("_hp/tools/config.json"))
	except OSError:
		proj_config = json.load(open("../config.json"))

DB_URL = proj_config['DB_URL'].replace("postgresql+psycopg2://", "postgresql://")


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

def send_url_intent(device_id, package_name, activity_name, url):	
	cmd_text = f'adb -s {device_id} shell am start -n {package_name}/{activity_name} -a android.intent.action.VIEW -d "{url}"'	
	subprocess.run(cmd_text, shell=True)

def get_available_device():
	cmd_text = f'adb devices'
	cmd_output = subprocess.run(cmd_text, shell=True, check=True, capture_output=True, text=True).stdout.strip()	
	device_id_list = []
	for line in cmd_output.split('\n'):
		if line.startswith('List of devices attached'):
			continue
		if 'offline' not in line:
			device_id = line.split('\t')[0]
			device_id_list.append(device_id)

	return device_id_list


def run_test(parameter):		
	for app in parameter.app_list:			
		print(f'Testing: {app.package_name}, on device ID: {app.device_id}, with URL: {app.test_url}')					

		# starting the browser to create init profile
		send_url_intent(app.device_id, app.package_name, app.activity_name, 'www.google.com')
		time.sleep(3)		

		run_id = uuid.uuid4().hex
		app.test_url += f'&run_id={run_id}'

		encoded_test_url = app.test_url.replace('&','\&')
		with psycopg.connect(DB_URL, autocommit=True) as conn:
			conn.execute("LISTEN page_runner")
			gen = conn.notifies()			

			send_url_intent(app.device_id, app.package_name, app.activity_name, encoded_test_url)

			for notify in gen:
				if notify.payload == run_id:
					print(notify)
					gen.close()				
		
		

def main(browser_list, url_list, config_dict):
	app_list = list()		

	for browser_name in browser_list:
		browser_config = config_dict[browser_name]

		browser_id = get_or_create_browser(browser_name, browser_config['version'], 'Android 11', 'real', 'intent', '')		
		for url in url_list:
			url += f'?browser_id={browser_id}'
			app_list.append(APP(browser_config['package_name'], browser_config['intent'], url))
	

	print(f'Total number of URLs: {len(app_list)}')
	device_ids = get_available_device()	
	
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
	ap.add_argument('-url_json', '--url_json', default='', type=str, help='Path to a json list of page_runner URLs to visit')
	args = ap.parse_args()

	if 'all' in args.browsers:
		args.browsers = list(config_dict.keys())

	if args.url_json:
		with open(args.url_json) as file:
			url_list = json.load(file)		
	
	print(f'Starting test on {args.browsers} ...')	
	
	main(args.browsers, url_list, config_dict)