// More helper functions here!
var org_scheme = location.port == 9000? "http2": location.protocol == "http:" ? "http": "https";
var org_host = location.hostname;

// We always visit the testpages at http://sub.headers.websec.saarland or https://sub.headers.websec.saarland
// We then create tests for http, https, and http2 for the following cases:
// same-org, 2x same-site (parent-domain + sub-domain), cross-site
function get_test_origins() {
    const same_host = 'sub.{{host}}';
    const parent = '{{host}}';
    const sub = 'sub.sub.{{host}}';
    const alt_host = '{{hosts[alt][]}}';

    origins = [];
    for (let host of [same_host, parent, sub, alt_host]) {
        origins.push(`http://${host}`);
        origins.push(`https://${host}`);
        // H2 has a process leak? after a while 7k+ processes are open and everything crashes
        // Occurs for both with/without settings to allow for invalid responses
        //origins.push(`https://${host}:{{ports[h2][0]}}`);
    }
    return origins;
};

function waitForMessageFrom(frame, test) {
    return new Promise(resolve => {
      window.addEventListener("message", test.step_func(e => {
        if (e.data.id == frame.id) {
          resolve(e);
        }
      }));
    });
  }

// Run all tests
function run_tests(test_declarations, path, label) {
  for (let test of test_declarations) {
    // Run all tests for origin relations and similar!
    let origins = get_test_origins();
    // Test self-driving tests:
    let urlParams = new URLSearchParams(decodeURIComponent(window.location.search));
    const start_id = parseInt(urlParams.get("start_id"), 10) || 0;
    const chunk_size = parseInt(urlParams.get("chunk_size"), 10) || 1;
    const end_id = parseInt(urlParams.get("end_id"), 10) || 1;

    // Currently for testing get resp_ids via the label endpoint!
    // Later: From start_id to end_id (provided by  the testrunner via query parameters &start_id=<id>&end_id=<id>&chunk_size=<chunk_size>)
    // TODO: iterate over the fixed ids instead of fetching them dynamically
    //for (var response_id=start_id; response_id < Math.min(end_id, start_id + chunk_size); i++){
    fetch(`${location.origin}/_hp/server/get_resp_ids.py?label=${label}`).then(resp => resp.json()).then(ids => {
      for (var response_id of ids){
        // origins = ["https://sub.headers.websec.saarland"];
        for (var origin of origins) {
          test(`${origin}${path}`, origin, response_id);
        }
      }
    });
  }
}

// Store result helpers!
let urlParams = new URLSearchParams(decodeURIComponent(window.location.search));
async function save_result(tests, status) {
    console.log(tests);
    var test_results = tests.map(function(x) {
        return {name: x.name, outcome: x.outcome, status: x.status, message: x.message, stack: x.stack,
                resp_scheme: x.resp_scheme, resp_host: x.resp_host, relation: x.relation}
    });
    var data = {
                // Results for the individual tests + metainfo (which browser)
                tests: test_results,
                browser_id: urlParams.get('browser_id') || 1, // One is the unknown browser!
                // Other metadata (status etc. of the complete test file run)
                test: window.location.href,
                status: status.status,
                message: status.message,
                stack: status.stack,
                org_scheme: org_scheme,
                org_host: org_host
            };
    await fetch('https://{{host}}:{{ports[https][0]}}/_hp/server/store_results.py', {
        method: 'POST',
        body: JSON.stringify(data),
        mode: 'no-cors',
        headers: {
            'Content-Type': 'application/json',
        }
    });

    // Self-driving test!
    const start_id = parseInt(urlParams.get("start_id"), 10) || 0;
    const chunk_size = parseInt(urlParams.get("chunk_size"), 10) || 1;
    const end_id = parseInt(urlParams.get("end_id"), 10) || 1;
    console.log(start_id, chunk_size, end_id);
    if (start_id + chunk_size < end_id) {
        urlParams.set('start_id', start_id + chunk_size);
        window.location.href = window.location.pathname + '?' + urlParams.toString();
    }
};
add_completion_callback(save_result);