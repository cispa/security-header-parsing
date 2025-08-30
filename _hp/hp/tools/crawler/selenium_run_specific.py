from hp.tools.crawler.utils import get_or_create_browser
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from hp.tools.crawler.desktop_selenium import get_browser
import json


def run_specific(url, browser_name, browser_version, binary_location, arguments):
    """Visit a specific test in a given browser configuration.

    Args:
        url (str): A full test URL
        browser_name (str): Name of the browser
        browser_version (str): Version of the browser
        binary_location (str): Location of the browser binary (optional)
        arguments (List[str]): Arguments to the selenium browser launch
    """
    driver = get_browser(browser_name, browser_version,
                        binary_location, arguments)
    original_window = driver.current_window_handle
    driver.get(url)
    driver.switch_to.window(original_window)

    # Wait 5 seconds or until the "finished" div is added
    WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "finished")))

    print(f"Visited, {browser_name}")
    driver.close()

try:
	wpt_config = json.load(open("/app/_hp/wpt-config.json"))
except OSError:
	try:
		wpt_config = json.load(open("../../wpt-config.json"))
	except OSError:
		wpt_config = json.load(open("../../../wpt-config.json"))
base_host = wpt_config["browser_host"]

if __name__ == "__main__":
    # Configure URL and Browser to visit for manual verification/testing
    url = f"http://sub.{base_host}/_hp/tests/referrer-access-rp.sub.html?resp_type=basic&browser_id=1&label=RP&first_id=199&last_id=199&scheme=http&t_resp_id=199&t_element_relation=iframe_window.open&t_resp_origin=http://sub.{base_host}"
    config = [
        # Browsers (managed by Selenium itself)
        # Released 2024-01-23
        ("firefox", "122", None, ["-headless"], get_or_create_browser("firefox", "122", "Ubuntu 22.04", "headless", "selenium", "")),
    ]
    for (browser_name, browser_version, binary_location, arguments, _) in config:
        print(browser_name)
        run_specific(url, browser_name, browser_version, binary_location, arguments)
