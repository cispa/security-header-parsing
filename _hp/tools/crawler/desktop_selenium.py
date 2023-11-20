import sys
from utils import TIMEOUT, get_tests, HSTS_DEACTIVATE
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import traceback
import datetime


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


def main(browser_name, browser_version, binary_location, arguments, browser_id):
    for scheme in ["http", "https"]:
        test_urls = get_tests(
            resp_type=MODE, browser_id=browser_id, scheme=scheme)
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
                    # Wait until the results are saved on the server (after finishing fetch request, a div with id "finished" is added to the DOM)
                    driver.switch_to.window(new_window)
                    WebDriverWait(driver, TIMEOUT).until(
                        EC.presence_of_element_located((By.ID, "finished")))
                except Exception as e:
                    print("Exception!", e)
                    print(driver.current_url)
                    print(url)
                finally:
                    # input("Next")  # Option to manualy debug
                    # Close the current window
                    driver.close()
                    # Switch back to the old tab or window
                    driver.switch_to.window(original_window)
        except Exception as e:
            print("Major Exception occured!", e)
        finally:
            driver.quit()
            print(f"Finish {browser_name} ({browser_version}) ({scheme})")


MODE = "basic"  # "debug", "parsing"
if __name__ == '__main__':
    # (browser_name, version, binary_location (e.g., for brave), arguments (e.g, for headless), browser_id)
    if sys.platform == "darwin":
        config = [
            # ("chrome", "119", None, None, 5),
            # ("firefox", "119", None, None, 6),
            # ("safari", "17.0", None, None, 7),
            # ("edge", "119", None, None, 8),
            # Download .dmg from https://github.com/brave/brave-browser/releases and install
            # E.g., https://github.com/brave/brave-browser/releases/tag/v1.60.118, rename the file
            ("brave", "119", "/Applications/Brave Browser 1.60.118.app/Contents/MacOS/Brave Browser",
             ["--disable-brave-update"], 37),
        ]
    # Linux Ubuntu
    else:
        config = [
            # Headless (new)
            ("chrome", "119", None, ["--headless=new"], 13),
            ("firefox", "119", None, ["-headless"], 14),
            # ("safari", "17.0", None, None, 4), No Safari on Linux
            ("edge", "119", None, ["--headless=new"], 15),
            # Brave (different version)
            # mkdir ~/brave-versions
            # mkdir ~/brave-versions/brave-version
            # CD into the folder and download *.linux-amd64.zip from https://github.com/brave/brave-browser/releases and unzip
            # The ZIP versions seem to not auto update and one can install as many as wanted (only on linux though?)
            # v1.59.120 (Chromium 118): wget https://github.com/brave/brave-browser/releases/download/v1.59.120/brave-browser-1.59.120-linux-amd64.zip
            # Note: if you specify the wrong chromium version, selenium will ignore the binary location and download CFT instead??
            ("brave", "118", "/home/ubuntu/brave-versions/v1.59.120/brave-browser",
             ["--headless=new"], 60),
            # v1.60.114 (Chromium 119): wget https://github.com/brave/brave-browser/releases/download/v1.60.114/brave-browser-1.60.114-linux-amd64.zip
            ("brave", "119", "/home/ubuntu/brave-versions/v1.60.114/brave-browser",
             ["--headless=new"], 59),
            # Headfull
            ("chrome", "119", None, None, 71),
            ("firefox", "119", None, None, 72),
            ("edge", "119", None, None, 73),
            ("brave", "118", "/home/ubuntu/brave-versions/v1.59.120/brave-browser", None, 75),
            ("brave", "119", "/home/ubuntu/brave-versions/v1.60.114/brave-browser", None, 74),
        ]
        debug = True
        if debug:
            config = [
                ("brave", "119", "/home/ubuntu/brave-versions/v1.60.114/brave-browser", None, 74),
            ]

    now = f"{datetime.datetime.now()}"
    for t in config:
        with Tee("desktop-selenium", now) as f:
            main(*t)

    # Headfull (linux):
    # Xvfb :99 -screen 0 1920x1080x24 &
    # x11vnc -display :99 -bg -shared -forever -passwd abc -xkb -rfbport 5900
    # export DISPLAY=:99 && fluxbox -log fluxbox.log &
    # export DISPLAY=:99 && python desktop_selenium.py

    # Alternative idea with grid
    # java -jar selenium-server-4.15.0.jar standalone --selenium-manager True
    # remote_url = "http://localhost:4444/wd/hub"
