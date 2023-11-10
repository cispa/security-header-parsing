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
for (name, version) in [("chrome", "119"), ("firefox", "119"), ("safari", "17.0"), ("edge", "119")]:
    create_browser(name, version, os, headless_mode, automation_mode, "")

# Linux browsers managed by Selenium
#TODO

# Android browsers
#TODO

# iPhone browsers
#TODO

# Linux browsers managed by Playwright
#MAYBE?

# More browser categories?