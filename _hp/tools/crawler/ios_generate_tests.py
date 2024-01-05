import json
import argparse
import os
import sys
import time
import shutil

from pathlib import Path
import numpy as np

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
HOME_PATH = str(Path.home())
MODE = 'basic'

from utils import get_tests, get_or_create_browser, TIMEOUT

HTML_TEMPLATE = "ios-test-template.html"

def main():    
	browser_list = [('chrome', '120.0.6099.119'), ('brave', '1.61 (23.12.18.22)'), ('opera', '4.4.1 (0)'), ('firefox', '121.0 (36782)'), ('safari', '17'), ('operagx', '2.2.2'), ('edge', '120.0.2210.116')]	
	
	if os.path.isdir('html'):
		shutil.rmtree('html')	
	os.mkdir('html')

	for browser_name, browser_version in browser_list:		
		browser_id = get_or_create_browser(browser_name, browser_version, 'iPadOS 17.2', 'real', 'intent', '')	
			
		test_urls = list()
		for scheme in ["http", "https"]:			
			tests = get_tests(resp_type = MODE, browser_id = browser_id, scheme = scheme, max_popups = 1)			
			test_urls.extend(tests)
	
		with open(HTML_TEMPLATE) as file:
			html_template = file.read()
			html_template = html_template.replace('$$$URLS$$$', json.dumps(test_urls))
			html_template = html_template.replace('$$$TIMEOUT$$$', str(TIMEOUT*1000))

		with open(f'html/test-{browser_name}.html', 'w') as file:
			file.write(html_template)

if __name__ == '__main__':
	main()

# iphone: 00008101-001429080CF9001E
# ipad 3: 00008101-000815DA1A38001E
# ipad 2: 00008101-000E212C1AB8001E
# ipad 1: 00008101-000A50922189003A