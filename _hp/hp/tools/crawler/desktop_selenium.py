import glob
import multiprocessing
import os
import re
import shutil
import sys
import time
import logging
import ecs_logging
import psutil
import datetime
import argparse
import json
from multiprocessing import Pool
from pathlib import Path
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import WebDriverException

from hp.tools.crawler.utils import TIMEOUT, generate_short_uuid, get_tests, HSTS_DEACTIVATE, create_test_page_runner, get_or_create_browser
from hp.tools.crawler.Timeout import SignalTimeout


class CustomTimeout(BaseException):
    """Custom Exception such that we can catch only this one."""
    pass


class CustomErrorTimeout(SignalTimeout):
    """Custom SignalTimeout that throws our CustomTimeout Exception"""
    def timeout_handler(self, signum, frame) -> None:
        """Handle timeout (SIGALRM) signal"""
        raise CustomTimeout


def get_child_processes(parent_pid):
    """Get all child processes for a given parent_pid

    Args:
        parent_pid (str): PID of a program

    Returns:
        List[str]: List of child PIDs
    """
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
    """Kill all processes in pid_list.
    First use terminate, then use kill if not successful.

    Args:
        pid_list (List[str]): List of PIDs
    """
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
    """Start a browser and return the corresponding driver.

    Args:
        browser (str): Name of the browser
        version (str): Versino of the browser
        binary_location (str, optional): Binary location of the browser, if not given managed by Selenium. Defaults to None.
        arguments (List[str], optional): Additional arguments to the browser such as headless. Defaults to None.

    Returns:
        driver: Selenium WebDriver instance
    """
    service = None
    if browser in ["chrome", "brave"]:
        options = webdriver.ChromeOptions()
        driver = webdriver.Chrome
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
        return Exception(f"Unsupported browser: {browser}")

    options.browser_version = version
    if binary_location:
        # Possible to specify other browsers e.g., brave
        options.binary_location = binary_location
    if arguments:
        for argument in arguments:
            # ("--headless=new") # Possible to add arguments such as headless
            options.add_argument(argument)
    # Start the browser and return the driver
    return driver(options=options, service=service)


def path_age(path):
    """Returns when a path was last modified in seconds"""
    return time.time() - os.path.getmtime(path)


