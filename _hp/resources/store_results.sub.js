// More helper functions here!
var org_scheme = location.port == 9000 ? "http2" : location.protocol == "http:" ? "http" : "https";
var org_host = location.hostname;

// We always visit the testpages at http://sub.headers.websec.saarland or https://sub.headers.websec.saarland
// We then create tests for http, https, ~~and http2~~ for the following cases:
// same-org, 2x same-site (parent-domain + sub-domain), cross-site
function get_test_origins(resp_type) {
  const same_host = 'sub.{{host}}';
  const parent = '{{host}}';
  const sub = 'sub.sub.{{host}}';
  const alt_host = '{{hosts[alt][]}}';

  // Only run for one origin relation (cross-site) in the parsing mode!
  if (resp_type == "parsing") {
    return [`https://${alt_host}`];
  }

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
function run_tests(test_declarations, path, label, origins) {
  for (let test of test_declarations) {
    // Run all tests for origin relations and similar!
    let urlParams = new URLSearchParams(decodeURIComponent(window.location.search));
    const resp_type = urlParams.get("resp_type") || "debug";
    if (!origins) {
      origins = get_test_origins(resp_type);
    }
    // Test self-driving tests:
    const start_id = parseInt(urlParams.get("start_id"), 10) || 0;
    const chunk_size = parseInt(urlParams.get("chunk_size"), 10) || 1;
    const end_id = parseInt(urlParams.get("end_id"), 10) || 1;

    // Currently for testing get resp_ids via the label endpoint!
    // Later: From start_id to end_id (provided by  the testrunner via query parameters &start_id=<id>&end_id=<id>&chunk_size=<chunk_size>)
    // TODO: iterate over the fixed ids instead of fetching them dynamically
    //for (var response_id=start_id; response_id < Math.min(end_id, start_id + chunk_size); i++){

    fetch(`${location.origin}/_hp/server/get_resp_ids.py?label=${label}&resp_type=${resp_type}`).then(resp => resp.json()).then(ids => {
      for (var response_id of ids) {
        for (var origin of origins) {
          test(`${origin}${path}`, origin, response_id);
        }
      }
    });
  }
}

function nested_test(frame_element, sandbox, url, response_id, element, test_info, test_name) {
  async_test(t => {
    t.set_test_info(url, test_info);
    const i = document.createElement(frame_element);
    count = count + 1;
    i.id = count;
    let origin = location.origin; // Works for A->B and A->B(->A)->A embedding; for A->B->B we would need to use the origin of B
    let nesting;
    // A -> B (sandbox) -> A embedding
    if (sandbox) {
      i.sandbox = "allow-scripts";
      nesting = 1;
    }
    // A -> B -> A -> A embedding
    if (test_info === "nested") {
      nesting = 2;
    }
    let final_url = url + response_id + `&count=${i.id}&nest=${nesting}&origin=${origin}&element=${element}&resp=0`
    i.data = final_url; // Object
    i.src = final_url; // Embed + IFrame
    // Wait for 90% of test_timeout; then report that no message was received!
    let timer = t.step_timeout(() => {
      t.report_outcome("message timeout");
      t.done();
    }, 0.9 * test_timeout);
    // Report that a message was received
    waitForMessageFrom(i, t).then(t.step_func_done(e => {
      clearTimeout(timer);
      t.report_outcome(e.data.message);
    }));
    // Cleanup function (remove the frame after the test)
    t.add_cleanup(() => i.remove());
    // Start the test
    document.body.append(i);
  }, test_name);
}

// Store result helpers!
async function save_result(tests, status) {
  let urlParams = new URLSearchParams(decodeURIComponent(window.location.search));
  console.log(tests);
  var test_results = tests.map(function (x) {
    return {
      name: x.name, outcome: x.outcome, status: x.status, message: x.message, stack: x.stack,
      resp_scheme: x.resp_scheme, resp_host: x.resp_host, relation: x.relation
    }
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

  // Append a "finished" div which we can await for in non self-driving tests
  d = document.createElement("div");
  d.id = "finished";
  document.body.appendChild(d);

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