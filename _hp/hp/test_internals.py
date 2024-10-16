import pytest
import json
import httpx

from hp.tools.crawler.selenium_run_specific import config, run_specific
from hp.tools.crawler.utils import generate_short_uuid
from hp.tools.create_responses import create_responses

with open("_hp/wpt-config.json", "r") as f:
    wpt_config = json.load(f)


def test_generate_short_uuid():
    """Assert length of generate_shot_uuid is correct."""
    assert len(generate_short_uuid(3)) == 3


def test_selenium_test_specific():
    """Smoke test for run_specific: function runs without crashing, browser can visit one of our test pages."""
    url = f"http://sub.{wpt_config['browser_host']}/_hp/tests/referrer-access-rp.sub.html?resp_type=basic&browser_id=1&label=RP&first_id=199&last_id=199&scheme=http&t_resp_id=199&t_element_relation=iframe_window.open&t_resp_origin=http://sub.{wpt_config['browser_host']}"
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
