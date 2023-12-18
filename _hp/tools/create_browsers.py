from crawler.utils import get_or_create_browser

# Android browsers
os = "Android 11"
automation_mode = "intent"
headless_mode = "real"
for (name, version) in [("firefox", "119.1.1"), ("brave", "1.60.116"), ("ucmobile", "13.3.8.1305"), ("opera", "78.4.4143.75735")]:
    get_or_create_browser(name, version, os, headless_mode, automation_mode, "")

# iPhone browsers
#TODO

# Mac browsers managed by PLaywright
os = "macOS 14.0"
automation_mode = "playwright"
headless_mode = "real"
for (name, version) in [("chrome", "119"), ("firefox", "118"), ("WebKit", "17.4")]:
    get_or_create_browser(name, version, os, headless_mode, automation_mode, "Playwright=v1.39")

# Linux browsers managed by Playwright
os = "Ubuntu 22.04"
automation_mode = "playwright"
headless_mode = "headless"
for (name, version) in [("chrome", "119"), ("firefox", "118"), ("WebKit", "17.4")]:
    get_or_create_browser(name, version, os, headless_mode, automation_mode, "Playwright=v1.39")

# More browser categories?