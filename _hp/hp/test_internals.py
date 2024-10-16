import pytest

from hp.tools.crawler.selenium_run_specific import config, run_specific
from hp.tools.crawler.utils import generate_short_uuid


def test_generate_short_uuid():
    assert len(generate_short_uuid(3)) == 3


def test_selenium_test_specific():
    url = "http://sub.headers.websec.saarland/_hp/tests/referrer-access-rp.sub.html?resp_type=basic&browser_id=1&label=RP&first_id=199&last_id=199&scheme=http&t_resp_id=199&t_element_relation=iframe_window.open&t_resp_origin=http://sub.headers.websec.saarland"
    for browser_name, browser_version, binary_location, arguments, _ in config:
        run_specific(url, browser_name, browser_version, binary_location, arguments)

    assert True
