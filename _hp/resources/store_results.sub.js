const queryString = window.location.search;
const urlParams = new URLSearchParams(decodeURIComponent(queryString));
async function save_result(tests, status) {
    //console.log(tests);
    var test_results = tests.map(function(x) {
        return {name: x.name, outcome: x.outcome, status: x.status, message: x.message, stack: x.stack}
    });
    var data = {
                // Results for the individual tests + metainfo (which browser)
                tests: test_results,
                browser_id: urlParams.get('browser_id') || 1, // One is the unknown browser!
                // Currently unused other metadata (status etc. of the complete test file run)
                test: window.location.href,
                status: status.status,
                message: status.message,
                stack: status.stack,
            };
    await fetch('https://{{host}}:{{ports[https][0]}}/_hp/server/store_results.py', {
        method: 'POST',
        body: JSON.stringify(data),
        mode: 'no-cors',
        headers: {
            'Content-Type': 'application/json',
        }
    });
}
add_completion_callback(save_result);