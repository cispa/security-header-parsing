# HTTP header parsing project

- For each header (and feature) we need a test (page) to know whether the feature is active or not
- For some headers/directive the used origins are important
- The test results should be saved in a database
- The test should be self-contained such that the test runner only needs to open a single URL and wait for some time
- Test runner: 
  - should support many browsers
  - including mobile browsers

## Analysis ideas
- For each browser and feature: group together all responses that resulted in the same test outcomes (or almost the same to account for noise/timeouts)
  - analyse the groups of responses to see any patterns
  - do it for every browser and then focus on the responses that are in different groups in different browsers

## Header generation thoughts

All tests:
1. headern: hvalue
2. headern: hvalue, hvalue
3. headern: hvalue + headern: hvalue
4. (Only for Framing-Control:XFO and CSP frame-ancestors): headern1: hvalue + headern2: hvalue AND headern2: hvalue + headern1: hvalue

Header name variations:
- headern: correct lowercase name or other
- other: varied casing, legacy names (e.g. X-WEBKIT-CSP), invalid
- invalid: leading spaces?, add other characters?

Header value options:
- hvalue: directive
- hvalue: duplicate directives (only for headers with mutiple directives not separated by comma)
- hvalue: several directives

Directives:
- directive: directivename=value (depending on the header it might not be equal but some other separator)
- directive: value (for headers that do not have "directives" such as XFO)

Directive name: valid OR invalid OR legacy

Value: valid OR invalid OR legacy OR empty
- Valid: block OR partial OR allow

Mutations (where to apply them? header value, directives, header names?, ...):
- add quotes (surrounding everything or a value, ...)
- switch quotes
- change whitespace (remove, add: tab, spaces, ...);
- change delimiters (=,;)
- add characters

More thoughts:
- Types of correct, incorrect headers and mutations
- 1: for all headers (multiple headers/header names): this is done after header generation with a grammar/independently of the grammar
- 2: for all headers (within a header): this is (mostly?) done with mutations? after header generation? (e.g., replace spaces with more spaces, tabs, ...?; replace commas or quotes? or add random spaces?)
- 3: specific for each header (within a header): this is done within the custom generation grammar for each header?!
- 4: combination of headers (e.g., both CSP frame-ancestors + XFO?; other interesting combinations?; feature-policy and permission-policy at the same time)
- Other things one has to be careful about? E.g., header necessary to activate a feature, ...
- ...
