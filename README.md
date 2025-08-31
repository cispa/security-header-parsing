# Software for: Head(er)s Up! Detecting Security Header Inconsistencies in Browsers
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16890359.svg)](https://doi.org/10.5281/zenodo.16890359)

## General Info
This repository contains all code for our paper: "Head(er)s Up! Detecting Security Header Inconsistencies in Browsers" published at [ACM CCS 2025](https://doi.org/10.1145/3719027.3765119).

**The software consists of three main parts:**
- A server component serving HTML test pages (e.g., framing test-page) and many HTTP responses for each tested security header.
- Browser runners visiting the HTML test pages. Browser runners for Linux, macOS, Android (Emulators on Linux), and iPadOS (native) exist.
- Jupyter analysis scripts analysing the collected data

**Table of Contents:**
- [Quickstart](#quickstart): Minimal setup of server component and browser runner
- [Usage](#usage): Reference on how to use and adapt the code to run security header consistency tests in browsers
- [Reproduction](#reproduction): Instructions on how to reproduce the results presented in the paper
- [Inventory](#inventory): List of the contents of this repository

**Additional Notes:**

This repository is a fork of [WPT](https://github.com/web-platform-tests/wpt), the original README can be found [here](./README_original.md).
All test and analysis code for our paper can be found in the [_hp](./_hp/README.md) directory.
Our modified version of the wptserve HTTP server implementation can be found in the `tools/serve` and `tools/wptserve` directories. All other directories are untouched and are required for `wptserve` to run, we removed the other WPT directories for clarity.

## Quickstart
In this section, we explain how to setup our custom WPT-HeaderTesting backend server and run some small tests with it.
- Prequistes:  Working installation of [Docker](https://docs.docker.com/get-started/get-docker/) on Linux or macOS. Ports 80, 443, 5432, and 8888 have to be available on the host machine or these exposed ports in [docker-compose.yml](docker-compose.yml) have to be disabled or changed.
- Installation: Run `docker compose up` this starts a database, configures the HTTP responses, and starts our modified WPT-HeaderTesting server (the initial startup takes a couple of minutes)
- Verify setup: Run `docker compose exec header-testing-server bash -c "poetry run -C _hp pytest /app/_hp"`: All tests should pass and the output should look similar to: `11 passed in 23.73s`
- Manual checks:
  - The server is now serving all the test pages and responses and should be available on the host (by default it binds to port 80 and 443). 
  - Visit: http://localhost/_hp/common/frame-script-csp.js in a browser
  - Run `curl -I http://localhost/_hp/common/empty.html` and `curl -I --insecure https://localhost/_hp/common/empty.html` (our dummy certificates are not valid, thus `--insecure` is required) on the host should return a response from `BaseHTTP/0.6 Python/3.11.5`
- Demo run of the desktop linux test-runner in docker:
  - Run: `docker compose exec header-testing-server bash -c "cd /app/_hp/hp/tools/crawler/ && poetry run python desktop_selenium.py --debug_browsers --resp_type debug --ignore_certs"` for a quick check that data can be collected, this should take around 2-3m.
  - Run: `docker compose exec header-testing-server bash -c 'cd /app/_hp/hp/tools/crawler/logs/desktop-selenium/; cat "$(ls -t | head -n1)"'` to verfiy the log file, there should be two rows with `Start chrome (128)` and two with `Finish chrome (128)` and no additional rows.
- Analysis:
  - Run: `docker compose exec header-testing-server bash -c "cd _hp/hp/tools/analysis && poetry run python analysis_demo.py"` to get some basic statistics about the test runs executed by the unit tests and running browser-test-runners.
- For a productive use of the server and the test runners, we refer to the [usage section](#usage).

## Usage
In the following, we explain how to use this software to collect security header inconsistencies for (new) browsers and headers. This section assumes the [quickstart](#quickstart) was followed and first explains how to run and modify the WPT-HeaderTesting server and then how to use the various browser-runners.

### WPT-HeaderTesting Server
- Starting the server: Run `docker compose up -d` to start the server. Optionally modify the [docker-compose.yml](docker-compose.yml) for your needs, e.g., make the database available on the outside, disable the platform mode on non `linux/amd64` platforms for increased efficiency, or change ports.
- (Optional) Adding responses:  modify [create_responses](_hp/hp/tools/create_responses.py) to add `basic` responses, modify [response_header_generation.py](_hp/hp/tools/response_header_generation.py) to add `parsing` responses
- (Optional) Add new HTML tests: 
  - If you want to add a test to an existing feature, you only need to open a test file in [_hp/tests/](_hp/tests/), add the testcode and add the test to `test_declarations`
  - If you want to add a new test feature: add a new test file in [_hp/tests/](_hp/tests/), add supporting files in [_hp/common/](_hp/common/), add the server logic in [_hp/server/responses.py](_hp/server/responses.py), add responses for this feature (see above `adding responses`)
- (Optional) Change the `host` domain of the server:
  - By default the server is available at `(sub.)(sub.)headers.websec.saarland` and `(sub.)(sub.)headers.webappsec.eu` within the docker network and exposed to the host at port 80 and 443 (with a self-signed certificate)
  - When running browser runners outside of the docker network, it is possible to keep this default config by mapping these hosts to the docker container running the server: e.g., if the dockerized WPT-HeaderTesting server runs on the same host where you want to run some browser test runners, you can add append the config of [host-config.txt](_hp/host-config.txt) to your `/etc/hosts` file such that the browser runners resolve these hosts to the docker container. Additionally, all browser runners have to be configured to accept the self-signed certificate (e.g., `--ignore_certs` for the linux browser runner).
  - If the tested browser has no option to accept self-signed certificates or adapting the network to point these hosts to the WPT-HeaderTesting server is not possible or difficult (e.g., on iPadOS), it is also possible to change the hosts:
    - Requirements: two domains (A, B) with subdomains `sub.[A|B]` and `sub.sub.[A|B]` pointing to the host where the WPT-HeaderTesting server is running
    - Change the `browser_host` and `alt_host` in [wpt-config.json](_hp/wpt-config.json)
    - Change the hosts in [host-config.txt](_hp/host-config.txt)
    - Place your certificate and key that is valid for your domains in [_hp/hp/tools/certs/](_hp/hp/tools/certs/) and update the certificate and key path in [wpt-config.json](_hp/wpt-config.json)
    - Lastly, recreate the dockerized server to take your updated config into account. Note that responses also have to be recreated. Running `docker compose down -v --rmi all`, `docker compose build --no-cache`, and `docker compose up -d` should ensure that everything was deleted and your new config is taken.
    - If the host is accessible from the web: Note that while the WPT-HeaderTesting server is good at sending invalid HTTP responses for testing, it is not very robust when receiving invalid requests which you will receive from time to time when it is web accessible. It can be that the server get stuck when receiving such requests, we thus provide an alternative entrypoint script in [docker-compose.yml](docker-compose.yml) that automatically restarts the server every 600 seconds.

### Browser Runners
Our WPT-HeaderTesting server can be used with any browser runner that is able to reach the server and it is also possible to manually execute the tests in the browser.
In the following, we provide instructions on how to use the browser runners we developed for our experiments.

#### Linux
The demo in [quickstart](#quickstart) used our Linux desktop test runner. It is possible to run the test runners in docker, but we observed multiple issues with it and thus recommend running the browsers outside of docker and have not tested more than the demo runs in docker.
- Prerequisites: Linux installation (native, VM, lxc); tested with Ubuntu22.04, similar installation likely also work
  - We recommend to use a fresh Ubuntu22 container: Run `lxc launch ubuntu:22.04 <name>`
  - Connect to the container: Run `lxc exec <name> bash`
  - Switch to the Ubuntu user: Run `su - ubuntu`
  - The machine needs to be able to reach the database: if running the WPT-HeaderTesting on the same machine, change the DB connection string in [config.json](_hp/hp/tools/config.json) to `postgresql+psycopg2://header_user:header_password@localhost:5432/http_header_demo` otherwise adapt as necessary (port forwards, expose your db, ...)
- Installation steps (should not be run as root user):
  - Clone this repository: Run `git clone git@github.com:header-testing/header-testing.git`
  - Install the necessary components:
    - We recommend running `cd header-testing/_hp`, `./setup.bash` (reopen all terminals or run `source ~/.bashrc` afterwards)
    - Alternativly the necessary tools can be installed manually (Browser dependencies, Xfvb and x11vnc, poetry, python3.11.5, ...) and then run `poetry install`
- Use the browser runner:
  - Go to the correct location: Run `cd _hp/hp/tools/crawler`
  - Check the options to run the tool: `poetry run python desktop_selenium.py --help`
  - Notes:
    - Most browsers are managed automatically by selenium and downloaded automatically when first used. Brave is not managed by selenium and has to be downloaded manually: for instructions on how to download the correct brave versions, check the comments in [desktop_selenium.py](_hp/hp/tools/crawler/desktop_selenium.py)
    - The used browser (versions) are specified in the `config` variable in [desktop_selenium.py](_hp/hp/tools/crawler/desktop_selenium.py) and can be changed there.
    - If using self-signed certs, add `--ignore_certs` to all commands.
    - For running headful browsers on a machine without a real display:
      - Run `Xvfb :99 -screen 0 1920x1080x24 & && export DISPLAY=:99 && fluxbox -log fluxbox.log &`
      - To be able to observe the browser, additionally run: `x11vnc -display :99 -bg -shared -forever -passwd abc -xkb -rfbport 5900` and then connect to it with any VNC viewer on port 5900
  - Example commands:
    - Run the debug test responses with the debug browsers: `poetry run python desktop_selenium.py --debug_browsers --resp_type debug --ignore_certs` (2-3m)
    - Run the basic test responses with the browsers of the second browser run with 10 parallel browsers: `poetry run python desktop_selenium.py --new_browsers --resp_type basic --ignore_certs --num_browsers 10` (~15m)

#### macOS
The test runner on macOS is in general the same as the one on Ubuntu.
- Prerequisites:
  - Real macOS device with a display
  - Poetry: [poetry installation instructions](https://python-poetry.org/docs/#installing-with-the-official-installer) and Python 3.11 (we recommend to use pyenv for that `brew install pyenv` and `pyenv install 3.11`)
  - The macOS devices needs to reach the WPT-HeaderTesting server at the specified host. When running the WPT-HeaderTesting server with the default config on the same macOS machine, you can append the entries from [host-config.txt](_hp/host-config.txt) to `/etc/hosts`, otherwise adapt them as necessary.
  - The macOS device needs to be able to reach the database: if running the WPT-HeaderTesting on the same machine, change the DB connection string in [config.json](_hp/hp/tools/config.json) to `postgresql+psycopg2://header_user:header_password@localhost:5432/http_header_demo` otherwise adapt as necessary (port forwards, expose your db, ...).
  - Configure Safari to be usable with Selenium: In Safari click on `Develop`, then on `Developer Settings`, then again on `Developer/Developer Settings` and then activate `Allow remote automation`
- Use the browser runner:
  - The usage of the browser runner is identical to on linux.
  - Run `poetry python desktop_selenium.py --help` to see all options.
  - Notes:
    - The `--ignore_certs` option is not working in Safari, thus either setup the WPT-HeaderTesting server with a valid certificate or trust the self-signed certificate in macOS Keychain.
    - The Safari version is bound to the OS version and the version has to be updated in [desktop_selenium.py](_hp/hp/tools/crawler/desktop_selenium.py), e.g., set it to `18.6` for macOS 17.6.
    - Selenium can only automate a single Safari instance at a time (this is a Safari restriction), thus one always needs to set `--num_browsers 1`
    - Everytime a new test is loaded, the Safari instance is receiving focus on MacOS. We try to minimize the annoyance by moving the Safari window (almost)out of the visible screen. However, one might still accidentally click or send other events to the automated Safari window. If that happens, the automation pauses (this is another Safari restriction) and one has to click on `Continue automation`. We recommend to use testing devices that only run the tests and are not otherwise used. 
  - Example run: `poetry run python desktop_selenium.py --resp_type debug --num_browsers 1`

#### Android (Emulated)
We provide a test runner that can be used with emulated Android devices to efficiently run the tests in parallel.
- Prerequisites:
  - A powerful server to run the emulated android devices on, in particular hardware accelaration has to be available on the system. We tested it on Ubuntu 22.04, but other host operating systems should also work.
  - The WPT-HeaderTesting server has to be setup to be reachible from the emulators via public DNS and the server needs valid certificates. Note: it is recommended to configure your firewall such that it only allows local access.
  - The machine where the emulators are started also needs to have the poetry project installed 
  - Download the Android SDK Command-Line Tools (command line tools only) and set it up (see https://developer.android.com/tools/sdkmanager for full documentation):
    - Run `wget <link-from-downloads-page>` [Android Studio downloads page](https://developer.android.com/studio#command-line-tools-only)
    - Unzip it: `unzip cmdlinetools-linux-<version_latest>.zip`
    - Create a folder and move it there: `mkdir -p androidsdk/cmdline-tools/latest/ && mv cmdline-tools androidsdk/cmdline-tools/latest`
    - Add `cmdline-tools` to the path: Run `export PATH=$(pwd)/androidsdk/cmdline-tools/latest/bin/:$PATH`
    - Install `platform-tools` and `emulator`: Run `sdkmanager platform-tools emulator`
    - Add `platform-tools` to the path: e.g., `export PATH=$(pwd)/androidsdk/platform-tools/:$PATH`
    - Add `emulator` to the path: e.g., `export PATH=$(pwd)/androidsdk/emulator/:$PATH`
  - Install and create a Pixel 3 Device with Android 11 installed (for efficient runs, create multiple devices such that the tests can be run in parallel):
    - Run `sdkmanager --install "platforms;android-30" "system-images;android-30;google_apis;x86_64"`
    - Run `avdmanager create avd -n device_1 -k "system-images;android-30;google_apis;x86_64" --device "pixel_3" --force`
  - Install `scrcpy` to be able to interact with the Android Device: `sudo apt install scrcpy`
  - Browser Installation and Setup:
    - Start the emulator: Run `emulator @device_1 -screen multi-touch -no-window -port 5554&`
    - Attach to the device: Run `scrcpy`
    - Setup required browsers:
      - Download the corresponding APKs, for example manually from apkmirror:
        - Chrome 121: https://www.apkmirror.com/apk/google-inc/chrome/chrome-121-0-6167-180-release/` (x86 APK)
        - Brave 1.62.165: https://www.apkmirror.com/apk/brave-software/brave-browser/brave-browser-1-62-165-release/ (x86 APK)
        - Firefox Beta 123: https://www.apkmirror.com/apk/mozilla/firefox-beta/firefox-beta-123-0b9-release/ (universal APK)
      - Install the APKs: Run `adb -s emulator-5554 install -r -g <path to apk>` for all APKs
    - Additional browser config (popups need to be allowed):
      - Open all browsers and go through their setup screen, then allow popups in all of them:
      - Open chrome: By default, Pop-ups and redirects are blocked. To allow, go to `Settings/Site Settings/ Turn on the Pop-Ups and Redirects option`
      - Open brave: By default, Pop-ups and redirects are blocked. To allow, go to `Settings/Site Settings/ Turn on the Pop-Ups and Redirects option`
      - Open firefox_beta: To allow popups, go to `about:config`, and then set `dom.disable_open_during_load` to false.
- Run browser test in them:
  - Run `cd _hp/hp/tools/crawler`
  - If you install other apks, update [android_config.json](_hp/hp/tools/crawler/android_config.json)
  - Change the DB config [config.json](_hp/hp/tools/config.json) such that the script can reach the DB. If the WPT-HeaderTesting server is running on the same device, change `postgres` to `localhost`.
  - Run `poetry run python android_intent.py --help` to see all available settings
  - Run `poetry run python android_intent.py -browser chrome -num_devices 1 -type debug -auto_restart` for a quick demo
- If you want to stop the emulator: Run `adb -s emulator-5554 emu kill`

#### ipadOS/generic Runner
In addition to the above browser runners that require Selenium, AndroidSDK, and similar, we also provide a generic browser runner that only requires to visit a single orchestration URL that then uses popups to execute each test. We used this test runner for the ipadOS runs, where we manually entered the URL in the browser.
- Notes:
  - The browser where the test page is opened needs to be able to reach the WPT-HeaderTesting server.
  - If the server has not valid certificates, the browser needs to be configured to ignore certificate errors or the self-signed certificate has to be trusted.
  - Popups needs to be allowed in the browser. For our iPad runs, we used the Chrome browser (currently still uses WebKit). On the iPad, open Chrome and go to `Open Settings` -> `Content-Settings` -> `Block Pop-Ups` and toggle it `off`.
- Usage instructions:
  - On the WPT-HeaderTesting server:
    - Adjust [create_generic_browser.py](_hp/hp/tools/crawler/create_generic_browser.py) to fit to the browser/os version info, you are using and then run `docker compose exec header-testing-server bash -c "cd _hp/hp/tools/crawler && poetry run python create_generic_browser.py"` and note down the `browser_id` printed. 
    - Run: `docker compose exec header-testing-server bash -c "cd _hp/hp/tools/crawler && poetry run python desktop_selenium.py --gen_page_runner --resp_type debug --max_urls_until_restart 10000 --gen_multiplier 1"` and note the returned URLs (they are also saved ina file in the `crawler` folder)
      - `--resp_type` specifies the response type that should be tested `debug, basic, parsing`
      - `--max_urls_until_restart` specifies how many URLs are opened on maximum on one top-level test page. If this is high you only need to visit a single URL in the browser, but there could be issues with state accumulation. If this is low, many URLs that you have to visit somehow are generated. Note that there are always at least two URLs to visit, as we do not mix tests on HTTP and HTTPS.
      - `--gen_multiplier` specifies how often the same test is executed, to deal with noise it is recommened to run all tests several times
  - On your device: Finally visit the URLs printed (e.g., by manually pasting them into the browser URL bar) and append `?browser_id=<browser_id>` to the URL. Example: `https://sub.headers.websec.saarland/_hp/tests/test-page-runner-1_ed4f3b-0.html?browser_id=16`

## Reproduction
We provide the full analysis scripts (including the output), the collected dataset [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16996059.svg)](https://doi.org/10.5281/zenodo.16996059), and instructions on how to rerun the analysis scripts and how we collected the data to enable full reproduction of this work.
We note that a full reproduction of this work is a significant effort and refer most readers to the [usage section](#usage) instead and encourage them to use our test runners and WPT-HeaderTesting server to test new browser versions and new security headers.

The files [analysis_may_2024.ipynb](_hp/hp/tools/analysis/analysis_may_2024.ipynb) (original analysis) and [analysis_december_2024.ipynb](_hp/hp/tools/analysis/analysis_december_2024.ipynb) (updated with additional browser versions) contain the full analysis used in our paper, including the output of the analysis. They can be viewed directly on GitHub or a jupyter server can be started to view them in Jupyter Lab. Note that the clustering output uses Jupyter Widgets that cannot be saved fully.

We also provide instructions to rerun the analysis scripts such that the clustering output can be seen and to verify that the output is correct. Note that re-executing the analysis scripts require a large amount of RAM available for the docker container (~60GB per script; they can be run indepedently) and take around 30m to execute. 
- Download the database: `curl https://zenodo.org/records/16996059/files/http_header_original.dump\?download\=1 --output data/http_header_original.dump` [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16996059.svg)](https://doi.org/10.5281/zenodo.16996059)
- Import the database into your local postgres: `docker compose exec postgres psql -U header_user -d http_header_demo -c "CREATE DATABASE http_header_original;"` and `docker compose exec -T postgres pg_restore -U header_user -d http_header_original -v /tmp/data/http_header_original.dump`
- Start the jupyter-lab: `docker compose exec header-testing-server bash -c "cd /app/_hp/hp/tools/analysis && poetry run jupyter-lab --allow-root --ip 0.0.0.0"` and access the URL printed on your local browser
- Run the analysis scripts in jupyter lab and analyze the outputs: the `analysis_december_2024.ipynb` notebook contains the full analysis including the original and the updated browser runs, thus usually it should be enough to use that.

For instructions on the commands we used to collect the above dataset and on how to reproduce it, we refer to the [Artifact Appendix](TODO) and the [reproduction instructions](REPRODUCTION.md).

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
  - `pyproject.toml`, `wpt-config.json`, `host-config.txt`, `setup.bash`: Various config files for the project
- `tools/`: Contains modified `wptserve`
- `data/`: Directory to download the original database dump to
- `README.md`: This file
- `README_original.md`: The original WPT README
- `REPRODUCTION.md`: Lists the commands used to collect the data for the paper
- `Dockerfile`, `docker-compose.yml`, `entrypoint.sh`: Docker files for a quick setup of this project
- `server.py`: Script to run the `wptserve` with automatic restarts
- Other directories are used by `wptserve` internally but are not modified

## Contact

If there are questions about our tools or paper, please either file an issue or contact `jannis.rautenstrauch (AT) cispa.de`.

## Research Paper

The paper is available at the [ACM Digital Library](https://doi.org/10.1145/3719027.3765119). 
You can cite our work with the following BibTeX entry:
```latex
@inproceedings{rautenstrauch2025header,
 author = {Rautenstrauch, Jannis and Nguyen, Trung Tin and Ramakrishnan, Karthik and Stock, Ben},
 booktitle = {ACM CCS},
 title = {{Head(er)s Up! Detecting Security Header Inconsistencies in Browsers}},
 year = {2025},
 doi = {https://doi.org/10.1145/3719027.3765119},
}
```

