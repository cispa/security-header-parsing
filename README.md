# Head(er)s Up! Detecting Security Header Inconsistencies in Browsers

This repository contains all code for our paper `Head(er)s Up! Detecting Security Header Inconsistencies in Browsers`.

This repository is a fork of [WPT](https://github.com/web-platform-tests/wpt), the original README can be found [here](./README_original.md).
All test and analysis code for our paper can be found in the [_hp](./_hp/README.md) directory.
Our modified version of the wptserve HTTP server implementation can be found in the `tools/serve` and `tools/wptserve` directories. All other directories are untouched and required for `wptserve` to run, we removed the other WPT directories for clarity.

The project is made out of 6 parts:
1. Modified WPT server
  - Dockerized and works on MacOS and Linux
  - Optional: Configure settings: in `docker-compose.yml` and TODO, e.g., setup working certificates
  - Start with `(sudo) docker compose up`, this starts a database, configures the HTTP responses, and starts our modified WPT server
  - (Optional) Run tests to verify server is setup correctly: `sudo docker compose exec header-testing-server bash -c "poetry run -C _hp pytest /app/_hp"`
  - The server is now serving all the tests pages and reponses for our paper. Depending on the configuration the server is now available within and outside the Docker network. E.g., by default it should bind to port 80 and 443 and `curl -I http://localhost/_hp/common/empty.html` and `curl -I -k https://localhost/_hp/common/empty.html` (our dummy certificates are not valid, thus `-k`/insecure is required) on the host should return a response from `BaseHTTP/0.6 Python/3.11.5`
2. (Optional) Analysis scripts
   - Dockerized and works on MacOS and Linux
   - Run: `(sudo) docker compose exec header-testing-server bash -c "cd _hp/hp/tools/analysis && poetry run python analysis_demo.py"` to get some basic statistics about the test runs executed by the unit tests and running browser-test-runners.
   - We also provide the data and the analysis scripts used for the paper:
    - Download the database from **TODO**
    - Import the database into your local postgres: `(sudo) docker compose exec -T postgres pg_restore -U header_user -d http_header_original -v /tmp/data/http_header_original.dump`
    - Start the jupyter-lab: `(sudo) docker compose exec header-testing-server bash -c "cd /app/_hp/hp/tools/analysis && poetry run jupyter-lab --allow-root --ip 0.0.0.0"` and access the URL printed on your local browser
    - The files `analysis_may_2024.ipynb` and `analysis_december_2024.ipynb` contain the full analysis for the original browser run and the updated browser run experiments described in the paper, including the output of the analysis and can be executed to reproduce the analysis. Note: re-executing these scripts require a large amount of RAM on the docker container >20GB.
3. (Optional) Test runner for desktop linux browsers
   - Dockerized demo works on Linux and macOS; For a full run, the browser runner needs to be installed outside of docker on a linux system.
   - Demo run:
     - Run: `(sudo) docker compose exec header-testing-server bash -c "cd /app/_hp/hp/tools/crawler/ && poetry run python desktop_selenium.py --debug_browsers --resp_type debug --ignore_certs"` for a quick check that data can be collected
     - This should take around 2-3m
     - Check `_hp/hp/tools/crawler/logs/desktop-selenium/` for logs, there should be two rows with `Start chrome (128)` and two with `Finish chrome (128)` and no additional rows. The results of these tests can also be seen in the database or checked with the `analysis_demo.py` script
   - Reproduce the basic experiment:
     - TODO (copy from below + verify, there are some issues with dockerized setup e.g. `--no-sandbox`?)
     - Run `(sudo) docker compose exec header-testing-server bash -c "cd /app/_hp/hp/tools/crawler/ && for i in {1..5}; do poetry run python desktop_selenium.py --num_browsers 50 --resp_type basic --ignore_certs; done"`
   - Reproduce the parsing experiment:
     - TODO
   - Reproduce the updated browser experiment and other notes:
     - TODO
   - The test runner can be also used outside of the docker container for efficiency:
     - Requires `python 3.11.5`, `poetry`, various browser dependencies and if run on a server without a screen `Xvfb` installed. Check `setup.bash` on how to install them (verified to work on Ubuntu 22.04)
     - Then install all dependencies: `cd _hp && poetry install`
     - Lastly, the modified WPT server needs to be reachable. One option is to modify `/etc/hosts/` to point the required hosts to the docker container  (see `_hp/host-config.txt`)
     - Then `poetry run python desktop_selenium.py --help` can be used to see all settings of the test runner and then executed as wanted
4. (Optional) Test runner for macOS browser
   - Requires access to a macOS device with a display
   - The Safari version is bound to the operating system, for an exact reproduction of our results, macOS devices in the correct version are required. To test the test runner on macOS, the used version can be updated in `desktop_selenium.py`
   - Requirements: `python=3.11.5`, `poetry` (see `setup.bash`) and access to the modified WPT server
   - Install `poetry install`
   - Run: TODO, copy from below (some manual steps in Safari are required) (Note: the device is not fully usable during the testing)
5. (Optional) Test runner for iPadOS browser
  - Requires access to iPadOS devices (in the correct version)
  - Only works in a setup where the server is setup to be reachable from the iPadOS (e.g., via public internet) and the server needs valid certificates
  - Run: TODO, copy from below
6. (Optional) Test runner for emulated Android browsers
   - Requires access to a linux machine
   - TODO: copy from below, install and run


----
Old review below:

## Setup and Start the Header Testing Server
- Create a fresh Ubuntu22 container/VM: `lxc launch ubuntu:22.04 <name>` and connect to it `lxc exec <name> bash` (Other environments might also work but are not tested)
  - Switch to the ubuntu user: `su - ubuntu`
  - Clone this repository: `git clone git@github.com:header-testing/header-testing.git`
  - Run the setup file: `cd header-testing/_hp`, `./setup.bash` (reopen all terminals or run `source ~/.bashrc` afterwards)
  - Start a postgres instance somewhere that is reachable from this container.
  - Configure DB settings in [config.json](_hp/hp/tools/config.json); Make sure that a database with the correct name already exists
  - Setup the database: `cd _hp/hp/tools && poetry run python models.py`
  - Setup certs: either remove `.demo` from the files in `_hp/hp/tools/certs/` to use self-signed certs or add your own certs here
- Create the basic and parsing responses: Run `cd _hp/hp/tools && poetry run python create_responses.py` (basic), run `cd analysis && poetry run jupyter-lab` and execute `response_header_generation.ipynb` to generate the parsing responses.
-  Start the WPT server first (from the top-most folder): `poetry run -C _hp python wpt serve --config _hp/wpt-config.json`
- Manually check if the server and the tests are working: Visit http://sub.headers.websec.saarland:80/_hp/tests/framing.sub.html and confirm that tests are loaded and executed.
- Optional: Run tests to check that everything is working correctly: `poetry run -C _hp pytest _hp`
- Optional: Change the used domains in [_hp/wpt-config.json](_hp/wpt-config.json) and [_hp/host-config.txt](_hp/host-config.txt)
- To run it inside a Docker container: `docker compose up --build`. This should spin up the server (as we use the same docker for the linux desktop browsers, the container is configured as `platform: linux/amd64` meaning it is emulated and slow on AppleSilicon)


## Reproduce or Enhance our Results
In the following, we describe how to reproduce all our results from the paper.
By slightly adapting the configuration and updating the used browsers, it is also possible to run our tool chain on new/other browser configurations.

### Desktop Browsers (Linux Ubuntu)
- Note: if running in the docker container on AppleSilicon only headless browser will work as Xvfb cannot be emulated
- Execute `cd _hp/hp/tools/crawler`
- If using self-signed certs, add `--ignore_certs` to all commands.
- Run the following for a quick test run to check that everything is working: `poetry run python desktop_selenium.py --debug_browsers --resp_type debug`
- Full run:
  - If the test environment cannot support 50 parallel browsers, reduce the `num_browsers` parameter.
  - Run all basic tests: `for i in {1..5}; do poetry run python desktop_selenium.py --num_browsers 50 --resp_type basic; done`
  - Run all parsing tests: `for i in {1..5}; do poetry run python desktop_selenium.py --num_browsers 50 --resp_type parsing; done`
  - It can happen that some tests do not have 5 results after the above commands due to timeouts and similar, to ensure that all tests have at least 5 results run the below commands.
  - Run missing basic tests: `poetry run python create_repeat.py --selection_str "\"Response\".resp_type = 'basic' and \"Browser\".os = 'Ubuntu 22.04'"` and `poetry run python desktop_selenium.py --num_browsers 50 --run_mode repeat --max_urls_until_restart 50`
  - Run missing parsing tests: `poetry run python create_repeat.py --selection_str "\"Response\".resp_type = 'parsing' and \"Browser\".os = 'Ubuntu 22.04'"` and `poetry run python desktop_selenium.py --num_browsers 50 --run_mode repeat --max_urls_until_restart 50`
  - To reproduce the results of the second experiment run with newer browsers, add `--new_browsers`
  - To run our tests on newer browsers, adjust the browser config in `desktop_selenium.py`
- Optional configuration to debug headfull browsers on the Ubuntu container:
```bash
Xvfb :99 -screen 0 1920x1080x24 &
x11vnc -display :99 -bg -shared -forever -passwd abc -xkb -rfbport 5900
export DISPLAY=:99 && fluxbox -log fluxbox.log &
```

### Desktop Browsers (MacOS)
- Have to be run on a real MacOS device, we used version 17.3, 17.5, and 18.2 (adjust the browser configuration in `desktop_selenium.py` if using another version).
- On MacOS the `setup.bash` script does not work. Instead manually install [poetry](https://python-poetry.org/docs/#installing-with-the-official-installer) and run `poetry install` in the `_hp` directory and append the entries from [host-config.txt](_hp/host-config.txt) to `/etc/hosts`.
- Make sure that the MacOS device can reach the Header Testing server. (Alternatively it could also work to run the header testing server and the database locally on the MacOS device).
- To be able to use Selenium with Safari, one needs to activate remote automation. In Safari: develop -> developer settings -> developer settings -> allow remote automation.
- If using self-signed certs, add `--ignore_certs` to all commands.
- Execute `cd _hp/hp/tools/crawler`
- Full run:
  - On the Header Testing Server:
    - Create test-page-runner pages for basic tests: `poetry run python desktop_selenium.py --resp_type basic --gen_page_runner --max_urls_until_restart 100`
    - Create test-page-runner pages for parsing tests: `poetry run python desktop_selenium.py --resp_type parsing --gen_page_runner --max_urls_until_restart 1000`
    - The above two commands output a path similar to `basic-MaxURLs100-MaxResps10-MaxPopups100-53332b.json`, make sure to copy the files to the MacOS device and replace the file name in the following commands.
  - On the MacOS device:
    - Run the basic tests: `for i in {1..5}; do poetry run python desktop_selenium.py --num_browsers 1 --page_runner_json <basic-test-json> --timeout_task 1000; done`
    - Run the parsing tests: `for i in {1..5}; do poetry run python desktop_selenium.py --num_browsers 1 --page_runner_json <parsing-test-json> --timeout_task 10000; done`
    - Add `--new_browsers` for running on 18.2
  - It can happen that not all tests recorded 5 results, thus run the following to ensure that all tests are executed at least 5 times:
    - For the basic tests: `poetry run python create_repeat.py --selection_str "\"Response\".resp_type = 'basic' and \"Browser\".os != 'Android 11'"` and `poetry run python desktop_selenium.py --num_browsers 1 --run_mode repeat --timeout_task 10000`
    - For the parsing tests: `poetry run python create_repeat.py --selection_str "\"Response\".resp_type = 'parsing' and \"Browser\".os != 'Android 11'"` and `poetry run python desktop_selenium.py --num_browsers 1 --run_mode repeat --timeout_task 10000`

### Mobile Browsers (Android)
- Execute `cd _hp/hp/tools/crawler`
- To run the tests on Android devices, first some emulators have to be set up and the browsers have to be installed and configured:
  - Download the Android SDK Command-Line Tools (command line tools only) form the Android Studio downloads page and unpack it in a folder called `AndroidSDK` (see https://developer.android.com/tools/sdkmanager ).
  - Add `cmdline-tools` to the path: e.g., `export PATH=<path-to-AndroidSDK>/cmdline-tools/latest/bin/:$PATH`
  - Install `platform-tools` and `emulator`: `sdkmanager platform-tools emulator`
  - Add `platform-tools` to the path: e.g., `export PATH=<path-to-AndroidSDK>/platform-tools/:$PATH`
  - Add `emulator` to the path: e.g., `export PATH=<path-to-AndroidSDK/emulator/:$PATH`
  - Install and create a Pixel 3 Device with Android 11 installed:
    - Run `sdkmanager --install "platforms;android-30" "system-images;android-30;google_apis;x86_64`
    - Run `avdmanager create avd -n device_1 -k "system-images;android-30;google_apis;x86_64" --device "pixel_3" --force`
  - Install `scrcpy` to be able to interact with the Android Device: `apt install scrcpy`
  - Browser Installation and Setup:
    - Start the emulator: `emulator @device_1 -screen multi-touch -no-window -port 5554&`
    - Attach with `scrcpy`
    - Setup required browsers:
      - Download the corresponding APKs:
        - Chrome: https://www.apkmirror.com/apk/google-inc/chrome/chrome-121-0-6167-180-release/ (x86 APK)
        - Brave: https://www.apkmirror.com/apk/brave-software/brave-browser/brave-browser-1-62-165-release/ (x86 APK)
        - Firefox Beta: https://www.apkmirror.com/apk/mozilla/firefox-beta/firefox-beta-123-0b9-release/ (universal APK)
      - Install the APKs:
        - Run `adb -s emulator-5554 install -r -g <path to apk>` for all three APKs
    - Additional browser config (popups need to be allowed):
      - Open all browsers and go through their setup screen, then allow popups in all of them:
      - Open chrome: By default, Pop-ups and redirects are blocked. To allow, go to `Settings/Site Settings/ Turn on the Pop-Ups and Redirects option`
      - Open brave: By default, Pop-ups and redirects are blocked. To allow, go to `Settings/Site Settings/ Turn on the Pop-Ups and Redirects option`
      - Open firefox_beta: To allow popups, go to `about:config`, and then set `dom.disable_open_during_load` to false.
    - Stop the emulator: `adb -s emulator-5554 emu kill`
- The emulators also need to be able to reach the Header Testing server.
- Issue: currently does not work with the self-signed certs, make sure to have correct certs setup
- Full run:
  - Run the basic tests: `for i in {1..5}; do timeout 15m poetry run python android_intent.py -browsers chrome -repeat 1 -num_devices 30 -type basic -auto_restart; done`
  - Run the parsing tests: `for i in {1..5}; do timeout 6h poetry run python android_intent.py -browsers chrome -repeat 1 -num_devices 30 -type parsing -auto_restart; done`
  - Similarly to the other tests, it could happen that not all tests collected 5 results, thus run the following to rerun some tests.
  - Create the repeat file for the basic tests: `poetry run python create_repeat.py --selection_str "\"Response\".resp_type = 'basic' and \"Browser\".os = 'Android 11'"`
  - Run them: `poetry run python android_intent.py -browsers all -repeat 1 -num_devices 30 -url_json repeat.json -auto_restart`
  - Create the repeat file for the parsing tests: `poetry run python create_repeat.py --selection_str "\"Response\".resp_type = 'parsing' and \"Browser\".os = 'Android 11'"`
  - Run them: `poetry run python android_intent.py -browsers all -repeat 1 -num_devices 30 -url_json repeat.json -auto_restart`


### Mobile Browsers (iPadOS)
- To run the tests on iPadOS a real iPad is required. The iPad also needs to be able to reach the Header Testing Server.
- Issue: currently does not work with the self-signed certs, make sure tho have correct certs setup
- On the iPad install Chrome (uses WebKit) and allow popups (Open Settings -> Content-Settings -> Block Pop-Ups -> Off)
- Full run:
  - On the Header Testing server:
    - Execute `cd _hp/hp/tools/crawler`
    - Add the DB entry: adjust the browser/os version info and then run `poetry run python create_ipados_browser.py` and note the returned browser_id
    - Generate URLs to visit:
      - Basic: `poetry run python desktop_selenium.py --resp_type basic --gen_page_runner --max_urls_until_restart 10000 --gen_multiplier 5`
      - Parsing: `poetry run python desktop_selenium.py --resp_type parsing --gen_page_runner --max_urls_until_restart 100000 --gen_multiplier 5`
  - On the iPad:
    - Visit the URLs generated by the above commands and add `?browser_id=<browser_id>` to the URL, example: `https://sub.headers.websec.saarland/_hp/tests/test-page-runner-1_ed4f3b-0.html?browser_id=16`
  - To ensure that all tests have at least 5 results run the following:
    - On the server:
      - Generate the repeats: `poetry run python create_repeat.py --selection_str "\"Response\".resp_type = 'parsing' and \"Browser\".os != 'Android 11'"`
      - Create a page-runner URL containing all URLs: `poetry run python create_page_runner_repeats.py --browser_id <browser_id>`
    - On the iPad:
      - Visit the page-runner URL

### Analysis:
  - Execute `cd _hp/hp/tools/analysis && poetry run jupyter-lab`
  - Open and run `_hp/hp/tools/analysis/analysis_may_2024.ipynb` or `_hp/hp/tools/analysis/analysis_december_2024.ipynb`
  - Note that the analysis is tailored towards our results from May or December 2024 and some small changes might be required if run on new data

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