def clean_dirs(timeout):
    """Remove old directories (last modified > timeout)."""
    # Directories created by Selenium Drivers/Browsers that are sometimes not cleaned up correctly
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
    """Visit given test_urls in the correct browser and settings

    Args:
        browser_name (str): Name of the browser
        browser_version (str): Version of the browser
        binary_location (str): Optional binary location of the browser
        arguments (List[str]): Optional arguments of the browser (such as headless)
        debug_input (bool): If True, pauses after each visited URl, default=False
        test_urls (List[str]): List of URLs to visit
        logger (logging.Logger): Logger instance to log output to
        page_timeout (int): How long to wait after a page is loaded; Max page load timeout is 2xpage_timeout

    Returns:
        List[str]: List of openend processes (such that they can be killed later if they were not correctly closed by Selenium)
    """
    try:
        url = None
        processes = []
        all_urls = len(test_urls)
        cur_url = 0
        extra = {"browser": browser_name, "browser_version": browser_version, "binary_location": binary_location, "arguments": arguments}
        logger.info(f"Start {browser_name} ({browser_version})", extra=extra)
        start = datetime.datetime.now()

        # Try getting a driver
        try:
            driver = get_browser(browser_name, browser_version,
                            binary_location, arguments)
        except (WebDriverException, OSError):
            logger.error(f"First get_browser failed.", exc_info=True, extra=extra)
            # Try twice (sometimes Safari fails the first attempt and succeeds for the second)
            driver = get_browser(browser_name, browser_version,
                            binary_location, arguments)

        processes = get_child_processes(driver.service.process.pid)
        # Set the max page load timeout
        driver.set_page_load_timeout(2 * page_timeout)
        # Store the ID of the original window
        original_window = driver.current_window_handle
        # Visit all test_urls
        for url in test_urls:
            try:
                # Position the window off-screen (necessary for macOS headfull mode, such that the device stays more or less usable)
                driver.set_window_position(-5000, 0)
                logger.debug(f"Attempting: {url}", extra=extra)
                # Create a new window for each test URL
                driver.switch_to.new_window('window')
                # Position the new window off-screen as well
                driver.set_window_position(-5000, 0)
                new_window = driver.current_window_handle
                # Visit a URL that deactivates HSTS for HSTS related tests
                if "upgrade" in url:
                    driver.get(HSTS_DEACTIVATE)
                driver.get(url)

                # Switch back to the original window (if the test opens new ones)
                # Required on firefox; can fail in some browsers
                try:
                    if browser_name == "firefox":
                        driver.switch_to.window(new_window)
                except Exception:
                    logger.error("Switching browser window failed", exc_info=True, extra=extra)

                # Normal mode: get test timeout from URL
                if not "test-page-runner" in url:
                    url_timeout = int(re.search("timeout=(\d+)", url)[1])
                # test-page-runner mode for MacOS: page_timeout == timeout
                else:
                    url_timeout = 0
                timeout = max(page_timeout, url_timeout+2)

                # Wait until the results are saved on the server (after finishing fetch request, a div with id "finished" is added to the DOM)
                WebDriverWait(driver, timeout).until(
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
    """Helper function to execute run_task in different worker processes.

    Args:
        args (**kwargs): log_path, browser_name, browser_version, binary_location, arguments, debug_input, test_urls, timeout, page_timeout
    """
    # Extract arguments
    log_path, browser_name, browser_version, binary_location, arguments, debug_input, test_urls, timeout, page_timeout = args

    # Setup logging
    log_filename = f"{log_path}-{browser_name}-{browser_version}.json"
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(ecs_logging.StdlibFormatter())
    logger = logging.getLogger(__name__)
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    processes = []
    # Execute run_task with a Timeout of timeout
    with CustomErrorTimeout(timeout):
        try:
            processes = run_task(browser_name, browser_version, binary_location, arguments, debug_input, test_urls, logger, page_timeout)
        except (CustomTimeout, Exception):
            logger.error("Fatal outer exception!", exc_info=True)

    # Sometimes driver.quit and similar do not work correctly, thus we kill the processes explicitely once again
    kill_processes(processes)
    # They can also fail to remove all temp directories thus we remove them manually
    clean_dirs(timeout)
    # We have to remove the file_handler if the process is reused
    logger.removeHandler(file_handler)


def setup_process(log_path):
    """Setup function for each process

    Args:
        log_path (str): Path of dir where to log to.
    """
    # Slowly start all processes, one new every second
    name = multiprocessing.current_process().name
    num = int(name.rsplit("-", maxsplit=1)[1]) - 1
    time.sleep(num)


def unraisable_hook(unraisable):
    """Log unraisable exceptions to a file"""
    for item in unraisable:
        logging.error(f"Unraisable exception: {item}")


# Set up logging to a file with the specified level and handler
log_path = f"logs/desktop-selenium/"
Path(log_path).mkdir(parents=True, exist_ok=True)
file_handler = logging.FileHandler(f"logs/desktop-selenium/{datetime.datetime.now().date().strftime('%Y-%m-%d')}_unraisable.json")
file_handler.setFormatter(ecs_logging.StdlibFormatter())
logging.basicConfig(level=logging.ERROR, handlers=[file_handler])
# Set the unraisable hook globally
sys.unraisablehook = unraisable_hook

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run tests on Desktop Selenium.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # General arguments
    parser.add_argument("--resp_type", choices=["basic", "debug", "parsing"], default="basic",
                        help="Specify the response type")
    parser.add_argument("--debug_browsers", action="store_true",
                        help="Toggle on to use debug browsers only")
    parser.add_argument("--debug_input", action="store_true",
                        help="Toggle on debugging to wait for user input between each URL.")
    parser.add_argument("--ignore_certs", action="store_true",
                        help="Ignore certificate errors (necessary for local/debug run)")
    parser.add_argument("--run_mode", choices=["run_all", "repeat"], default="run_all",
                        help="Specify the run_mode. If run_all all tests are executed, if repeat only the ones in ../repeat.json.")
    parser.add_argument("--num_browsers", default=60, type=int, help="How many browsers to start in parallel at most.")
    parser.add_argument("--max_urls_until_restart", default=100, type=int, help="Maximum number of URLs until the browser is restarted.")
    parser.add_argument("--timeout_task", default=1500, type=int, help="Timeout for a single task in seconds (max_urls_until_restart URLs in one browser).")
    parser.add_argument("--max_resps", default=10, type=int, help="Maximum number of responses per parsing test URL")
    parser.add_argument("--max_popups", default=100, type=int, help="Maximum number of popus per test URL")
    # Arguments for the test-page-runner mode (generation or execution)
    parser.add_argument("--gen_page_runner", action="store_true", help="Toggle the generate test-page-runner mode.")
    parser.add_argument("--gen_multiplier", default=1, type=int, help="How often to include each URL in the test-page-runner page.")
    parser.add_argument("--page_runner_json", default="", type=str, help="Path to a json list of generated test-page-runner URLs to visit")
    parser.add_argument("--new_browsers", action="store_true",
                        help="Toggle on to use the set of newer browsers")
    args = parser.parse_args()

    # Browser Config:
    # (browser_name, version, binary_location (e.g., for brave), arguments (e.g, for headless), browser_id)
    # MacOS
    if sys.platform == "darwin":
        config = [
            # Only run Safari (headfull as no headless mode exists)
            # Released 2024-01-22 (17.3 (19617.2.4.11.8))
            # ("safari", "17.3.1", None, None, get_or_create_browser("safari", "17.3.1", "macOS 14.3.1", "real", "selenium", "")),
            # Released 2024-05-13 (17.5 (19618.2.12))
            ("safari", "17.5", None, [], get_or_create_browser("safari", "17.5", "macOS 14.5", "real", "selenium", "")),


            # Brave without updates on MacOS
            # Download .dmg from https://github.com/brave/brave-browser/releases and install
            # E.g., https://github.com/brave/brave-browser/releases/tag/v1.60.118, rename the file, run with --disable-brave-updage
            # Version has to be the major version of the corresponding chromium version to select the correct driver
            # ("brave", "119", "/Applications/Brave Browser 1.60.118.app/Contents/MacOS/Brave Browser",
            # ["--headless=new", "--disable-brave-update"], get_or_create_browser("brave", "1.60.118 (119.0.6045.163)", "macOS 14.2.1", "headless-new", "selenium", "")),
        ]
        if args.new_browsers:
            config = [
                # Released 2024-12-11 (18.2 (20620.1.16.11.8))
                ("safari", "18.2", None, [], get_or_create_browser("safari", "18.2", "macOS 15.2", "real", "selenium", "")),
            ]
    # Linux Ubuntu
    else:
        # Headless (new)
        config = [
            # Major browsers (managed by Selenium itself)
            # Released 2024-01-17
            # Chrome, Edge, and Brave all use the same Chromium version! I.e., we test differences between them and not between Chromium versions! (which initial tests showed to be larger?)
            ("chrome", "121", None, ["--headless=new"], get_or_create_browser("chrome", "121", "Ubuntu 22.04", "headless-new", "selenium", "")),
            # Released 2024-01-23
            ("firefox", "122", None, ["-headless"], get_or_create_browser("firefox", "122", "Ubuntu 22.04", "headless", "selenium", "")),
            # Released 2024-01-25
            # ("edge", "121", None, ["--headless=new"], get_or_create_browser("edge", "121", "Ubuntu 22.04", "headless-new", "selenium", "")),

            # To compare between versions use additional chrome and firefox versions
            # Released 2024-02-14
            ("chrome", "122", None, ["--headless=new"], get_or_create_browser("chrome", "122", "Ubuntu 22.04", "headless-new", "selenium", "")),
            # Released 2023-11-29
            ("chrome", "120", None, ["--headless=new"], get_or_create_browser("chrome", "120", "Ubuntu 22.04", "headless-new", "selenium", "")),
            # Released 2023-12-19
            ("firefox", "121", None, ["-headless"], get_or_create_browser("firefox", "121", "Ubuntu 22.04", "headless", "selenium", "")),
            # Released 2023-02-20
            ("firefox", "123", None, ["-headless"], get_or_create_browser("firefox", "123", "Ubuntu 22.04", "headless", "selenium", "")),

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
        if args.new_browsers:
            config = [
                # Released 2024-11-06
                ("chrome", "131", None, ["--headless=new"], get_or_create_browser("chrome", "131", "Ubuntu 22.04", "headless-new", "selenium", "")),
                # Released 2024-11-26
                ("firefox", "133", None, ["-headless"], get_or_create_browser("firefox", "133", "Ubuntu 22.04", "headless", "selenium", "")),
                # Released 2024-12-11 
                ("brave", "131", "/home/ubuntu/brave-versions/v1.73.101/brave-browser",
                ["--headless=new"], get_or_create_browser("brave", "v1.73.101 (Chromium 131.0.6778.139)", "Ubuntu 22.04", "headless-new", "selenium", "")),
            ]
    if args.debug_browsers:
        config = [
            # Configure browsers to use for debug runs manually here
            ("chrome", "128", None, ["--headless=new"], get_or_create_browser("chrome", "128", "Ubuntu 22.04", "headless-new", "selenium", "")),
        ]

    # Use the debug Unknown browser if generating the page-runner json File
    if args.gen_page_runner:
        config = [("Unknown", "Unknown", None, None, get_or_create_browser("Unknown", "Unknown", "Unknown", "real", "manual", None))]

    # Setup variables related to logging and more
    now = f"{datetime.datetime.now()}"
    log_path = f"logs/desktop-selenium/{now}"
    all_args = []
    url_list = []
    rand_token = generate_short_uuid()
    chunk_id = 0

    # If page_runner_json is set, load the URLs from the file
    if args.page_runner_json != "":
        with open(args.page_runner_json, "r") as f:
            urls = json.load(f)
        all_args = []
        assert(len(config) == 1)
        browser_name, browser_version, binary_location, arguments, browser_id = config[0]
        if args.ignore_certs:
            arguments = arguments + ["--ignore-certificate-errors"]
        for url in urls:
            assert(int(re.findall("runner-(\d+)", url)[0]) == 1)
            url = url + f"?browser_id={browser_id}"
            all_args.append((log_path, browser_name, browser_version, binary_location, arguments, args.debug_input, [url], args.timeout_task, args.timeout_task-60))
    # Otherwise load the test_urls by using get_tests or from repeat.json
    else:
        for scheme in ["http", "https"]:
            for browser_name, browser_version, binary_location, arguments, browser_id in config:
                if args.ignore_certs:
                    arguments = arguments + ["--ignore-certificate-errors"]

                if args.run_mode == "run_all":
                    test_urls = get_tests(resp_type=args.resp_type, browser_id=browser_id, scheme=scheme, max_resps=args.max_resps, max_popups=args.max_popups)
                    page_timeout = TIMEOUT
                elif args.run_mode == "repeat":
                    with open("repeat.json", "r") as f:
                        test_urls = json.load(f).get(str(browser_id), [])
                        test_urls = list(filter(lambda s: s.startswith(f"{scheme}://"), test_urls))
                        # Increased timeout for repeat tests
                        page_timeout = 3 * TIMEOUT
                    if not len(test_urls):
                        continue
                else:
                    raise Exception(f"Unknown run mode: {args.run_mode}")

                # Chunk the test_urls according to the max_urls_until_restart setting
                url_chunks = [test_urls[i:i + args.max_urls_until_restart] for i in range(0, len(test_urls), args.max_urls_until_restart)]
                for url_chunk in url_chunks:
                    all_args.append((log_path, browser_name, browser_version, binary_location, arguments, args.debug_input, url_chunk, args.timeout_task, page_timeout))

                    if args.gen_page_runner:
                        url_chunk = url_chunk * args.gen_multiplier
                        url_list.append(create_test_page_runner(browser_id, f"{rand_token}-{chunk_id}", url_chunk))
                        chunk_id += 1

    # If the gen_page_runner option is set, generate a JSON with a list of URLs to visit
    if args.gen_page_runner:
        print(f"URLs to visit: {url_list}")
        with open(f"{args.resp_type}-MaxURLs{args.max_urls_until_restart}-MaxResps{args.max_resps}-MaxPopups{args.max_popups}-{rand_token}.json", "w") as f:
            json.dump(url_list, f)
    # Otherwise create up to num_browsers processes and start running tests in all of them
    else:
        with Pool(processes=args.num_browsers, initializer=setup_process, initargs=(log_path,)) as p:
            r = list(tqdm(p.imap_unordered(worker_function, all_args), total=len(all_args), desc="Header Parsing Progress (URL Chunks)", leave=True, position=0))
            # print(r)
