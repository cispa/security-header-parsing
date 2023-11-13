import sys
from utils import TIMEOUT, get_tests
from playwright.sync_api import sync_playwright, Playwright, Browser

def get_browser(browser: str, headless: bool, playwright: Playwright):
    if browser == "chromium":
        driver = playwright.chromium
    elif browser == "firefox":
        driver = playwright.firefox
    elif browser == "webkit":
        driver = playwright.webkit
    else:
        print(f"Unsupported browser: {browser}")
        return Exception()  
    return driver.launch(headless=headless)


def main(browser_name, browser_version, headless, browser_id):
    with sync_playwright() as playwright:
        for scheme in ["http", "https"]:
            test_urls = get_tests(resp_type=MODE, browser_id=browser_id, scheme=scheme)
            browser: Browser = get_browser(browser_name, headless, playwright)
            print(browser.browser_type, scheme)
            try:
                for url in test_urls:
                    try:
                        page = browser.new_page()
                        page.goto(url)
                        print(url)
                        print(page.title())
                        # Wait until the results are saved on the server (after finishing fetch request, a div with id "finished" is added to the DOM)
                        page.locator("#finished").wait_for(timeout=TIMEOUT*1000, state="attached")
                        print("Page finished")
                        input("Next!")
                        page.close()
                    except Exception as e:
                        print(e)
                    finally:
                        input("Next!")
            except Exception as e:
                print("Exception occured!")
                print(e)
            finally:
                browser.close()

MODE = "debug"  # "debug", "basic", "parsing"
if __name__ == '__main__':
    # (browser_name, version, headless, browser_id)
    if sys.platform == "darwin":
        config = [
            ("chromium", "119", False, 23),
            ("firefox", "118", False, 24),
            ("webkit", "17.4", False, 25),
        ]
    # Linux Ubuntu
    else:
        # Headless for now as no Xvfb or similar configured
        config = [
            ("chromium", "119", True, 26),
            ("firefox", "118", True, 27),
            ("webkit", "17.4", True, 28), 
        ]
    for t in config:
        main(*t)