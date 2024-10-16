# Head(er)s Up! Detecting Security Header Inconsistencies in Browsers

This repository contains all code for our paper `Head(er)s Up! Detecting Security Header Inconsistencies in Browsers`.

This repository is a fork of [WPT](https://github.com/web-platform-tests/wpt), the original README can be found [here](./README_original.md).
All test and analysis code for our paper can be found in the [_hp](./_hp/README.md) directory.
Our modified version of the wptserve HTTP server implementation can be found in `tools/serve` and `tools/wptserve`. All other directories are untouched and required for `wptserve` to run, we removed the other WPT test directories for better clarity.

## Setup
- Create a fresh Ubuntu22 container/VM: `lxc launch ubuntu:22.04 <name>` and connect to it `lxc exec <name> bash`
  - Switch to the ubuntu user: `su - ubuntu`
  - Clone this repository: `git clone git@github.com:header-testing/header-testing.git`
  - Run the setup file: `cd header-testing/_hp`, `./setup.bash` (reopen all terminals or run `source ~/.bashrc` afterwards)
  - Configure DB settings in [config.json](_hp/tools/config.json); Make sure to create a database with the correct name
  - Setup the database: `cd _hp/hp/tools && poetry run python models.py`
  - Setup certs: either remove `.demo` from the files in `_hp/hp/tools/certs/` to use self-signed certs or add your own certs here

## Run Instructions
- Always start the WPT server first (from the top-most folder): `poetry run -C _hp python wpt serve --config _hp/wpt-config.json`
- Create the basic and parsing responses: Run `cd _hp/hp/tools && poetry run python create_responses.py` (basic), run `cd analysis` and execute `response_header_generation.ipynb` to generate the parsing responses.
- Manually check if the server and the tests are working: Visit http://sub.headers.websec.saarland:80/_hp/tests/framing.sub.html
- Automatic testrunners:
  - `cd _hp/hp/tools/crawler`
  - Android: `poetry run python android_intent.py` (TODO: Additional config required; solve android_intent and more?!)
  - MacOS/Ubuntu: `poetry run python desktop_selenium.py` (For a quick test run: `poetry run python desktop_selenium.py --debug_browsers --resp_type debug --ignore_certs`)
  - iPadOS/iOS: `poetry run python desktop_selenium.py ----gen_page_runner --page_runner_json urls.json --max_urls_until_restart 10000"`, then visit the URLs in that file manually
  - TODO: Exact settings of the runs for our experiment:
    - TODO: some information about how to exactly reproduce our results?
    - TODO: repeat to ensure each test has 5x repetitions (`poetry run python create_repeat ...`)
    - ...
- Optional configuration to run headfull browsers on linux server:
```bash
Xvfb :99 -screen 0 1920x1080x24 &
x11vnc -display :99 -bg -shared -forever -passwd abc -xkb -rfbport 5900
export DISPLAY=:99 && fluxbox -log fluxbox.log &
```
- Analysis:
  - Run `cd _hp/hp/tools/analysis && poetry run jupyter-lab`
  - Open `_hp/hp/tools/analysis/main_analysis_desktop_basic+parsing.ipynb`
  - TODO: rename: (Also contains the mobile analysis)
  - TODO: check analysis code and improve

## Inventory
- `_hp/`: All test and analysis code for the paper:
  - `common/`: Response helper files required for the tests
  - `resources/`:
    - `store_results.sub.js`: Main JavaScript file with all helper functions such that our test functions work
    - `testharness.sub.js`: Modified testharness.js to store the recorded output additonally to the test status
  - `server/`: Custom server endpoints to save data in our database and serve the correct responses from the DB
  - `tests/`: The template pages containing the test functions for the 12 tested features
  - `hp/tools/`: All other code
    - `analysis/`: Analysis code (.ipynb files) + utils
    - `certs/`: Put your certs here to enable testing of HTTPS
    - `crawler/`:  Intent (Android), Selenium (Mac + Ubuntu), and Browser Page Runner (iOS) test runners + utils
  - `pyproject.toml`, `wpt-config.json`, and more: Various config files for the project
- `tools/`: Contains modified `wptserve`
- Other directories are used by `wptserve` internally but are not modified
