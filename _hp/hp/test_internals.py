import pytest
import json

from hp.tools.crawler.selenium_run_specific import run_specific
from hp.tools.crawler.utils import generate_short_uuid, get_tests, get_resp_ids, get_or_create_browser
from hp.tools.create_responses import create_responses
from hp.tools.crawler.desktop_selenium import get_child_processes

with open("/app/_hp/wpt-config.json", "r") as f:
    wpt_config = json.load(f)


def test_generate_short_uuid():
    """Assert length of generate_shot_uuid is correct."""
    assert len(generate_short_uuid(3)) == 3

def test_selenium_test_specific():
    """Smoke test for run_specific: function runs without crashing, browser can visit one of our test pages."""
    url = f"http://sub.{wpt_config['browser_host']}/_hp/tests/referrer-access-rp.sub.html?resp_type=basic&browser_id=1&label=RP&first_id=199&last_id=199&scheme=http&t_resp_id=199&t_element_relation=iframe_window.open&t_resp_origin=http://sub.{wpt_config['browser_host']}"
    config = [
        # Browsers (managed by Selenium itself)
        # Released 2024-01-23
        ("firefox", "122", None, ["-headless"], get_or_create_browser("firefox", "122", "Ubuntu 22.04", "headless", "selenium", "")),
    ]
    for browser_name, browser_version, binary_location, arguments, _ in config:
        run_specific(url, browser_name, browser_version, binary_location, arguments)

    assert True

def test_create_responses():
    """Check whether a response can be generated"""
    header_list = [[('x-frame-options', 'DENY')], [('x-frame-options', 'SAMEORIGIN')]]
    label = "XFO"
    resp_type = "debug"
    status_code = 200
    create_responses(header_list=header_list, label=label, status_code=status_code, resp_type=resp_type)
    assert True

def test_get_tests():
    """Check whether get_tests returns test URLs"""
    resp_type = "basic"
    browser_id = "-5"
    scheme = "http"
    max_popups = 2
    max_resps = 10
    browser_modifier = 2
    tests = get_tests(resp_type=resp_type, browser_id=browser_id, scheme=scheme, max_popups=max_popups, max_resps=max_resps, browser_modifier=browser_modifier)
    assert len(tests) == 269

def test_get_resp_ids():
    """Check whether get_resp_ids returns valid splits
    """
    label = "XFO"
    resp_type = "basic"
    num_resp_ids = 3
    splits = get_resp_ids(label=label, resp_type=resp_type, num_resp_ids=num_resp_ids)

    assert len(splits) == 4

def test_get_or_create_browser():
    """Check whether a browser configuration entry can be created
    """
    # The unknown browser always has to be ID 1
    browser = get_or_create_browser(name="Unknown", version="Unknown", os="Unknown", headless_mode="real", automation_mode="manual", add_info=None)
    assert browser == 1

def test_get_child_processes():
    """Check that 0 or 1 has a couple of childs
    """
    process_list_m = get_child_processes(0)
    process_list_l = get_child_processes(1)
    assert len(process_list_m) > 5 or len(process_list_l) > 5

