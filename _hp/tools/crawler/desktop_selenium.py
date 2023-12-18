import sys
from utils import TIMEOUT, get_tests, HSTS_DEACTIVATE
from create_browsers import get_or_create_browser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import traceback
import datetime
import argparse
import json


class Tee(object):
    def __init__(self, filename, name):
        self.file = open(f"{filename}-{name}.log", 'a')
        self.stdout = sys.stdout
        self.name = name

    def __enter__(self):
        sys.stdout = self
        return self.file

    def __exit__(self, exc_type, exc_value, tb):
        sys.stdout = self.stdout
        if exc_type is not None:
            self.file.write(traceback.format_exc())
        self.file.close()

    def write(self, data):
        if data != "\n" and data != " " and data != "":
            data = f"{datetime.datetime.now()}-{self.name}: {data}"
        self.file.write(data)
        self.stdout.write(data)

    def flush(self):
        self.file.flush()
        self.stdout.flush()


def get_browser(browser: str, version: str, binary_location=None, arguments=None):
    service = None
    if browser in ["chrome", "brave"]:
        options = webdriver.ChromeOptions()
        driver = webdriver.Chrome
        # Optional use different ChromeDriver version!, default is chosen from the given browser_version
        # if browser == "brave":
        #    service = Service("/Applications/chromedriver")
    elif browser == "firefox":
        options = webdriver.FirefoxOptions()
        driver = webdriver.Firefox
    elif browser == "safari":
        options = webdriver.SafariOptions()
        driver = webdriver.Safari
    elif browser == "edge":
        options = webdriver.EdgeOptions()
        driver = webdriver.Edge
    else:
        print(f"Unsupported browser: {browser}")
        return Exception()

    options.browser_version = version
    if binary_location:
        # Possible to specify other browsers e.g., brave
        options.binary_location = binary_location
    if arguments:
        for argument in arguments:
            # ("--headless=new") # Possible to add arguments such as headless
            options.add_argument(argument)
    print(options.to_capabilities())
    return driver(options=options, service=service)


