from utils import TIMEOUT, get_tests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main():
    test_urls = get_tests(resp_type="debug", browser_id=1, scheme="https")
    driver = webdriver.Chrome()
    try:
        for url in test_urls:
            driver.get(url)
            print(driver.title)
            element = WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located(By.ID, "results"))
            print(element)
    except Exception as e:
        print(e)
    finally:
        driver.quit()

if __name__ == '__main__':
    main()