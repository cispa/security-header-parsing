# HTTP header parsing project

- For each header (and feature) we need a test (page) to know whether the feature is active or not
- For some headers/directive the used origins are important
- The test results should be saved in a database
- The test should be self-contained such that the test runner only needs to open a single URL and wait for some time
- Potential issue timeout/crash vs test result in no outcome (e.g., as CSP blocked code execution)? -> repeat tests?, use screenshots?
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

## Considered feature groups + tests

- **TODO:** write down what is necessary to test each feature group
  - how many/which origins (what relation do they need)
  - how to measure the success/failure of the feature
  - how to communicate the outcome back
  - how many features are there for each header to test, ...

### Feature groups

- Framing Control:
    - Tests:
        - simple framing (same-origin, cross-origin (parent, sub), cross-site)
        - nested/double framing (A->B->A->A)
        - sandbox framing (A->B(sandbox)->A)
        - all with iframe, object, and embed
        - others?:
            - XFO on redirect? (how to implement?: ~~seperate test?~~ same tests but in addition also use responses with redirect codes+location)
            - service-worker stuff? FA
            - ...
    - Headers:
        - CSP FA:
            - also X-CSP and other deprecated names?
            - wildcard in URL
            - multiple header spec: composition
        - XFO: multiple header spec: complex algorithm -> usually deny
        - Both: XFO is CSP framing control fallback?
- Connection Upgrade (Strict-Transport-Security):
    - Tests:
        -  HSTS upgrade site-randomURL (visit site and set HSTS, visit again and check whether connection is upgraded)
        -  HSTS upgrade site-subdomainURL (same as above but visit a subdomain URL)
        -  Double subdomain? (visit domain, set HSTS, visit subdomain, set HSTS, visit subsubdomain?) 
           -  (see example on whiteboard)
           -  max-age=1 on sub.domain.com, max-age=123,ISD on domain.com -> what happens when visiting foo.sub.domain.com?
           -  max-age=123 on sub.domain.com, max-age=123,ISD on domain.com -> what happens when visiting foo.sub.domain.com?
        -  HSTS via HTTP does nothing (tested implicetly during the normal tests!)
        -  Clearing?
        -  Caching?
    - STS-Header: multiple header spec: (first; some browsers might order headers in a strange way with different casing/HTTP versions)
    - Test site has to be visited on HTTP due to Mixed Content Blocking
- Restricted API Access (Permission Policy):
    - Tests:
      - Access API same-origin top-frame (fullscreen?; document.fullscreenEnabled; Its default allowlist is 'self'.)
      - Access API same-origin frame
      - Acces API cross-origin frame
      - Access API same-site frame?
      - Multiple nestings?
      - Inheritance for IFrames? ...
      - Log document.permissionsPolicy/featurePolicy object?
      - ...
    - Headers:
        - PermissionPolicy:
            - Multiple header spec: (last per feature; is a structured header -> values that break syntax MUST be rejected; still WIP not an official spec) 
            - where to deploy the header? top-level document? nested document? both? ...
            - OT: camera/video; pp is only responsible for allowing the call to getUserMedia, mediacapture spec is then responsible to check whether it is allowed or not; which Origin is shown to the user if the call comes from a cross-origin iframe?
        - FeaturePolicy: FeaturePolicy/iframe allow (no idea; should we test this?)
- Referrer value:
    - Tests:
        - Referrer send to same-origin
        - Referrer send to same-site
        - Referrer send to cross-site
        - Referrer send to cross-site downgrade? (HTTPS to HTTP)
        - ...?
    - Referer-Policy:
        - multiple header spec: (no idea; fallback features)
        - (whiteboard) window.open(), check if this works on all browsers, x-proto, x-site, x-origin (not sure what the idea was here)
- TimingAPI:
    - Tests:
        - Access Timing API same-origin
        - Access Timing API same-site (subdomain)
        - Access Timing API cross-site
        - Access Timing API cross-site (subdomain)?
    - Timing-Allow-Origin:
        -  *, origin list, ...
-  Image Load (CORP):
    -  Tests:
        -  Events-fired image (same-origin)
        -  Events-fired image (same-site) (subdomain)
        -  Events-fired image (cross-site)
        -  Events-fired image (cross-site) (subdomain)?
    - Cross-Origin-Resource-Policy: ...  
- Window-References (COOP):
    - Tests:
        - Access window.opener (same-origin)
        - Access window.opener (cross-site)
        - (Currently the tests run in the opened window? however, we can run the tests in the top-level window that opened the new windows to check whether they can be accessed?)
    - Cross-Origin-Opener-Policy: ...
- Cross-Origin-Isolation (COEP):
    - Tests:
        - TODO: what do we actually want to test for COEP and what are we currently testing?
        - Check whether window is cross-origin-isolated?
        - Check whether requests are send without credentials, blocked if they do not have correct CORP or CORS settings?
        - ...?
    - Cross-Origin-Embedder-Policy: ...
- Origin-keying (OAC)
    - Tests:
        - Access window.originAgentCluster (top-level window)
        - Document.domain, webassembly.module, sharedarraybuffer?
        - Caching? (Caution: Don't forget to send the header on error pages, like your 404 page!)
    - Origin-Agent-Cluster: ..
- CORS:
    - Several test pages as we have different groups of headers
    - Tests:
        - Access response allowed (same-origin)
        - Access response allowed (same-site)
        - Access response allowed (cross-site)
        - Access response for request with credentials allowed (same-origin)
        - Access response for request with credentials allowed (same-site)
        - Access response for request with credentials allowed (cross-site)
        - Request with special headers allowed (cross-site)
        - Request with special method allowed (cross-site)
        - Access special response header allowed (same-origin)
        - Access special response header allowed (same-site)
        - Access special response header allowed (cross-site)
        - Caching? ACMA?
    - Headers:
        - ACAO only
        - ACAC (+ACAO)
        - ACAH (+ACAO)
        - ACAM (+ACAO)
        - ACEH (+ACAO)

- Other stuff:
    - Other CSP stuff:
        - script-control
        - anything else? TLS enforcement (UIR), fetch directive, fallback rules, reporting?, trusted-types?, ...
        - What about meta tags? E.g., CSP or XFO?
        - csp tag for iframes?
    - XCTO
    - Expect-CT (not interesting?)
    - Set-Cookie
    - ...