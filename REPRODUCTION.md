# Reproduction Instructions

The following presents the commands that we used to collect the data presented in the paper and some notes for the browser runs.
Please first read the full [README](README.md), before using this file.
Note that for using the commands in this file, all browser runners on all devices need to be able to reach the WPT-HeaderTesting server under the hostnames specified in [wpt-config.json](_hp/wpt-config.json) and [host-config.txt](_hp/host-config.txt). Additionally, the server needs to have valid certificates for these hosts or the clients have to be configured to ignore certificate errors or trust the self-signed certificate: `--ignore_certs` for Linux Ubuntu, for the other operating systems the certificates have to be trusted on the OS level.

## Desktop Browsers (Linux Ubuntu)
- Originally run on an `lxc` container with Ubuntu 22.04
- All commands are run from  the `_hp/hp/tools/crawler` directory
- The [pyproject.toml](_hp/pyproject.toml) has to be installed with poetry
- The server requires a (virtual) display: we used `Xvfb :99 -screen 0 1920x1080x24 &`, `x11vnc -display :99 -bg -shared -forever -passwd abc -xkb -rfbport 5900`, `export DISPLAY=:99 && fluxbox -log fluxbox.log &`
- We used a powerful container (100 vCPUs, 256GB RAM) to execute 50 browsers in parallel. If the container is less powerful, decrease the `--num_browsers` parameter. The timing estimates assume `50` browsers are used in parallel and that the setup is complete.
- The Brave browser is not automatically installed by Selenium, follow the installation instructions in [desktop_selenium.py](_hp/hp/tools/crawler/desktop_selenium.py).
- Commands to reproduce the `basic` responses data (20 person-minutes, 30 compute-minutes):
  - Run `for i in {1..5}; do poetry run python desktop_selenium.py --num_browsers 50 --resp_type basic; done`, should take around 13m for all 5 iterations
  - It can happen that some tests do not have 5 results after the above commands due to timeouts and similar, to ensure that all tests have at least 5 results run the below commands:
    - Create a `repeat.json` file with all tests that have to be rerun: `poetry run python create_repeat.py --selection_str "\"Response\".resp_type = 'basic' and \"Browser\".os = 'Ubuntu 22.04'"`
    - Run `poetry run python desktop_selenium.py --num_browsers 50 --run_mode repeat --max_urls_until_restart 50` to reexecute these tests
    - It can happen that some tests are still missing results. Run the `create_repeat.py` command again to verify and potentially run the `--run_mode repeat` command until all tests have 5 responses
  - The above commands collect data for the original set of browsers. To collect the data for the browsers added in December, run the above `desktop_selenium.py` commands again with the additional flag `--new_browsers` (`create_repeat.py` does not require this flag)
- Commands to reproduce the `parsing` responses data (45 person-minutes, 6 computer-hours)
  - Run `for i in {1..5}; do poetry run python desktop_selenium.py --num_browsers 50 --resp_type parsing; done`, should take around 5h for all 5 iterations
  - It can happen that some tests do not have 5 results after the above commands due to timeouts and similar, to ensure that all tests have at least 5 results run the below commands:
    - Create a `repeat.json` file with all tests that have to be rerun: `poetry run python create_repeat.py --selection_str "\"Response\".resp_type = 'parsing' and \"Browser\".os = 'Ubuntu 22.04'"`
    - Run `poetry run python desktop_selenium.py --num_browsers 50 --run_mode repeat --max_urls_until_restart 50` to reexecute these tests
    - It can happen that some tests are still missing results. Run the `create_repeat.py` command again to verify and potentially run the `--run_mode repeat` command until all tests have 5 responses
  - The above commands collect data for the original set of browsers. To collect the data for the browsers added in December, run the above `desktop_selenium.py` commands again with the additional flag `--new_browsers` (`create_repeat.py` does not require this flag)

## Desktop Browsers (macOS)
- For the original run, a macOS device with macOS 14.5 is required, for the updated browser run a macOS device with macOS 15.2 is required and that device requires a display.
- All commands are run from  the `_hp/hp/tools/crawler` directory
- The [pyproject.toml](_hp/pyproject.toml) has to be installed with poetry
- Make sure that the macOS device can reach the WPT-HeaderTesting server.
- Make sure to configure you device, to not go to sleep/power-safe mode or similar.
- To be able to use Selenium with Safari, one needs to activate remote automation. In Safari: develop -> developer settings -> developer settings -> allow remote automation.
- The macOS device is not usable while running the tests as each time a new popup is opened the Safari window receives auto-focus from macOS.
- For the experiment in the paper, we used a mixture of the generic browser runner (`--gen_page_runner`) and the desktop runner.
- Preparation, has to be executed on the WPT-HeaderTesting server (e.g., prepend the commands with `docker compose exec header-testing-server bash -c "<command>"`):
  - Create generic test-page-runner pages for basic tests: `poetry run python desktop_selenium.py --resp_type basic --gen_page_runner --max_urls_until_restart 100`
  - Create generic test-page-runner pages for parsing tests: `poetry run python desktop_selenium.py --resp_type parsing --gen_page_runner --max_urls_until_restart 1000`
  - The above two commands output a path similar to `basic-MaxURLs100-MaxResps10-MaxPopups100-53332b.json`, make sure to copy these json files to the macOS device and replace the file name in the following commands.
