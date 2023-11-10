import time
from utils import TIMEOUT, get_tests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



def main():
    # TODO use correct browser_id, basic mode, both schemes, ...
    test_urls = get_tests(resp_type="debug", browser_id=1, scheme="https")
    driver = webdriver.Safari()
    try:
        for url in test_urls:
            driver.get(url)
            print(driver.title)
            # Wait until the results are saved on the server (after finishing fetch request, a div with id "finished" is added to the DOM)
            WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, "finished")))
    except Exception as e:
        print(e)
    finally:
        driver.quit()


if __name__ == '__main__':
    main()

    # TODO: define and create different browsers
    chrome_options = webdriver.ChromeOptions()
    chrome_options.browser_version = "118"
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://example.org")
    time.sleep(10)
    driver.quit()

    options = webdriver.FirefoxOptions()
    options.browser_version = "115" #119
    driver = webdriver.Firefox(options=options)
    driver.get("https://example.org")
    time.sleep(10)
    driver.quit()

    options = webdriver.SafariOptions()
    options.browser_version = "17.0"
    driver = webdriver.Safari(options=options)
    driver.get("https://example.org")
    time.sleep(10)
    driver.quit()

    options = webdriver.EdgeOptions()
    options.browser_version = "119"
    driver = webdriver.Edge(options=options)
    driver.get("https://example.org")
    time.sleep(10)
    driver.quit()

    # Alternative idea with grid
    # java -jar selenium-server-4.15.0.jar standalone --selenium-manager True
    # remote_url = "http://localhost:4444/wd/hub"