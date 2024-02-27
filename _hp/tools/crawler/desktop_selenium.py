import glob
from multiprocessing import Pool
import multiprocessing
import os
import re
import shutil
import sys
import time

from tqdm import tqdm
from utils import TIMEOUT, generate_short_uuid, get_tests, HSTS_DEACTIVATE, create_test_page_runner
from create_browsers import get_or_create_browser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime
import argparse
import json
from pathlib import Path
from Timeout import SignalTimeout
import logging
import ecs_logging
import psutil


class CustomTimeout(BaseException):
    pass


class CustomErrorTimeout(SignalTimeout):
    def timeout_handler(self, signum, frame) -> None:
        """Handle timeout (SIGALRM) signal"""
        raise CustomTimeout


def get_child_processes(parent_pid):
    try:
        # Get the process by PID
        parent_process = psutil.Process(parent_pid)

        # Get all child processes
        child_processes = parent_process.children(recursive=True)
        child_processes.append(parent_process)
        return child_processes
    except psutil.NoSuchProcess:
        return []
    

def kill_processes(pid_list):
    for process in pid_list:
        try:
            process.terminate()
        except psutil.NoSuchProcess:
            pass
    
    try:
        psutil.wait_procs(pid_list, timeout=5)
    except psutil.NoSuchProcess:
        pass

    for process in pid_list:
        try:
            if process.is_running():
                process.kill()
        except psutil.NoSuchProcess:
            pass


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
        # Problem: "Could not create a session: The Safari instance is already paired with another WebDriver session"
        # Idea: use different ports for each driver, however that does not work with the current version anymore (https://developer.apple.com/documentation/webkit/about_webdriver_for_safari#2957226)
        # port = 5555
        # service = webdriver.SafariService(port=port)
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


def path_age(path):
    """Returns when a path was last modified in seconds"""
    return time.time() - os.path.getmtime(path)


def clean_dirs(timeout):
    """Remove old directories."""
    selenium_dirs = glob.glob("/tmp/rust_*")
    selenium_dirs.extend(glob.glob("/tmp/Temp-*"))
    selenium_dirs.extend(glob.glob("/tmp/.org.chromium.*"))
    selenium_dirs.extend(glob.glob("/tmp/.com.microsoft.*"))

    for dir in selenium_dirs:
        try:
            age = path_age(dir)
            if age > timeout:
                shutil.rmtree(dir, ignore_errors=True)
                Path(dir).unlink(missing_ok=True)
        except Exception:
            pass


