/*
Functions and helpers to run the "Head(er)s Up!" browser tests and store the final results in the database
*/
// Scheme and host of the top-level file (original scheme/host)
var org_scheme = location.port == 9000 ? "http2" : location.protocol == "http:" ? "http" : "https";
var org_host = location.hostname;

// String to search for on the page; Only necessary for manual debugging of the COEP bug
let search = urlParams.get('search') || undefined;

// We always visit the testpages at http://sub.headers.websec.saarland or https://sub.headers.websec.saarland
// We then create tests for the following origins:
// (https and https) X same-org, 2x same-site (parent-domain + sub-domain), cross-site
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
    if (!(search && org_scheme == 'https')) {
      origins.push(`http://${host}`);
    }
    origins.push(`https://${host}`);

    // The WPT HTTP/2 server has a process leak: after a while 7k+ processes are open and everything crashes
    // Occurs for both with/without settings to allow for invalid responses
    // For now do not test HTTP/2
    //origins.push(`https://${host}:{{ports[h2][0]}}`);
  }
  return origins;
};

// Helper to wait for a postMessage from a specific frame
function waitForMessageFrom(frame, test) {
  return new Promise(resolve => {
    window.addEventListener("message", test.step_func(e => {
      if (e.data.id == frame.id) {
        resolve(e);
      }
    }));
  });
}

// Run all declared tests for the specified origins
function run_tests(test_declarations, path, label, origins) {
  // Which tests to run: debug (default), basic, parsing
  const resp_type = urlParams.get("resp_type") || "debug";
  // Which tests to run (from first_id to last_id)
  const first_id = parseInt(urlParams.get("first_id"), 10) || null;
  const last_id = parseInt(urlParams.get("last_id"), 10) || null;
  // If tests open popups, which to run (from first_popup to last_popup)
  const first_popup = parseInt(urlParams.get("first_popup"), 10) || 0;
  const last_popup = parseInt(urlParams.get("last_popup"), 10) || Infinity;
  // Do not run any popup tests
  const run_no_popup = urlParams.get("run_no_popup") || 'yes';

  // Settings for the manual confirmation mode
  // Only run this exact test instance
  const t_resp_id = parseInt(urlParams.get("t_resp_id"), 10) || null;
  const t_resp_origin = urlParams.get("t_resp_origin") || null;
  const element_relation = urlParams.get("t_element_relation") || null;

  // If no origin relations are specified, run for the default origins of the `resp_type`
  if (!origins) {
    origins = get_test_origins(resp_type);
  }

  // For automated testing run on the specified ids (&first_id=<first_id>&last_id=<last_id>;)
  let popup_count = 0;
  if (first_id && last_id) {
    for (var response_id = first_id; response_id < last_id + 1; response_id++) {
      for (var origin of origins) {
        for (let test of test_declarations) {
          // Only run exactly one test in the manual confirmation mode
          // (the manual confirmation mode has to use clean_urls without popup_settings!)
          if (t_resp_id) {
            if (t_resp_id != response_id) {
              continue
            }
            if (t_resp_origin != origin) {
              continue
            }
            if (element_relation != test.element_relation) {
              continue
            }
          }

          if (test.popup) {
            popup_count = popup_count + 1;
            if (popup_count >= first_popup && popup_count <= last_popup) {
              test(`${origin}${path}`, origin, response_id);
            }
          } else {
            if (run_no_popup == 'yes') {
              test(`${origin}${path}`, origin, response_id);
            }
          }
        }
      }
    }
  }
  // For (manual) testing get resp_ids via the label endpoint!
  else {
    fetch(`${location.origin}/_hp/server/get_resp_ids.py?label=${label}&resp_type=${resp_type}`).then(resp => resp.json()).then(ids => {
      for (var response_id of ids) {
        for (var origin of origins) {
          for (let test of test_declarations) {
            test(`${origin}${path}`, origin, response_id);
          }
        }
      }
    });
  }
  console.log(`All popups: ${popup_count}`);
}

// Helper to create nested tests
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

// Store all the results on our database
async function save_result(tests, status) {
  console.log(tests);
  // Convert the WPT test results to our format
  var test_results = tests.map(function (x) {
    return {
      name: x.name, outcome: x.outcome, status: x.status, message: x.message, stack: x.stack,
      resp_scheme: x.resp_scheme, resp_host: x.resp_host, relation: x.relation
    }
  });
  var data = {
    // Results for the individual tests + metainfo (e.g., which browser)
    tests: test_results,
    browser_id: urlParams.get('browser_id') || 1, // "1" is the unknown browser!
    // Other metadata (status etc. of the complete test file run)
    test: window.location.href,
    status: status.status,
    message: status.message,
    stack: status.stack,
    org_scheme: org_scheme,
    org_host: org_host,
    full_url: document.location.href
  };
  // Store the results at the database
  await fetch('https://{{host}}:{{ports[https][0]}}/_hp/server/store_results.py', {
    method: 'POST',
    body: JSON.stringify(data),
    mode: 'no-cors',
    headers: {
      'Content-Type': 'application/json',
    }
  });

  // Append a "finished" div which we can await for in Selenium/Playwright based tests
  d = document.createElement("div");
  d.id = "finished";
  document.body.appendChild(d);

  // Stop the run_id page runner by notifying the runner via postgres
  let run_id = urlParams.get('run_id') || undefined;
  if (run_id) {
    await fetch(`${location.origin}/_hp/server/notify_runner_clients.py?run_id=${run_id}`);
  }

  // For manual debugging of the COEP test only
  if (search) {
    // Get the content of the webpage
    const webpageContent = document.body.innerText;

    // Define the string to search for
    const searchString = '"swag-same-origin.jpg":"error"';
    const searchString2 = '"swag-same-site.jpg":"error"';


    // Count occurrences of the search string
    const c = (webpageContent.match(new RegExp(searchString, 'g')) || []).length;
    const c2 = (webpageContent.match(new RegExp(searchString2, 'g')) || []).length;


    // Output the count
    alert(`The string "${searchString}" occurs ${c} times on the page. The string "${searchString2}" occurs ${c2} times on the page.`);
  }

  // Notify opener page that the test is finished!
  try {
    window.opener.postMessage("finished", "*");
  } catch (e) {
    // Opener page does not exist; test opened directly
    console.log(e);
  }


};
// Save the results if the tests are finished
add_completion_callback(save_result);
