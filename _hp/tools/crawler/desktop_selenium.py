from multiprocessing import Pool
import sys

from tqdm import tqdm
from utils import TIMEOUT, get_tests, HSTS_DEACTIVATE
from create_browsers import get_or_create_browser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import traceback
import datetime
import argparse
import json
import multiprocessing
from pathlib import Path
from Timeout import SignalTimeout
import logging
import ecs_logging

class CustomTimeout(BaseException):
    pass

class CustomErrorTimeout(SignalTimeout):
    def timeout_handler(self, signum, frame) -> None:
        """Handle timeout (SIGALRM) signal"""
        raise CustomTimeout


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
    # print(options.to_capabilities())
    return driver(options=options, service=service)


def run_task(browser_name, browser_version, binary_location, arguments, debug_input, test_urls, logger: logging.Logger):  
    try:
        url = None
        all_urls = len(test_urls)
        cur_url = 0
        extra = {"browser": browser_name, "browser_version": browser_version, "binary_location": binary_location, "arguments": arguments}

        start = datetime.datetime.now()  
        driver = get_browser(browser_name, browser_version,
                            binary_location, arguments)
        # Max page load timeout
        driver.set_page_load_timeout(TIMEOUT*2)
        logger.info(f"Start {browser_name} ({browser_version})", extra=extra)
        # print(driver.capabilities)
        # Store the ID of the original window
        original_window = driver.current_window_handle
        for url in test_urls:
            try:
                logger.debug(f"Attempting: {url}", extra=extra)
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
                except Exception:
                    logger.error("Switching browser window failed", exc_info=True, extra=extra)
                # Wait until the results are saved on the server (after finishing fetch request, a div with id "finished" is added to the DOM)
                WebDriverWait(driver, TIMEOUT).until(
                    EC.presence_of_element_located((By.ID, "finished")))
                cur_url += 1
            except Exception:
                logger.error(f"Visiting: {url} driver.current_url {driver.current_url} failed", exc_info=True, extra=extra)
            finally:
                # Option to manually debug
                if debug_input:
                    input("Next")
                # Close the current window
                driver.close()
                # Switch back to the old tab or window
                driver.switch_to.window(original_window)
    except Exception:
        logger.error(f"Major Exeception occured! Visited {cur_url}/{all_urls}. Last URL: {url}", exc_info=True, extra=extra)
    except CustomTimeout:
        logger.error(f"CustomTimeout occured! Visited {cur_url}/{all_urls}. Last URL: {url}", exc_info=True, extra=extra)

    finally:
        # Closing the browser should take less than 30s
        with CustomErrorTimeout(30):
            try:
                # Closing twice is necessary for brave; Safari crashes when closing twice, Firefox has some timeout issues here
                if browser_name not in ["safari", "firefox"]:
                    driver.close()
                driver.quit()
            except CustomTimeout:
                logger.error("CustomTimeout while closing the browser", exc_info=True, extra=extra)
            except Exception as e:
                logger.error("Exception while closing the browser", exc_info=True, extra=extra)
            finally:
                logger.info(f"Finish {browser_name} ({browser_version}). Took: {datetime.datetime.now() - start}", extra=extra)


def worker_function(args):
    log_path, browser_name, browser_version, binary_location, arguments, debug_input, test_urls, timeout = args
    
    log_filename = f"{log_path}-{browser_name}-{browser_version}.json"
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(ecs_logging.StdlibFormatter())
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    with CustomErrorTimeout(timeout):
        try:
            run_task(browser_name, browser_version, binary_location, arguments, debug_input, test_urls, logger)
        except (CustomTimeout, Exception):
            logger.error("Fatal outer exception!", exc_info=True)


