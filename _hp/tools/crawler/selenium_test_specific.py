from utils import TIMEOUT, generate_short_uuid, get_tests, HSTS_DEACTIVATE, create_test_page_runner

from create_browsers import get_or_create_browser
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from desktop_selenium import get_browser


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

def test_specific(url, browser_name, browser_version, binary_location, arguments):
    driver = get_browser(browser_name, browser_version,
                        binary_location, arguments)
    original_window = driver.current_window_handle
    driver.get(url)
    driver.switch_to.window(original_window)
    WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "finished")))
    
    print(f"Visited, {browser_name}")
    driver.close()
    

if __name__ == "__main__":
    url = "http://sub.headers.websec.saarland/_hp/tests/referrer-access-rp.sub.html?resp_type=basic&browser_id=1&label=RP&first_id=199&last_id=199&scheme=http&t_resp_id=199&t_element_relation=iframe_window.open&t_resp_origin=http://sub.headers.websec.saarland"

    for (browser_name, browser_version, binary_location, arguments, _) in config:
        test_specific(url, browser_name, browser_version, binary_location, arguments)