- Execute the runs:
  - Run the basic tests: `for i in {1..5}; do poetry run python desktop_selenium.py --num_browsers 1 --page_runner_json <basic-test-json> --timeout_task 1000; done`, this takes around 1 hour
  - Run the parsing tests: `for i in {1..5}; do poetry run python desktop_selenium.py --num_browsers 1 --page_runner_json <parsing-test-json> --timeout_task 10000; done`, this takes around 1 week
  - Add `--new_browsers` if running on macOS 15.2
- Ensure that all tests have 5 results:
  - For the basic tests:
    - Excute on the WPT-HeaderTesting server: `poetry run python create_repeat.py --selection_str "\"Response\".resp_type = 'basic' and \"Browser\".os != 'Android 11'"`, the output is a `repeat.json` file that has to be copied to the macOS device. (This command requires that the Desktop Linux browsers data collection is finished.)
    - Execute on the macOS device: `poetry run python desktop_selenium.py --num_browsers 1 --run_mode repeat --timeout_task 10000`
  - For the parsing tests:
    - Excute on the WPT-HeaderTesting server: `poetry run python create_repeat.py --selection_str "\"Response\".resp_type = 'parsing' and \"Browser\".os != 'Android 11'"`, the output is a `repeat.json` file that has to be copied to the macOS device. (This command requires that the Desktop Linux browsers data collection is finished.)
    - Execute on the macOS device: `poetry run python desktop_selenium.py --num_browsers 1 --run_mode repeat --timeout_task 10000`

## Mobile Browsers (Android)
- Originally run on a Debian 12.7 server. The machine has to be x86_64 and hardware acceleration has to be available.
- We created 30 Android emulators and installed and configured the browsers as explained in the [README](README.md#android-emulated). 
- All commands are run from  the `_hp/hp/tools/crawler` directory
- The [pyproject.toml](_hp/pyproject.toml) has to be installed with poetry
- Note that the timeouts are 2x for Android (due to speed issues in the emulator) and thus the tests execute slower
- Commands used for collection the data:
  - Run the basic tests: `for i in {1..5}; do timeout 15m poetry run python android_intent.py -browsers chrome -repeat 1 -num_devices 30 -type basic -auto_restart; done`, should take around 30m
  - Run the parsing tests: `for i in {1..5}; do timeout 6h poetry run python android_intent.py -browsers chrome -repeat 1 -num_devices 30 -type parsing -auto_restart; done`, should take around 20h
  - Similarly to the other tests, it could happen that not all tests collected 5 results, thus run the following to rerun these tests:
    - Create the repeat file for the basic tests: `poetry run python create_repeat.py --selection_str "\"Response\".resp_type = 'basic' and \"Browser\".os = 'Android 11'"`
    - Run them: `poetry run python android_intent.py -browsers all -repeat 1 -num_devices 30 -url_json repeat.json -auto_restart`
    - Create the repeat file for the parsing tests: `poetry run python create_repeat.py --selection_str "\"Response\".resp_type = 'parsing' and \"Browser\".os = 'Android 11'"`
    - Run them: `poetry run python android_intent.py -browsers all -repeat 1 -num_devices 30 -url_json repeat.json -auto_restart`
    - Repeat these steps if some tests still do not have 5 results in a browser


## Mobile Browsers (iPadOS)
- The original run used two iPad Air(4th generation) devices with iPadOS 17.3.1
- On the iPad we installed Chrome 122 (uses WebKit) and allowed popups (Open Settings -> Content-Settings -> Block Pop-Ups -> Off)
- Preparation on the WTP-HeaderTesting server (prepend the command with `sudo docker compose exec header-testing-server bash -c "cd _hp/hp/tools/crawler && <command>"`):
    - Run `poetry run python create_generic_browser.py` and note the returned browser_id
    - Generate URLs to visit:
      - Basic: `poetry run python desktop_selenium.py --resp_type basic --gen_page_runner --max_urls_until_restart 10000 --gen_multiplier 5`, the output is a list of URLs to visit (there should be two)
      - Parsing: `poetry run python desktop_selenium.py --resp_type parsing --gen_page_runner --max_urls_until_restart 100000 --gen_multiplier 5`, the output is a list of URLs to visit (there should be two)
- On the iPad:
  - Manually visit the two URLs generated by the above commands and add `?browser_id=<browser_id>` to the URL, example: `https://sub.headers.websec.saarland/_hp/tests/test-page-runner-1_ed4f3b-0.html?browser_id=16`
  - If only one iPad is use, visit the URLs one after the other. The basic tests should take around 1h per URL. The parsing tests take several days.
  - Note: it could be that the browser get stuck, in that case reload the browser or use the below commands to generate only the tests that are still missing, depending on when it got stuck.
- To ensure that all tests have at least 5 results run the following:
  - On the WPT-HeaderTesting:
    - First generate the usual `repeat.json` file: `poetry run python create_repeat.py --selection_str "\"Response\".resp_type = 'parsing' and \"Browser\".os != 'Android 11'"` (Note: this assumes that either the Desktop Linux or Desktop macOS browsers already collected data for all tests)
    - Then create a single page-runner URL containing all URLs from the `repeat.json` file: `poetry run python create_page_runner_repeats.py --browser_id <browser_id>`
  - On the iPad:
    - Visit the page-runner URL