def setup_process(log_path):
    pass


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
    parser.add_argument("--num_browsers", default=80, type=int, help="How many browsers to start in parallel (max).")
    parser.add_argument("--max_urls_until_restart", default=100, type=int, help="Maximum number of URLs until the browser is restated.")
    parser.add_argument("--timeout_task", default=1000, type=int, help="Timeout for a single task (max_urls_until_restart URLs in one browser) in seconds.")
    args = parser.parse_args()

    # (browser_name, version, binary_location (e.g., for brave), arguments (e.g, for headless), browser_id
    if sys.platform == "darwin":
        config = [
            ("chrome", "120", None, None, get_or_create_browser("chrome", "120", "macOS 14.2.1", "real", "selenium", "")),
            ("firefox", "120", None, None, get_or_create_browser("firefox", "120", "macOS 14.2.1", "real", "selenium", "")),
            ("safari", "17.2.1", None, None, get_or_create_browser("safari", "17.2", "macOS 14.2.1", "real", "selenium", "")),
            ("edge", "120", None, None, get_or_create_browser("edge", "120", "macOS 14.2.1", "real", "selenium", "")),
            # Download .dmg from https://github.com/brave/brave-browser/releases and install
            # E.g., https://github.com/brave/brave-browser/releases/tag/v1.60.118, rename the file
            ("brave", "119", "/Applications/Brave Browser 1.60.118.app/Contents/MacOS/Brave Browser",
             ["--disable-brave-update"], get_or_create_browser("brave", "1.60.118 (119.0.6045.163)", "macOS 14.2.1", "real", "selenium", "")),

            ("chrome", "120", None, ["--headless=new"], get_or_create_browser("chrome", "120", "macOS 14.2.1", "headless-new", "selenium", "")),
            ("firefox", "120", None, ["-headless"], get_or_create_browser("firefox", "120", "macOS 14.2.1", "headless", "selenium", "")),
            # ("safari", "17.2.1", None, None, 4), No Safari headless exist
            ("edge", "120", None, ["--headless=new"], get_or_create_browser("edge", "120", "macOS 14.2.1", "headless-new", "selenium", "")),
            ("brave", "119", "/Applications/Brave Browser 1.60.118.app/Contents/MacOS/Brave Browser",
             ["--headless=new", "--disable-brave-update"], get_or_create_browser("brave", "1.60.118 (119.0.6045.163)", "macOS 14.2.1", "headless-new", "selenium", "")),
        ]
    # Linux Ubuntu
    else:
        config = [
            # Headless (new)
            ("chrome", "119", None, ["--headless=new"], get_or_create_browser("chrome", "119", "Ubuntu 22.04", "headless-new", "selenium", "")),
            ("firefox", "119", None, ["-headless"], get_or_create_browser("firefox", "119", "Ubuntu 22.04", "headless", "selenium", "")),
            # ("safari", "17.0", None, None, 4), No Safari on Linux
            ("edge", "119", None, ["--headless=new"], get_or_create_browser("edge", "119", "Ubuntu 22.04", "headless-new", "selenium", "")),
            # Brave (different version)
            # mkdir ~/brave-versions
            # mkdir ~/brave-versions/brave-version
            # CD into the folder and download *.linux-amd64.zip from https://github.com/brave/brave-browser/releases and unzip
            # The ZIP versions seem to not auto update and one can install as many as wanted (only on linux though?)
            # v1.59.120 (Chromium 118): wget https://github.com/brave/brave-browser/releases/download/v1.59.120/brave-browser-1.59.120-linux-amd64.zip
            # Note: if you specify the wrong chromium version for brave, selenium will ignore the binary location and download CFT instead??
            #("brave", "118", "/home/ubuntu/brave-versions/v1.59.120/brave-browser",
            # ["--headless=new"], get_or_create_browser("brave", "1.59.120 (118.0.5993.88)", "Ubuntu 22.04", "headless-new", "selenium", "")),
            # v1.60.114 (Chromium 119): wget https://github.com/brave/brave-browser/releases/download/v1.60.114/brave-browser-1.60.114-linux-amd64.zip
            ("brave", "119", "/home/ubuntu/brave-versions/v1.60.114/brave-browser",
             ["--headless=new"], get_or_create_browser("brave", "1.60.114 (119.0.6045.124)", "Ubuntu 22.04", "headless-new", "selenium", "")),
            # Headfull
            ("chrome", "119", None, None, get_or_create_browser("chrome", "119", "Ubuntu 22.04", "xvfb", "selenium", "")),
            ("firefox", "119", None, None, get_or_create_browser("firefox", "119", "Ubuntu 22.04", "xvfb", "selenium", "")),
            ("edge", "119", None, None, get_or_create_browser("edge", "119", "Ubuntu 22.04", "xvfb", "selenium", "")),
            #("brave", "118", "/home/ubuntu/brave-versions/v1.59.120/brave-browser", None,
            # get_or_create_browser("brave", "1.59.120 (118.0.5993.88)", "Ubuntu 22.04", "xvfb", "selenium", "")),
            ("brave", "119", "/home/ubuntu/brave-versions/v1.60.114/brave-browser", None,
             get_or_create_browser("brave", "1.60.114 (119.0.6045.124)", "Ubuntu 22.04", "xvfb", "selenium", "")),
        ]
    if args.debug_browsers:
        config = [
            ("brave", "119", "/home/ubuntu/brave-versions/v1.60.114/brave-browser", None,
             get_or_create_browser("brave", "1.60.114 (119.0.6045.124)", "Ubuntu 22.04", "xvfb", "selenium", "")),
            ("firefox", "119", None, None, get_or_create_browser("firefox", "119", "Ubuntu 22.04", "xvfb", "selenium", "")),
        ]

    now = f"{datetime.datetime.now()}"
    log_path = f"logs/desktop-selenium/{now}"
    Path(log_path).mkdir(parents=True, exist_ok=True)

    all_args = []
    for scheme in ["http", "https"]:
        for browser_name, browser_version, binary_location, arguments, browser_id in config:
            if args.run_mode == "run_all":
                test_urls = get_tests(
                    resp_type=args.resp_type, browser_id=browser_id, scheme=scheme)
            elif args.run_mode == "repeat":
                with open("../repeat.json", "r") as f:
                    test_urls = json.load(f).get(str(browser_id), [])
                    test_urls = list(filter(lambda s: s.startswith(f"{scheme}://"), test_urls))
                if not len(test_urls):
                    continue
            else:
                raise Exception(f"Unknown run mode: {args.run_mode}")
        
            url_chunks = [test_urls[i:i + args.max_urls_until_restart] for i in range(0, len(test_urls), args.max_urls_until_restart)]
            for url_chunk in url_chunks:
                all_args.append((log_path, browser_name, browser_version, binary_location, arguments, args.debug_input, url_chunk, args.timeout_task))


    with Pool(processes=args.num_browsers, initializer=setup_process, initargs=(log_path,)) as p:
        r = list(tqdm(p.imap_unordered(worker_function, all_args), total=len(all_args), desc="Header Parsing Progress (URL Chunks)", leave=True, position=0))
        print(r)

    # Headfull (linux):
    # Xvfb :99 -screen 0 1920x1080x24 &
    # x11vnc -display :99 -bg -shared -forever -passwd abc -xkb -rfbport 5900
    # export DISPLAY=:99 && fluxbox -log fluxbox.log &
    # export DISPLAY=:99 && python desktop_selenium.py

    # Alternative idea with grid
    # java -jar selenium-server-4.15.0.jar standalone --selenium-manager True
    # remote_url = "http://localhost:4444/wd/hub"
