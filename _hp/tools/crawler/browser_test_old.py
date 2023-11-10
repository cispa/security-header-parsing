import logging
import time
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

TESTING_SERVER="http://localhost:5001"

def get_browser_log_entries(driver):
    """get log entreies from selenium and add to python logger before returning"""
    loglevels = { 'NOTSET':0 , 'DEBUG':10 ,'INFO': 20 , 'WARNING':30, 'ERROR':40, 'SEVERE':40, 'CRITICAL':50}
    time.sleep(10)
    #initialise a logger
    browserlog = logging.getLogger("chrome")
    #get browser logs
    slurped_logs = driver.get_log('browser')
    print("yes")
    for entry in slurped_logs:
        if entry['level']=='SEVERE' and "X-Frame-Options" in entry['message']:
            # print(entry)
            #convert broswer log to python log format
            rec = browserlog.makeRecord("%s.%s"%(browserlog.name,entry['source']),loglevels.get(entry['level']),'.',0,entry['message'],None,None)
            rec.created = entry['timestamp'] /1000 # log using original timestamp.. us -> ms
            try:
                #add browser log to python log
                browserlog.handle(rec)
            except:
                print("")
                # print(entry)
    #and return logs incase you want them
    print("Hello")
    return slurped_logs

def demo():
    caps = DesiredCapabilities.CHROME
    caps['goog:loggingPrefs'] = { 'browser':'ALL' }
    driver = webdriver.Chrome(desired_capabilities=caps )
    header_data = {
    "xfo": "html",
    "hsts": "html",
    "csp": "html",
    "rp": {"header_name": "Referrer-Policy:"},
    "pp": {"header_name": "Permissions-Policy:"},
    "coop": {"header_name": "Cross-Origin-Opener-Policy:"}
}
    driver.get(f"{TESTING_SERVER}/xfo/xfo.html")
    print("yeahhhhh")
    time.sleep(10)
    # for entry in driver.get_log('browser'):
    #     if entry['level']=='SEVERE' and "X-Frame-Options" in entry['message']:
    #         print(entry)
    messages = get_browser_log_entries(driver)
    driver.quit()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(levelname)7s:%(message)s')
    logging.info("start")
    demo()
    logging.info("end")