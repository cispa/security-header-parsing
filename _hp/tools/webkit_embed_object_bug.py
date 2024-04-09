from playwright.sync_api import sync_playwright
import requests
from tqdm import tqdm


def check_for_alert(browser_type, url):
    with sync_playwright() as p:
        browser = getattr(p, browser_type).launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # Check if an alert pops up
        alert_triggered = False
        def handle_alert(alert):
            nonlocal alert_triggered
            alert_triggered = True
            return alert.accept()

        page.on("dialog", handle_alert)
        page.goto(url)
        page.wait_for_timeout(100)
        page.close()
        context.close()
        browser.close()
        
        if alert_triggered:
            return True
        else:
            return False
        
def fetch_file_extensions():
    url = "https://gist.githubusercontent.com/securifera/e7eed730cbe1ce43d0c29d7cd2d582f4/raw/908a7934ca448f389275432514eaa157def9c385/Filename%2520extension%2520list"
    response = requests.get(url)
    if response.status_code == 200:
        return response.text.splitlines()
    else:
        print("Failed to fetch file extensions.")
        return []

def main():
    url = "https://observer.sectec.rocks/opg/embed/?url=https://echo.sectec.rocks/echo/abc.js?content-type=text/html&ecocnt_js=%3Cscript%3Ealert(1)%3C/script%3E"
    browsers = ['chromium', 'webkit', 'firefox']
    file_endings = fetch_file_extensions() 
    results = {}
    
    for browser_type in tqdm(browsers, desc='Browsers'):
        for element in tqdm(['embed', 'object'], desc='Elements', leave=False):
            for file_ending in tqdm(file_endings, desc='File Endings', leave=False):
                updated_url = url.replace('.js', file_ending)
                updated_url += f'&element={element}'
                key = f'{browser_type}_{element}_{file_ending}'
                results[key] = check_for_alert(browser_type, updated_url)
    
    print("Results:", results)

if __name__ == "__main__":
    main()
