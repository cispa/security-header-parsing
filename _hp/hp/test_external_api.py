import pytest
import json
import httpx

with open("/app/_hp/wpt-config.json", "r") as f:
    wpt_config = json.load(f)

def test_get_resp_ids():
    """Check that server returns resp_ids: 2 entries for label=XFO&resp_type=debug"""
    assert wpt_config["browser_host"]
    assert wpt_config["alternate_hosts"]["alt"]
    base_host = f"sub.{wpt_config['browser_host']}"
    label = "XFO"
    resp_type = "debug"

    resp_ids = httpx.get(
        f"https://{base_host}/_hp/server/get_resp_ids.py?label={label}&resp_type={resp_type}",
        verify=False,
    ).json()

    assert len(resp_ids) == 2


def test_notify_runner_clients():
    """Check that notify_runner_clients.py works"""
    base_host = f"sub.{wpt_config['browser_host']}"
    run_id = "does_not_exist"

    resp = httpx.get(
        f"https://{base_host}/_hp/server/notify_runner_clients.py?run_id={run_id}",
        verify=False,
    ).json()

    assert resp == {"result": "done"}


def test_responses():
    """Check that responses.py returns valid responses"""
    base_host = f"sub.{wpt_config['browser_host']}"
    resp_id = 1
    resp = 1
    feature_group = "framing"

    resp = httpx.get(
        f"https://{base_host}/_hp/server/responses.py?resp={resp}&resp_id={resp_id}&feature_group={feature_group}",
        verify=False,
    )

    assert resp.status_code == 200


def test_store_results():
    """Check that store_results.py works"""
    base_host = f"sub.{wpt_config['browser_host']}"

    resp = httpx.post(
        f"https://{base_host}/_hp/server/store_results.py", verify=False
    ).json()

    # Empty body/non-json body should be rejected
    assert resp == {"Error": "Expecting value: line 1 column 1 (char 0)"}

    # Correct entry should be saved
    body = {
        "tests": [
            {
                "name": f"referrer_iframe|false|window.open|http://{base_host}|199",
                "outcome": f"document.referrer: http://{base_host}/_hp/server/responses.py?feature_group=rp&resp_id=199&count=1&nest=1&origin=http://{base_host}&element=window.open&resp=1",
                "status": 0,
                "message": None,
                "stack": None,
                "resp_scheme": "http",
                "resp_host": f"{base_host}",
                "relation": "window.open",
            }
        ],
        "browser_id": "1",
        "test": f"http://{base_host}/_hp/tests/referrer-access-rp.sub.html?resp_type=basic&browser_id=1&label=RP&first_id=199&last_id=199&scheme=http&t_resp_id=199&t_element_relation=iframe_window.open&t_resp_origin=http://{base_host}",
        "status": 0,
        "message": None,
        "stack": None,
        "org_scheme": "http",
        "org_host": f"{base_host}",
        "full_url": f"http://{base_host}/_hp/tests/referrer-access-rp.sub.html?resp_type=basic&browser_id=1&label=RP&first_id=199&last_id=199&scheme=http&t_resp_id=199&t_element_relation=iframe_window.open&t_resp_origin=http://{base_host}",
    }

    resp = httpx.post(
        f"https://{base_host}/_hp/server/store_results.py", verify=False, json=body
    ).json()

    # Correct body should be saved
    assert resp == {'Status': 'Success'}