def run_task(browser_name, browser_version, binary_location, arguments, debug_input, test_urls, logger: logging.Logger, page_timeout):  
    try:
        url = None
        processes = []
        all_urls = len(test_urls)
        cur_url = 0
        extra = {"browser": browser_name, "browser_version": browser_version, "binary_location": binary_location, "arguments": arguments}
        logger.info(f"Start {browser_name} ({browser_version})", extra=extra)
        start = datetime.datetime.now()  
        driver = get_browser(browser_name, browser_version,
                            binary_location, arguments)
        processes = get_child_processes(driver.service.process.pid)
        # Max page load timeout
        driver.set_page_load_timeout(2 * page_timeout)
        # print(driver.capabilities)
        # Store the ID of the original window
        original_window = driver.current_window_handle
        for url in test_urls:
            try:
                driver.set_window_position(-5000, 0)  # Posititon the window off-screen (necessary on macOS such that the device stays more or less usable)
                logger.debug(f"Attempting: {url}", extra=extra)
                # Create a new window for each test/URL; another option would be to restart the driver for each test but that is even slower
                driver.switch_to.new_window('window')
                driver.set_window_position(-5000, 0)  # Posititon the new window off-screen as well
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
                WebDriverWait(driver, page_timeout).until(
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
        logger.error(f"Major Exception occured! Visited {cur_url}/{all_urls}. Last URL: {url}", exc_info=True, extra=extra)
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
            except UnboundLocalError:
                # driver = get_browser(...) failed, we do not have to log it again
                pass
            except CustomTimeout:
                logger.error("CustomTimeout while closing the browser", exc_info=True, extra=extra)
            except Exception:
                logger.error("Exception while closing the browser", exc_info=True, extra=extra)
            finally:
                logger.info(f"Finish {browser_name} ({browser_version}). Took: {datetime.datetime.now() - start}", extra=extra)
                return processes



def worker_function(args):
    log_path, browser_name, browser_version, binary_location, arguments, debug_input, test_urls, timeout, page_timeout = args
    
    log_filename = f"{log_path}-{browser_name}-{browser_version}.json"
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(ecs_logging.StdlibFormatter())
    logger = logging.getLogger(__name__)
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    processes = []
    with CustomErrorTimeout(timeout):
        try:
            processes = run_task(browser_name, browser_version, binary_location, arguments, debug_input, test_urls, logger, page_timeout)
        except (CustomTimeout, Exception):
            logger.error("Fatal outer exception!", exc_info=True)
    
    # Sometimes driver.quit and similar do not work, thus we kill the processes explicitely once again
    # Another approach would be to have a separate watchdog process to kill stale drivers + browsers
    kill_processes(processes)
    # They also fail to remove all temp directories thus we remove them manually
    clean_dirs(timeout)
    # We only want to have one log handler per process
    logger.removeHandler(file_handler)


def setup_process(log_path):
    # Slowly start all processes, one new every second
    name = multiprocessing.current_process().name
    num = int(name.rsplit("-", maxsplit=1)[1]) - 1
    time.sleep(num)  

log_path = f"logs/desktop-selenium/"
Path(log_path).mkdir(parents=True, exist_ok=True)
file_handler = logging.FileHandler(f"logs/desktop-selenium/{datetime.datetime.now().date().strftime('%Y-%m-%d')}_unraisable.json")
file_handler.setFormatter(ecs_logging.StdlibFormatter())

# Set up logging to a file with the specified level and handler
logging.basicConfig(level=logging.ERROR, handlers=[file_handler])

def unraisable_hook(unraisable):
    """Log unraisable exceptions to a file"""
    for item in unraisable:
        logging.error(f"Unraisable exception: {item}")

# Set the unraisable hook globally
sys.unraisablehook = unraisable_hook

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
    parser.add_argument("--num_browsers", default=60, type=int, help="How many browsers to start in parallel (max).")
    parser.add_argument("--max_urls_until_restart", default=100, type=int, help="Maximum number of URLs until the browser is restated.")
    parser.add_argument("--timeout_task", default=1000, type=int, help="Timeout for a single task (max_urls_until_restart URLs in one browser) in seconds.")
    parser.add_argument("--gen_page_runner", action="store_true", help="Toggle the generate test-page runner mode.")
    parser.add_argument("--page_runner_json", default="", type=str, help="Path to a json list of page_runner URLs to visit")
    parser.add_argument("--max_resps", default=10, type=int, help="Maximum number of responses per parsing test URL")
    parser.add_argument("--max_popups", default=100, type=int, help="Maximum number of popus per test URL")
    args = parser.parse_args()

    # (browser_name, version, binary_location (e.g., for brave), arguments (e.g, for headless), browser_id
    if sys.platform == "darwin":
        # Only run Safari (headfull as no headless mode exists)
        # Initial experiments showed almost no differences between Linux and macOS versions of brave, chrome, firefox
        config = [
            # Released 2024-01-22 (17.3 (19617.2.4.11.8))
            ("safari", "17.3", None, None, get_or_create_browser("safari", "17.3", "macOS 14.3", "real", "selenium", "")),
            
            # Brave without updates on MacOS
            # Download .dmg from https://github.com/brave/brave-browser/releases and install
            # E.g., https://github.com/brave/brave-browser/releases/tag/v1.60.118, rename the file, run with --disable-brave-updage
            # ("brave", "119", "/Applications/Brave Browser 1.60.118.app/Contents/MacOS/Brave Browser",
            # ["--headless=new", "--disable-brave-update"], get_or_create_browser("brave", "1.60.118 (119.0.6045.163)", "macOS 14.2.1", "headless-new", "selenium", "")),
        ]
    # Linux Ubuntu
    else:
        # Initial experiments revealed that there are no differences between --headless=new and Xvfb for Chromium-based browsers and -headless and Xvfb for Firefox
        # As headless browsers are faster, less resource intensive, and more stable we decided to only test headless versions!
        # (One exception is download handling in brave where there is a small difference between brave headless and headfull)
            
        # Headless (new)
        config = [
            # Major browsers (managed by Selenium itself)
            # Released 2024-01-17
            # Chrome, Edge, and Brave all use the same Chromium version! I.e., we test differences between them and not between Chromium versions! (which initial tests showed to be larger?)
            ("chrome", "121", None, ["--headless=new"], get_or_create_browser("chrome", "121", "Ubuntu 22.04", "headless-new", "selenium", "")),
            # Released 2024-01-23
            ("firefox", "122", None, ["-headless"], get_or_create_browser("firefox", "122", "Ubuntu 22.04", "headless", "selenium", "")),
            # Released 2024-01-25
            ("edge", "121", None, ["--headless=new"], get_or_create_browser("edge", "121", "Ubuntu 22.04", "headless-new", "selenium", "")),
            
            # To compare between versions use additional chrome and firefox versions
            # Released 2024-02-14
            ("chrome", "122", None, ["--headless=new"], get_or_create_browser("chrome", "122", "Ubuntu 22.04", "headless-new", "selenium", "")),
            # Released 2023-11-29
            ("chrome", "120", None, ["--headless=new"], get_or_create_browser("chrome", "120", "Ubuntu 22.04", "headless-new", "selenium", "")),
            # Released 2023-12-19
            ("firefox", "121", None, ["-headless"], get_or_create_browser("firefox", "121", "Ubuntu 22.04", "headless", "selenium", "")),


            # Brave (setup for a concrete version managed manually)
            # mkdir ~/brave-versions
            # mkdir ~/brave-versions/brave-version
            # CD into the folder and download *.linux-amd64.zip from https://github.com/brave/brave-browser/releases and unzip
            # The ZIP versions does not auto update and one can install as many as wanted (on Linux)
            # Note: if you specify the wrong chromium version, selenium will ignore the binary location (brave) and instead use CFT
            # v1.62.156 (Chromium 121): wget https://github.com/brave/brave-browser/releases/download/v1.62.156/brave-browser-1.62.156-linux-amd64.zip
            # Latest as of 2024-02-05
            ("brave", "121", "/home/ubuntu/brave-versions/v1.62.156/brave-browser",
             ["--headless=new"], get_or_create_browser("brave", "v1.62.156 (121.0.6167.139)", "Ubuntu 22.04", "headless-new", "selenium", "")),
        ]  
        # Headfull option
        use_headfull = False
        if use_headfull:
                config = config + [
                    ("chrome", "119", None, None, get_or_create_browser("chrome", "119", "Ubuntu 22.04", "xvfb", "selenium", "")),
                    ("firefox", "119", None, None, get_or_create_browser("firefox", "119", "Ubuntu 22.04", "xvfb", "selenium", "")),
                    ("edge", "119", None, None, get_or_create_browser("edge", "119", "Ubuntu 22.04", "xvfb", "selenium", "")),
                    ("brave", "119", "/home/ubuntu/brave-versions/v1.60.114/brave-browser", None,
                    get_or_create_browser("brave", "1.60.114 (119.0.6045.124)", "Ubuntu 22.04", "xvfb", "selenium", ""))
                ]
    
    if args.debug_browsers:
        config = [
            ("firefox", "119", None, None, get_or_create_browser("firefox", "119", "Ubuntu 22.04", "xvfb", "selenium", "")),
        ]

    if args.gen_page_runner:
        config = [("Unknown", "Unknown", None, None, get_or_create_browser("Unknown", "Unknown", "Unknown", "real", "manual", None))]

    now = f"{datetime.datetime.now()}"
    log_path = f"logs/desktop-selenium/{now}"

    all_args = []
    url_list = []
    rand_token = generate_short_uuid()
    chunk_id = 0
    if args.page_runner_json != "":
        with open(args.page_runner_json, "r") as f:
            urls = json.load(f)
        all_args = []
        assert(len(config) == 1)
        browser_name, browser_version, binary_location, arguments, browser_id = config[0]
        for url in urls:
            assert(int(re.findall("runner-(\d+)", url)[0]) == 1)
            url = url + f"?browser_id={browser_id}"
            all_args.append((log_path, browser_name, browser_version, binary_location, arguments, args.debug_input, [url], args.timeout_task, args.timeout_task-60))
    else:
        for scheme in ["http", "https"]:
            for browser_name, browser_version, binary_location, arguments, browser_id in config:
                if args.run_mode == "run_all":
                    test_urls = get_tests(resp_type=args.resp_type, browser_id=browser_id, scheme=scheme, max_resps=args.max_resps, max_popups=args.max_popups)
                    page_timeout = TIMEOUT
                elif args.run_mode == "repeat":
                    with open("../repeat.json", "r") as f:
                        test_urls = json.load(f).get(str(browser_id), [])
                        test_urls = list(filter(lambda s: s.startswith(f"{scheme}://"), test_urls))
                        page_timeout = 3 * TIMEOUT
                    if not len(test_urls):
                        continue
                else:
                    raise Exception(f"Unknown run mode: {args.run_mode}")
            
                url_chunks = [test_urls[i:i + args.max_urls_until_restart] for i in range(0, len(test_urls), args.max_urls_until_restart)]
                for url_chunk in url_chunks:
                    all_args.append((log_path, browser_name, browser_version, binary_location, arguments, args.debug_input, url_chunk, args.timeout_task, page_timeout))
                    if args.gen_page_runner:
                        url_list.append(create_test_page_runner(browser_id, f"{rand_token}-{chunk_id}", url_chunk))
                        chunk_id += 1

    if args.gen_page_runner:
        print(f"URLs to visit: {url_list}")
        with open(f"{args.resp_type}-MaxURLs{args.max_urls_until_restart}-MaxResps{args.max_resps}-MaxPopups{args.max_popups}-{rand_token}.json", "w") as f:
            json.dump(url_list, f)
    else:
        with Pool(processes=args.num_browsers, initializer=setup_process, initargs=(log_path,)) as p:
            r = list(tqdm(p.imap_unordered(worker_function, all_args), total=len(all_args), desc="Header Parsing Progress (URL Chunks)", leave=True, position=0))
            # print(r)

    # Headfull (linux):
    # Xvfb :99 -screen 0 1920x1080x24 &
    # x11vnc -display :99 -bg -shared -forever -passwd abc -xkb -rfbport 5900
    # export DISPLAY=:99 && fluxbox -log fluxbox.log &
    # export DISPLAY=:99 && python desktop_selenium.py

    # Alternative idea with grid
    # java -jar selenium-server-4.15.0.jar standalone --selenium-manager True
    # remote_url = "http://localhost:4444/wd/hub"
