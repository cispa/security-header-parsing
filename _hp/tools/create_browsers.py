# TODO: fill the Browser table with all browsers used!
from models import Session, Browser
from sqlalchemy.exc import IntegrityError

def create_browser(name, version, os, headless_mode, automation_mode, add_info):
    with Session() as session:
        try:
            r = Browser(name=name, version=version, os=os, headless_mode=headless_mode, automation_mode=automation_mode, add_info=add_info)
            session.add(r)
            session.commit()
        except IntegrityError as e:
            session.rollback()
            print("IntegrityError probably response already exists")

# MAC (local) browsers with Selenium automation
os = "macOS 14.0"
automation_mode = "selenium"
headless_mode = "real"
for (name, version) in [("chrome", "119"), ("firefox", "119"), ("safari", "17.0"), ("edge", "119"), ("brave", "1.60.114 (119.0.6045.124)")]:
    create_browser(name, version, os, headless_mode, automation_mode, "")

# Linux browsers managed by Selenium
os = "Ubuntu 22.04"
automation_mode = "selenium"
for (name, version) in [("chrome", "119"), ("firefox", "119"), ("edge", "119")]:
    if name == "firefox":
        headless_mode = "headless"
    else:
        headless_mode = "headless-new"
    create_browser(name, version, os, headless_mode, automation_mode, "")

# Android browsers
os = "Android 11"
automation_mode = "intent"
headless_mode = "real"
for (name, version) in [("firefox", "119.1.1"), ("brave", "1.60.116"), ("ucmobile", "13.3.8.1305"), ("opera", "78.4.4143.75735")]:
    create_browser(name, version, os, headless_mode, automation_mode, "")

# iPhone browsers
#TODO

# Mac browsers managed by PLaywright
os = "macOS 14.0"
automation_mode = "playwright"
headless_mode = "real"
for (name, version) in [("chrome", "119"), ("firefox", "118"), ("WebKit", "17.4")]:
    create_browser(name, version, os, headless_mode, automation_mode, "Playwright=v1.39")

# Linux browsers managed by Playwright
os = "Ubuntu 22.04"
automation_mode = "playwright"
headless_mode = "headless"
for (name, version) in [("chrome", "119"), ("firefox", "118"), ("WebKit", "17.4")]:
    create_browser(name, version, os, headless_mode, automation_mode, "Playwright=v1.39")

# More browser categories?