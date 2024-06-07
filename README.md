# Head(ers) Up! Detecting Security Header Inconsistencies in Browsers

This repository contains all code for our paper `Head(ers) Up! Detecting Security Header Inconsistencies in Browsers`.

This repository is a fork of [WPT](https://github.com/web-platform-tests/wpt), the original README can be found [here](./README_original.md).
All test and analysis code for our paper can be found in the `_hp` directory.
Our modified version of the wptserve HTTP server implementation can be found in `tools/serve` and `tools/wptserve`. All other directories are untouched and required for `wptserve` to run, we removed the other WPT test directories for better clarity.

## Setup

## Run Instructions

## Inventory
- `_hp`: All test and analysis code for the paper:
  - 
- `tools`: Contains modified `wptserve`
- Other directories are used by `wptserve` internally but are not modified



- Setup:
    - Create a fresh Ubuntu22 container/VM: `lxc launch ubuntu:22.04 <name>` and connect to it `lxc exec <name> bash`
    - Switch to the ubuntu user: `su - ubuntu`
    - Clone this repository: `git@github.com:header-testing/header-testing.git`
    - Run the setup file: `cd wpt/_hp`, `./setup.bash` (reopen all terminals or run `source ~/.bashrc` afterwards)
    - Configure DB settings in [config.json](config.json)
    - Setup the database: `cd _hp/tools && poetry run python models.py`
    - Setup certs: either remove `.demo` from the files in `_hp/tools/certs/` to use self-signed certs or add the real certs there
- Run:
    - Start the WPT Server (from the top-most folder): `poetry run -C _hp python wpt serve --config _hp/wpt-config.json`
    - Automatic: Start the testrunners, e.g., `poetry run desktop_selenium.py`
    - Manual: Visit http://sub.headers.websec.saarland:80/_hp/tests/framing.sub.html (HTTPS: 443)
- TODOs:
    - analyse results!
      - discover differences in browsers/versions
      - "explain" reasons (keep in mind that other features such as blocked mixed content and CORB might be responsible for differences and not different parsing of the security header)
    - ...
- Inventory (of _hp):
    - wpt-config.json: Ports, Domains, Certs, ... (Subdomains currently hardcoded in tools/serve/serve.py)
    - common/: Shared non-js files for the tests (images, html, ...)
    - resources/: Shared javascript files for the tests (testharness, save_results, ...)
    - server/
        - responses.py: Serves the correct responses from the db (responses.py?resp_id=<int>&feature_group=<str>)
        - store_results.py: Stores the test results in the db (expects JSON with {tests: [...], browser=browser_id})
    - tests/
        - One file for each feature group to test
        - Create one testcase for everything one wants to test
        - Then run these for all corresponding responses and relevant origin configurations
        - How to provide parameters to the tests
            - http://sub.headers.websec.saarland:80/_hp/tests/framing.sub.html?browser=<browser_id>&first_id=<id>&last_id=<id>
    - tools/
        - Non web files
        - config.json: DB connection and co.
        - crawler/ The code for the crawlers that visit the tests
        - models.py: Defines the database models (results, responses, ...); creates dummy data if run directly
        - create_responses.py: create two responses for each feature group: "deny" and "allow" for testing the tests
- The only other relevant files are:
    - tools/serve/...: Config to run WPT
    - tools/wptserve/...: The WPT server
    - Some of the tests to take inspirations e.g., x-frame-options/...