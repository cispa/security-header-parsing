import json
import argparse
import time
import subprocess
import numpy as np


from desktop_selenium import CustomErrorTimeout, CustomTimeout
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
	def __init__(self, app_list, device_id, auto_restart):
		self.app_list = app_list
		self.device_id = device_id
		self.auto_restart = auto_restart

class APP:
	def __init__(self, package_name, activity_name, test_url):
		self.package_name = package_name
		self.activity_name = activity_name
		self.test_url = test_url		

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

def force_stop_emulators(device_avd_name = None):
	print(f'Stop the enumator name: {device_avd_name}')
	if device_avd_name:
		kill_current_devices_cmd = "kill -9 $(ps aux | grep '[e]mulator/qemu/linux-x86_64/qemu-system-i386-headless @device_"+device_avd_name+" ' | awk '{print $2}')"
		subprocess.run(kill_current_devices_cmd, shell=True)
		time.sleep(2)	
		kill_current_devices_cmd = "kill -9 $(ps aux | grep '[e]mulator/qemu/linux-x86_64/qemu-system-x86_64-headless @device_"+device_avd_name+" ' | awk '{print $2}')"
		subprocess.run(kill_current_devices_cmd, shell=True)
		time.sleep(2)	
	else:
		kill_current_devices_cmd = "kill -9 $(ps aux | grep '[e]mulator/qemu/linux-x86_64/qemu-system-i386-headless @device_' | awk '{print $2}')"
		subprocess.run(kill_current_devices_cmd, shell=True)
		time.sleep(2)	
		kill_current_devices_cmd = "kill -9 $(ps aux | grep '[e]mulator/qemu/linux-x86_64/qemu-system-x86_64-headless @device_' | awk '{print $2}')"
		subprocess.run(kill_current_devices_cmd, shell=True)
		time.sleep(2)	

def get_emulator_avd_name(device_id):
	# device id format: emulator-5554
	emulator_port = int(device_id.split('-')[-1])
	start_port = 5554
	device_name = int((emulator_port - start_port)/2 + 1)
	return str(device_name)

def get_port_by_emulator_avd_name(device_avd_name):
	port = 5552
	for i in range(1,int(device_avd_name) + 1):	
		port += 2
	return port	

def start_emulator_by_avd_name(device_avd_name):
	print(f'Starting the emulator: {device_avd_name}')
	port = get_port_by_emulator_avd_name(device_avd_name)
	cmd_text = f'nohup emulator @device_{device_avd_name} -no-snapshot  -screen multi-touch -no-window -port {port}&'		
	subprocess.run(cmd_text, shell=True)				

	max_times = 0
	is_started = False
	while not is_started and max_times <= 100:		
		print(f'Waiting for the devices : {device_avd_name}, to start!')
		device_id_list = get_available_device()		
		for device_id in device_id_list:
			if device_id == f'emulator-{port}':
				is_started = True		
		time.sleep(2)
		max_times += 1

	time.sleep(5)

	print('Switch to root and connect reverse proxy for adb command line.')
	cmd_text = f'adb -s emulator-{port} root'		
	subprocess.run(cmd_text, shell=True)
	time.sleep(10)	

def start_emulators(num_devices):
	port = 5554
	for device in range(1,num_devices + 1):		
		cmd_text = f'nohup emulator @device_{device} -no-snapshot  -screen multi-touch -no-window -port {port}&'		
		subprocess.run(cmd_text, shell=True)				
		port += 2
		time.sleep(5)

	max_times = 0
	device_id_list = get_available_device()
	while len(device_id_list) < num_devices:
		if max_times >= 100:
			break
		device_id_list = get_available_device()
		print('Waiting for the devices to start!')
		time.sleep(2)
		max_times += 1


	device_id_list = get_available_device()
	print(f'Available devices: {device_id_list}')

	print('Switch to root and connect reverse proxy for adb command line.')
	for device_id in device_id_list:
		print(device_id)
		cmd_text = f'adb -s {device_id} root'		
		subprocess.run(cmd_text, shell=True)

