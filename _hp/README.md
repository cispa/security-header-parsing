# HTTP Header Security

- Setup:
    - Create a fresh Ubuntu22 container/VM: `lxc launch ubuntu:22.04 <name>` and connect to it `lxc exec <name> bash`
    - Switch to the ubuntu user: `su - ubuntu`
    - Clone this repository: `git clone git@projects.cispa.saarland:swag/wpt.git`
    - Run the setup file: `cd wpt/_hp`, `./setup.sh` (reopen all terminals or run `source ~/.bashrc` afterwards)
    - Configure DB settings in [config.json](config.json)
    - Setup the database: `cd _hp/tools && poetry run python models.py`
    - Setup certs: either remove `.demo` from the files in `_hp/tools/certs/` to use self-signed certs or add the real certs there
- Run:
    - Start the WPT Server (from the top-most folder): `poetry run -C _hp python wpt serve --config _hp/wpt-config.json`
    - Automatic: Start the testrunners, ...
    - Manual: Visit http://headers.websec.saarland:80/_hp/tests/framing.sub.html (HTTPS: 443, HTTP2: 9000)
    - ...
- TODOs:
    - setup container on 01 + rules to forward the traffic there
    - implement tests for each feature group
    - ...
- Inventory (of _hp):
    - config.json: DB connection and co.
    - wpt-config.json: Ports, Domains, .. TODO: How to configure subdomains and certs? currently hardcoded in tools/serve/serve.py
    - common/: Shared non-js files for the tests (images, html, ...)
    - ressources/: Shared javascript files for the tests (testharness, save_results, ...)
    - server/
        - responses.py: Serves the correct responses from the db (responses.py?resp_id=<int>&feature_group=<str>)
        - store_results.py: Stores the test results in the db (expects JSON with {tests: [...], browser=browser_id})
    - tests/
        - One file for each feature group to test
        - Create one testcase for everything one wants to test
        - Then run these for all corresponding responses and relevant origin configurations
        - TODO: decide/fix how to provide parameters to the tests: Maybe http://headers.websec.saarland:1234/_hp/tests/framing.sub.html?browser=browser_id&start_id=start_id&end_id=end_id 
        - TODO: find out how to save test metadata (e.g., resp_id) and how to also store that in the db
    - tools/
        - Non Web files
        - crawler/ The code for the crawlers that visit the tests
        - models.py: Defines the database models (results, rseponses, ...); creates dummy date if run directly
        - TODO: create_responses.py
            - First create two responses for each feature group: "deny" and "allow" for testing the tests
            - Later create useful data for responses
- The only other relevant files are:
    - tools/serve/...: Config to run WPT
    - tools/wptserve/...: The WPT server
    - Some of the tests to take inspirations e.g., x-frame-options/...


## Browser setup?
```
{
    "BROWSERS": {
        "BROWSERNAME_desktop":"PATH_TO_BROWSER_EXECUTABLE",
        "BROWSERNAME_android":"PACKAGE_NAME",
        "BROWSERNAME_ios":"YET_TO_DECIDE",
    }
}

> For desktop browsers, assign the value as the path to the executable/driver file. For android, assign the value of the package name.

```