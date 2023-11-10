import time
from utils import TIMEOUT, get_tests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_browser(browser: str, version: str, binary_location=None, arguments=None):
    if browser == "chrome":
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
        print(f"Unsupported browser: {browser}")
        return Exception()
    
    options.browser_version = version
    if binary_location:
        options.binary_location = binary_location # Possible to specify other browsers? e.g., brave?
    if arguments:
        options.add_argument(arguments) # ("--headless=new") # Possible to add arguments such as headless?
    return driver(options=options)


def main(browser_name, browser_version, binary_location, arguments, browser_id):
    for scheme in ["http", "https"]:
        test_urls = get_tests(resp_type=MODE, browser_id=browser_id, scheme=scheme)
        driver = get_browser(browser_name, browser_version, binary_location, arguments)
        print(driver.capabilities)
        try:
            1/0
            for url in test_urls:
                driver.get(url)
                print(driver.title)
                # Wait until the results are saved on the server (after finishing fetch request, a div with id "finished" is added to the DOM)
                WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, "finished")))
        except Exception as e:
            print("Exception occured!")
            print(e)
        finally:
            driver.quit()

MODE = "basic"  # "debug", "parsing"
if __name__ == '__main__':
    # (browser_name, version, binary_location (e.g., for brave), arguments (e.g, for headless), browser_id)
    config = [
        ("chrome", "119", None, None, 2),
        ("firefox", "119", None, None, 3),
        ("safari", "17.0", None, None, 4),
        ("edge", "119", None, None, 5)
    ]
    for t in config:
        main(*t)

    # Alternative idea with grid
    # java -jar selenium-server-4.15.0.jar standalone --selenium-manager True
    # remote_url = "http://localhost:4444/wd/hub"