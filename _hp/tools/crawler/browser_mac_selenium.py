from utils import TIMEOUT, get_tests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main():
    # TODO use correct browser_id, basic mode, both schemes, ...
    test_urls = get_tests(resp_type="debug", browser_id=1, scheme="https")
    driver = webdriver.Chrome()
    try:
        for url in test_urls:
            driver.get(url)
            print(driver.title)
            element = WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, "finished")))
    except Exception as e:
        print(e)
    finally:
        driver.quit()

if __name__ == '__main__':
    main()

    # TODO: define and create different browsers

    # Popups are enabled by default in Selenium in all browsers apart from Safari (https://www.browserstack.com/docs/automate/selenium/handle-permission-pop-ups#python)
    # caps["browserstack.safari.enablePopups"] = "true"