# run on each emulator
def run_test(parameter):		
	device_id = parameter.device_id
	device_avd_name = get_emulator_avd_name(device_id)
	print(f'Testing: on device ID: {device_id}, with number of URLs: {len(parameter.app_list)}')	
	
	run_times = 0	
	for app in parameter.app_list:			
		print(f'Testing: {app.package_name}, on device ID: {device_id}, with URL: {app.test_url}, test run number: {run_times}')					
		run_times += 1		

		run_id = uuid.uuid4().hex
		app.test_url += f'&run_id={run_id}'

		try:
			with CustomErrorTimeout(520*10):
				try:
					encoded_test_url = app.test_url.replace('&','\&')
					with psycopg.connect(DB_URL, autocommit=True) as conn:
						conn.execute("LISTEN page_runner")
						gen = conn.notifies()			

						send_url_intent(device_id, app.package_name, app.activity_name, encoded_test_url)

						for notify in gen:
							if notify.payload == run_id:
								print(notify)
								gen.close()
				except Exception as e:
					print(e)
					print('Timeout exception!')
		except CustomTimeout as e:	
			print(e)
			print('Timeout exception!')
		
		if run_times >= 100 and parameter.auto_restart:
			run_times = 0			
			print(f'Restarting the emulator: {device_id}, AVD: {device_avd_name}')
			force_stop_emulators(device_avd_name)
			start_emulator_by_avd_name(device_avd_name)
			print(f'Done restarting the emulator: {device_id}, AVD: {device_avd_name}')
	
	force_stop_emulators(device_avd_name)
		

def main(browser_list, url_dict, repeat_times, num_devices, resp_type, auto_restart, config_dict):
	app_list = list()		
	url_list = list()

	for browser_name in browser_list:
		browser_config = config_dict[browser_name]

		browser_id = get_or_create_browser(browser_name, browser_config['version'], 'Android 11', 'real', 'intent', '')	

		if not url_dict:
			for scheme in ["http", "https"]:			
				urls = get_tests(resp_type = resp_type, browser_id = browser_id, scheme = scheme, max_popups = 1, browser_modifier = 2)			
				url_list.extend(urls)			
		else:			
			browser_id_key = str(browser_id)
			if browser_id_key in url_dict:
				url_list.extend(url_dict[browser_id_key])
		
		for i in range(0, repeat_times):
			for url in url_list:				
				app_list.append(APP(browser_config['package_name'], browser_config['intent'], url))

	print(f'Total number of URLs: {len(app_list)}')
	
	device_ids = get_available_device()	
	while len(device_ids) > 0:
		print('Force stop current emulatos ...')
		force_stop_emulators()
		device_ids = get_available_device()	
		time.sleep(2)

	print('Starting emulators ...')
	start_emulators(num_devices)
	time.sleep(5)
	device_ids = get_available_device()

	chunked_app_lists = np.array_split(app_list, len(device_ids))
	parameters = []

	for index, working_list in enumerate(chunked_app_lists):
		device_id = device_ids[index]
		parameters.append(PARAMETER(working_list, device_id, auto_restart))

	start_time = time.time()	
	pool = Pool()
	pool.map(run_test, parameters)
	pool.close()
	pool.join()
	print(f'{(time.time() - start_time)}')

if __name__ == '__main__':
	with open('android_config.json') as file:
		config_dict = json.load(file)

	browser_list = list(config_dict.keys())
	browser_list.append('all')

	ap = argparse.ArgumentParser(description='Tester for Android devices')
	ap.add_argument('-browsers', '--browsers', dest='browsers', type=str, required=True, nargs='+', choices=browser_list)
	ap.add_argument('-url_json', '--url_json', default='', type=str, help='Path to a json list of create_repeat tests')
	ap.add_argument('-repeat', '--repeat', default=1, type=int, help='Repeat x times')
	ap.add_argument('-num_devices', '--num_devices', dest='num_devices', type=int)
	ap.add_argument('-type', '--resp_type', choices=['basic', 'debug', 'parsing'], default='basic', help='Specify the response type (default: basic)')
	ap.add_argument('-auto_restart', action='store_true', help='Auto restart')
	
	args = ap.parse_args()

	if 'all' in args.browsers:
		args.browsers = list(config_dict.keys())

	url_dict = dict()
	if args.url_json:
		with open(args.url_json) as file:
			url_dict = json.load(file)		
		
	print(f'Starting test on {args.browsers} ...')	
	main(args.browsers, url_dict, args.repeat, args.num_devices, args.resp_type, args.auto_restart, config_dict)