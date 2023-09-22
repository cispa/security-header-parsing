# HTTP Header Security

- Install WPT
- Update config files
- Run `./wpt serve --config _hp/wpt_config.json`
- DB setup: `cd _hp/tools`, `python models.py`
- ...
- Visit: http://headers.websec.saarland:1234/_hp/tests/framing.sub.html

Old stuff below, TODO: update?
---
## Setup
- Install poetry
- `poetry install`
- Add the following to your `~/.gitconfig` file:
- Install jq
```git
[filter "nbstrip_full"]
    clean = "jq --indent 1 \
            '(.cells[] | select(has(\"outputs\")) | .outputs) = []  \
            | (.cells[] | select(has(\"execution_count\")) | .execution_count) = null  \
            | .metadata = {\"language_info\": {\"name\": \"python\", \"pygments_lexer\": \"ipython3\"}} \
            | .cells[].metadata = {} \
            '"
    smudge = cat
    required = true    
```

# Steps to Run the Framework

- Clone the repo using `git clone git@projects.cispa.saarland:swag/http-header-security.git`.
- Git pull all submodules: `git submodule update --force --recursive --init --remote`

- Create the Project config file `code/config.json`.
The structure is as follows: 
```
{
    "SAME_ORIGIN": "headers.websec.saarland",
    "SUB_SAME_ORIGIN": "headers.websec.saarland",
    "CROSS_ORIGIN": "headers.webappsec.eu",
    "SUB_CROSS_ORIGIN": "sub.headers.webappsec.eu",
    "DB_URL": "DB_CONNECTION_STRING",
    "SECRET": "swagisthebest",
    "HEADERS": ["xfo","hsts","csp","pp","rp","coop","coep","corp","cors_acac","cors_aceh","oac","tao"],
    "BROWSERS": {
        "BROWSERNAME_desktop":"PATH_TO_BROWSER_EXECUTABLE",
        "BROWSERNAME_android":"PACKAGE_NAME",
        "BROWSERNAME_ios":"YET_TO_DECIDE",
    }
}

> For desktop browsers, assign the value as the path to the executable/driver file. For android, assign the value of the package name.
> For `DB_URL`, assign it to the DB connection string of your choice Sqlite,Postegres etc. Just host any DB server and extract the connection string.

```
----
## LOCAL SERVER SETUP
- Add the following lines to `/etc/hosts` file `if testing locally` and replace the mentioned origin values with the desired ones:

```
127.0.0.1       headers.websec.saarland
127.0.0.1       sub.headers.websec.saarland
127.0.0.1       sub.sub.headers.websec.saarland
127.0.0.1       headers.webappsec.eu
127.0.0.1       sub.headers.webappsec.eu
127.0.0.1       sub.sub.headers.webappsec.eu
```
- Change the config file accordingly after setting these values.
- Run the script `code/cert-install.sh` to generate the certs.
- Install `mkcert` from https://github.com/FiloSottile/mkcert.
----

- Run `poetry shell` to activate the virtual env.
- Navigate using `cd code/testing_server`. Run `python server.py` to start the server.
- During first run, execute `python code/run_script.py` to initialise and populate the `Testcases` Table.
(**NOTE:** The server has to be running for this command to be executed successfully).

The following information includes the methods to run tests for different headers.

- Get the testcases `COUNT` for a `HEADER` by requesting `https://headers.websec.saarland/get_count?header={HEADER}` and choose a `LIMIT` to get a list of `OFFSET` values.
- Based on these values, run the testcases for each header as follows:
```
XFO -> Navigate to https://headers.websec.saarland/xfo/xfo.html?limit={LIMIT}&offset={OFFSET}&browser={BROWSERNAME} using Browser.

For CSP -> Navigate to https://headers.websec.saarland/csp/csp.html?limit={LIMIT}&offset={OFFSET}&browser={BROWSERNAME} using Browser

For HSTS -> Navigate to http://headers.websec.saarland/hsts/hsts.html?limit={LIMIT}&offset={OFFSET}&browser={BROWSERNAME} using Browser

For COEP -> Navigate to https://headers.websec.saarland/coep/coep.html?limit={LIMIT}&offset={OFFSET}&browser={BROWSERNAME} using Browser

For CORP -> Navigate to https://headers.websec.saarland/corp/corp.html?limit={LIMIT}&offset={OFFSET}&browser={BROWSERNAME} using Browser

For OAC -> Navigate to https://headers.websec.saarland/oac/oac.html?limit={LIMIT}&offset={OFFSET}&browser={BROWSERNAME} using Browser

For TAO -> Navigate to https://headers.websec.saarland/tao/tao.html?limit={LIMIT}&offset={OFFSET}&browser={BROWSERNAME} using Browser

For RP -> Get testcases from https://headers.websec.saarland/get_testcases?header=rp, then for each `uid`, navigate to https://headers.websec.saarland/runtest?test=rp&pair={uid}&browser={BROWSERNAME} using Browser

For PP -> Get testcases from https://headers.websec.saarland/get_testcases?header=pp, then for each `uid`, navigate to https://headers.websec.saarland/runtest?test=pp&pair={uid}&browser={BROWSERNAME} using Browser

For COOP -> Get testcases from https://headers.websec.saarland/get_testcases?header=coop, then for each `uid`, navigate to https://headers.websec.saarland/runtest?test=coop&pair={uid}&browser={BROWSERNAME} using Browser

```