def main(browser_name, browser_version, binary_location, arguments, browser_id, resp_type, run_mode, debug_input):
    
    for scheme in ["http", "https"]:
        if run_mode == "run_all":
            test_urls = get_tests(
                resp_type=resp_type, browser_id=browser_id, scheme=scheme)
        elif run_mode == "repeat":
            with open("../repeat.json", "r") as f:
                test_urls = json.load(f).get(str(browser_id), [])
                test_urls = list(filter(lambda s: s.startswith(f"{scheme}://"), test_urls))
            if not len(test_urls):
                continue
        else:
            raise Exception(f"Unknown run mode: {run_mode}")
        
        driver = get_browser(browser_name, browser_version,
                             binary_location, arguments)
        # Max page load timeout
        driver.set_page_load_timeout(TIMEOUT*2)
        print(f"Start {browser_name} ({browser_version}) ({scheme})")
        print(driver.capabilities)
        # Store the ID of the original window
        original_window = driver.current_window_handle
        try:
            for url in test_urls:
                try:
                    # Create a new window for each test/URL; another option would be to restart the driver for each test but that is even slower
                    driver.switch_to.new_window('window')
                    new_window = driver.current_window_handle
                    if "upgrade" in url:
                        driver.get(HSTS_DEACTIVATE)
                    driver.get(url)
                    # print(driver.title)
                    # Switch back to the original window (if the test opens new ones)
                    # Only required on firefox; Brave does not like it
                    try:
                        if browser_name == "firefox":
                            driver.switch_to.window(new_window)
                    except Exception as e:
                        print("Switch failed:", e)
                    # Wait until the results are saved on the server (after finishing fetch request, a div with id "finished" is added to the DOM)
                    WebDriverWait(driver, TIMEOUT).until(
                        EC.presence_of_element_located((By.ID, "finished")))
                except Exception as e:
                    print("Exception!", e)
                    print(driver.current_url)
                    print(url)
                finally:
                    # Option to manualy debug
                    if debug_input:
                        input("Next")
                    # Close the current window
                    driver.close()
                    # Switch back to the old tab or window
                    driver.switch_to.window(original_window)
        except Exception as e:
            print("Major Exception occured!", e)
        finally:
            try:
                # Quit will fail with the additional close in safari?
                if browser_name != "safari":
                    driver.close()
                driver.quit()
            except Exception as e:
                print(f"Failed quitting the browser", e)
            print(f"Finish {browser_name} ({browser_version}) ({scheme})")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run tests on Desktop Selenium.")
    parser.add_argument("--resp_type", choices=["basic", "debug", "parsing"], default="basic",
                        help="Specify the response type (default: basic)")
    parser.add_argument("--debug_browsers", action="store_true",
                        help="Toggle on debugging for browser selection")
    parser.add_argument("--debug_input", action="store_true",
                        help="Toggle on debugging for input(Next) during the run.")
    parser.add_argument("--run_mode", choices=["run_all", "repeat"], default="run_all",
                        help="Specify the mode (default: run_all)")
    args = parser.parse_args()

    # (browser_name, version, binary_location (e.g., for brave), arguments (e.g, for headless), browser_id)
    if sys.platform == "darwin":
        config = [
            ("chrome", "120", None, None, get_or_create_browser("chrome", "120", "macOS 14.2", "real", "Selenium", "")),
            ("firefox", "120", None, None, get_or_create_browser("firefox", "120", "macOS 14.2", "real", "Selenium", "")),
            ("safari", "17.2", None, None, get_or_create_browser("safari", "17.2", "macOS 14.2", "real", "Selenium", "")),
            ("edge", "120", None, None, get_or_create_browser("edge", "120", "macOS 14.2", "real", "Selenium", "")),
            # Download .dmg from https://github.com/brave/brave-browser/releases and install
            # E.g., https://github.com/brave/brave-browser/releases/tag/v1.60.118, rename the file
            ("brave", "119", "/Applications/Brave Browser 1.60.118.app/Contents/MacOS/Brave Browser",
             ["--disable-brave-update"], get_or_create_browser("brave", "1.60.118 (119.0.6045.163)", "macOS 14.2", "real", "Selenium", "")),

            ("chrome", "120", None, ["--headless=new"], get_or_create_browser("chrome", "120", "macOS 14.2", "headless-new", "Selenium", "")),
            ("firefox", "120", None, ["-headless"], get_or_create_browser("firefox", "120", "macOS 14.2", "headless", "Selenium", "")),
            # ("safari", "17.0", None, None, 4), No Safari headless exist
            ("edge", "120", None, ["--headless=new"], get_or_create_browser("edge", "120", "macOS 14.2", "headless-new", "Selenium", "")),
            ("brave", "119", "/Applications/Brave Browser 1.60.118.app/Contents/MacOS/Brave Browser",
             ["--headless=new"], get_or_create_browser("brave", "1.60.118 (119.0.6045.163)", "macOS 14.2", "headless-new", "Selenium", "")),
        ]
    # Linux Ubuntu
    else:
        config = [
            # Headless (new)
            ("chrome", "119", None, ["--headless=new"], get_or_create_browser("chrome", "119", "Ubuntu 22.04", "headless-new", "Selenium", "")),
            ("firefox", "119", None, ["-headless"], get_or_create_browser("firefox", "119", "Ubuntu 22.04", "headless", "Selenium", "")),
            # ("safari", "17.0", None, None, 4), No Safari on Linux
            ("edge", "119", None, ["--headless=new"], get_or_create_browser("edge", "119", "Ubuntu 22.04", "headless-new", "Selenium", "")),
            # Brave (different version)
            # mkdir ~/brave-versions
            # mkdir ~/brave-versions/brave-version
            # CD into the folder and download *.linux-amd64.zip from https://github.com/brave/brave-browser/releases and unzip
            # The ZIP versions seem to not auto update and one can install as many as wanted (only on linux though?)
            # v1.59.120 (Chromium 118): wget https://github.com/brave/brave-browser/releases/download/v1.59.120/brave-browser-1.59.120-linux-amd64.zip
            # Note: if you specify the wrong chromium version, selenium will ignore the binary location and download CFT instead??
            ("brave", "118", "/home/ubuntu/brave-versions/v1.59.120/brave-browser",
             ["--headless=new"], get_or_create_browser("brave", "1.59.120 (118.0.5993.88)", "Ubuntu 22.04", "headless-new", "Selenium", "")),
            # v1.60.114 (Chromium 119): wget https://github.com/brave/brave-browser/releases/download/v1.60.114/brave-browser-1.60.114-linux-amd64.zip
            ("brave", "119", "/home/ubuntu/brave-versions/v1.60.114/brave-browser",
             ["--headless=new"], get_or_create_browser("brave", "1.60.114 (119.0.6045.124)", "Ubuntu 22.04", "headless-new", "Selenium", "")),
            # Headfull
            ("chrome", "119", None, None, get_or_create_browser("chrome", "119", "Ubuntu 22.04", "xvfb", "Selenium", "")),
            ("firefox", "119", None, None, get_or_create_browser("firefox", "119", "Ubuntu 22.04", "xvfb", "Selenium", "")),
            ("edge", "119", None, None, get_or_create_browser("edge", "119", "Ubuntu 22.04", "xvfb", "Selenium", "")),
            ("brave", "118", "/home/ubuntu/brave-versions/v1.59.120/brave-browser", None,
             get_or_create_browser("brave", "1.59.120 (118.0.5993.88)", "Ubuntu 22.04", "xvfb", "Selenium", "")),
            ("brave", "119", "/home/ubuntu/brave-versions/v1.60.114/brave-browser", None,
             get_or_create_browser("brave", "1.60.114 (119.0.6045.124)", "Ubuntu 22.04", "xvfb", "Selenium", "")),
        ]
    if args.debug_browsers:
        config = [
            ("brave", "119", "/home/ubuntu/brave-versions/v1.60.114/brave-browser", None,
             get_or_create_browser("brave", "1.60.114 (119.0.6045.124)", "Ubuntu 22.04", "xvfb", "Selenium", "")),
            ("firefox", "119", None, None, get_or_create_browser("firefox", "119", "Ubuntu 22.04", "xvfb", "Selenium", "")),
        ]

    now = f"{datetime.datetime.now()}"
    print(config)
    for t in config:
        with Tee("desktop-selenium", now) as f:
            main(*t, args.resp_type, args.run_mode, args.debug_input)

    # Headfull (linux):
    # Xvfb :99 -screen 0 1920x1080x24 &
    # x11vnc -display :99 -bg -shared -forever -passwd abc -xkb -rfbport 5900
    # export DISPLAY=:99 && fluxbox -log fluxbox.log &
    # export DISPLAY=:99 && python desktop_selenium.py

    # Alternative idea with grid
    # java -jar selenium-server-4.15.0.jar standalone --selenium-manager True
    # remote_url = "http://localhost:4444/wd/hub"
