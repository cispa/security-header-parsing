"""
Generate the DB entry for the iPadOS browser
"""
from hp.tools.crawler.utils import get_or_create_browser

browser_name = "chrome"
browser_version = "122.0.6261.89"

browser_id = get_or_create_browser(browser_name, browser_version, 'iPadOS 17.3.1', 'real', 'intent', '')
print(f"Browser ID: {browser_id}")
