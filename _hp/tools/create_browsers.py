from crawler.utils import get_or_create_browser

# Android browsers
# Will be created automatically based on the android_config.json file

# iPhone browsers
ios_browser_list = [('chrome', '120.0.6099.119'), ('brave', '1.61 (23.12.18.22)'), ('opera', '4.4.1 (0)'), ('firefox', '121.0 (36782)'), ('safari', '17'), ('operagx', '2.2.2'), ('edge', '120.0.2210.116')]

for browser_name, browser_version in ios_browser_list:		
    browser_id = get_or_create_browser(browser_name, browser_version, 'iPadOS 17.2', 'real', 'intent', '')	

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
