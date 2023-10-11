function test_feature_availability(
    feature_description, test, src, expect_feature_available, feature_name,
    allow_attribute, is_promise_test = false) {
    let frame = document.createElement('iframe');
    frame.src = src;

    if (typeof feature_name !== 'undefined') {
        frame.allow = frame.allow.concat(";" + feature_name);
    }

    if (typeof allow_attribute !== 'undefined') {
        frame.setAttribute(allow_attribute, true);
    }

    function expectFeatureAvailable(evt) {
        if (evt.source === frame.contentWindow &&
            evt.data.type === 'availability-result') {
            expect_feature_available(evt.data, feature_description);
            document.body.removeChild(frame);
            test.done();
        }
    }

    if (!is_promise_test) {
        window.addEventListener('message', test.step_func(expectFeatureAvailable));
        document.body.appendChild(frame);
        return;
    }

    const promise = new Promise((resolve) => {
        window.addEventListener('message', resolve);
    }).then(expectFeatureAvailable);
    document.body.appendChild(frame);
    return promise;
}

// Default helper functions to test a feature's availability:
function expect_feature_available_default(data, feature_description) {
    assert_true(data.enabled, feature_description);
}

function expect_feature_unavailable_default(data, feature_description) {
    assert_false(data.enabled, feature_description);
}
