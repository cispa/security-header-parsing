from models import Response, Session
from sqlalchemy.exc import IntegrityError

# Common area
# Redirect to empty response, has ACAO *, other than that no special headers!
redirect_empty = ("location", "https://sub.headers.websec.saarland/_hp/common/empty.html")
site = "sub.headers.websec.saarland"
origin_s = "https://sub.headers.websec.saarland"
origin = "http://sub.headers.websec.saarland"
origin_sp = f"{origin_s}:443"
home = f"{origin_s}/"
home_p = f"{origin_sp}/"
parent = "https://headers.websec.saarland"
child = "https://sub.sub.headers.websec.saarland"
parent_childs = "*.headers.websec.saarland"
self_childs = "*.sub.headers.websec.saarland"


# TODO: create responses for each feature group (file in /tests)
# Some feature groups have more than one group of responses (label in the DB), e.g., framing has both XFO, CSP, and XFO vs CSP
# We have to define somewhere which label responses we use for which test_file tests?

def create_responses(header_list, label, status_code=200, resp_type="debug"):
    with Session() as session:
        for header in header_list:
            try:
                r = Response(raw_header=header, status_code=status_code, label=label, resp_type=resp_type)
                session.add(r)
                session.commit()
            except IntegrityError as e:
                session.rollback()
                print("IntegrityError probably response already exists")


#region Framing

## XFO only
header_deny = [("x-frame-options", "DENY")]
header_allow = [("x-frame-options", "INVALID")]
label = "XFO"
create_responses([header_deny, header_allow], label)

# WPT tests: https://wpt.fyi/results/x-frame-options?label=master&label=experimental&aligned&q=x-frame
# Basic tests: same-origin, cross-origin
# Special tests: XFO on redirect, nested same/cross-origin
# WPT headers:
# DENY, denY, <SPACE>DENY<SPACE>, sameOrigin, SAMEORIGIN, ...
# empty values and commas
# invalid: allow-from, allow-from=, ALLOWALL, "<value(s)>", empty string
wpt_values = {'', 'allowAll', 'ALLOWALL', 'DENY', 'sameOriGin', 'ALLOW-FROM=https://example.com/', '"DENY"', '"SAMEORIGIN"', 'INVALID', 'SAMEORIGIN', '  SAMEORIGIN,    DENY', 'sameOrigin', '  DENY ', '"SAMEORIGIN,DENY"', '  SAMEORIGIN ', 'ALLOW-FROM https://example.com/', 'denY', ',SAMEORIGIN,,DENY,'}
# multiple with , and multiple headers (marked with ; in their tests)
# XFO + CSP-FA

# Siewert tests:
# Basic tests: same-origin, cross-origin (subdomain) ; no cross-site! no nested/double framing, ...!
# Special test: XFO in meta tag (does not have any effect)
# Siewert headers:
siewert_values = {'allow-from http://randomorigin.com, sameorigin', 'sameorigin; sameorigin', 'RANDOMDIRECTIVE', 'allow-from http://randomorigin.com/, deny', 'sameorigin; deny', 'allow-from http://randomorigin.com/, allow-from http://randomorigin.com/', 'allow-from http://much.ninja', 'allow-from TESTURI; deny', 'allow-from http://randomorigin.com/, allow-from TESTURI', 'allow-from TESTURI, deny', 'sameorigin, allow-from http://randomorigin.com', 'allow-from TESTURI, allow-from http://randomorigin.com/', 'deny', 'sameorigin', 'deny; deny', 'allow-from http://randomorigin.com/; allow-from http://randomorigin.com/', 'allow-from TESTURI; allow-from http://randomorigin.com/', 'deny; allow-from TESTURI', 'deny; sameorigin', 'allowall', 'sameorigin, deny', 'allow-from http://random.ninja', 'allow-from http://randomorigin.com/', 'deny, deny', 'allow-from TESTURI', 'sameorigin, sameorigin', 'allow-from https://much.ninja', 'deny, allow-from TESTURI', 'deny, sameorigin'}

# crawler.ninja (https://crawler.ninja/files/xfo-values.txt) 
# Subset of (popular) invalid choices
crawler_values = {'GOFORIT', '*', 'ALLOW-FROM *', 'same-origin', 'â€œDENYâ€', 'ALLOW-FROM SAMEDOMAIN', 'NONE', 'SAMEORIGIN always', 'ALLOW-FROM \'self\'', 'CROSS-ORIGIN', 'FALSE', 'SAMEORIGIN <url>', ': SAMEORIGIN', '<url>', '"SAMEORIGIN" always;', 'NEVER', 'SAMESITE', 'strict-origin-when-cross-origin', '(DENY || SAMEORIGIN)', 'self', 'X-Frame-Options: DENY', 'add_header X-Frame-Options "SAMEORIGIN" always;', 'nosniff', 'ALLOW-ALL', 'crossorigin', 'null', 'ANY', 'all', 'SMAEORIGIN', 'sameoriginSAMEORIGIN', "'DENY'", 'SAMEORIGINS', 'SAMEORIGION'}


# Other values: (own ideas)
# Firefox replaces all whitespaces, chromium only strips them
# Also Tab %09, vertical tab %0B, (all control characters!)
# %C2%A0 (non-breaking space) ...
# Separation with space: sameorigin sameorigin
# Full-Width comma? ，%EF%BC%8C
# ...
other_values = {"same origin", "den y"}


# Alternative header names (legacy/invalid/typos)
# For main name use different casing: x-frame-options, X-FRAME-OPTIONS, X-Frame-Options, X-frame-options
# Idea for alternative header names: Test with one basic testcase (DENY) whether the wrong header name works? If not, skip all tests, if yes run all tests to see if they behave the same or not
alt_header_names = ["Frame-Options", "X-Frame-Option", "X-FRAMES-OPTIONS", "Content-Security-Policy", "X_FRAME_OPTIONS", "XFRAMEOPTIONS"]

## CSP-FA
header_deny = [("Content-Security-Policy", "frame-ancestors 'none'")]
header_allow = [("Content-Security-Policy", "frame-ancestors *")]
label = "CSP-FA"
create_responses([header_deny, header_allow], label)

# WPT tests?: https://wpt.fyi/results/content-security-policy/frame-ancestors?label=master&label=experimental&aligned&q=frame
# Simple framing: same-origin, cross-origin, nested (cross-cross, cross-same, same-cross, same-same)
# Special stuff: service workers, overwrite XFO, sandboxed iframe parent, report fired for violations

# WPT values?
wpt_values = {"frame-ancestors 'none'", "frame-ancestors 'self'", "frame-ancestors *", "frame-ancestors http://www1.wpt.live:8000", "frame-ancestors https://wpt.live:443"}

# Siewert tests?
# Simple framing: same-origin, cross-origin (subdomain); XFO+CSP simple framing
# Special test: meta tag
# Siewert values?
siewert_csp_fa = {'frame-ancestors http://much.ninja;', 'frame-ancestors much.ninja;', 'frame-ancestors *.ninja;', 'frame-ancestors http:;', 'frame-ancestors http://randomorigin.com;', 'frame-ancestors http://*.ninja http://randomorigin.com;', 'frame-ancestors https:;'}

# Crawler.ninja values? https://crawler.ninja/files/csp-values.txt
# Many more
ninja_csp_fa = {"default-src 'none'", "self", "*", "frame-ancestors self", "frame-ancestors", "frame-ancestors none", "frame-src none",}

# Other values?
# Spaces, typo in frame-ancestors, ...
other = {}

# Alternative names
# X-Content-Security-Policy, X-Webkit-CSP, ...

## XFO vs CSP
header_deny = [("Content-Security-Policy", "frame-ancestors 'none'"), ('X-Frame-Options', 'DENY')]
header_allow = [("Content-Security-Policy", "frame-ancestors *"), ('X-Frame-Options', 'INVALID')]
label = "CSPvsXFO"
create_responses([header_deny, header_allow], label)

#endregion

#region CORP
# Subresource loading/CORP
header_deny = [("Cross-Origin-Resource-Policy", "same-origin")]
header_allow = [("Cross-Origin-Resource-Policy", "cross-origin")]
label = "CORP"
create_responses([header_deny, header_allow], label)

#endregion

#region COEP
# No non-corp ressources allowed while COEP is there, + crossOriginIsolated Flag
header_deny = [("Cross-Origin-Embedder-Policy", "require-corp")]
header_allow = [("Cross-Origin-Embedder-Policy", "unsafe-none"),
                ]
label = "COEP"
create_responses([header_deny, header_allow], label)

#endregion

#region Window References/COOP
header_deny = [("Cross-Origin-Opener-Policy", "same-origin")]
header_allow = [("Cross-Origin-Opener-Policy", "unsafe-none")]
label = "COOP"
create_responses([header_deny, header_allow], label)

#endregion

#region CORS
# For testing we only need one AC-XX headers pair
header_deny = [("Access-Control-Allow-Origin", "null")]
header_allow = [("Access-Control-Allow-Origin", "https://sub.headers.websec.saarland"),
                 ("Access-Control-Allow-Credentials", "true"),
                 ("Access-Control-Allow-Methods", "TEST"),
                 ("Access-Control-Allow-Headers", "Test"),
                 ("Access-Control-Expose-Headers", "Test"),
                 ("Test", "Test"),
                 # ("Access-Control-Max-Age", "10") # Caching
                ]
label = "CORS"
create_responses([header_deny, header_allow], label)
#endregion

#region CSP script-execution
header_deny = [("Content-Security-Policy", "script-src 'none'")]
header_allow = [("Content-Security-Policy", "script-src *")]
label = "CSP-SCRIPT"
create_responses([header_deny, header_allow], label)
#endregion

#region CSP subresource loading (image)
header_deny = [("Content-Security-Policy", "img-src 'none'")]
header_allow = [("Content-Security-Policy", "img-src *")]
label = "CSP-IMG"
create_responses([header_deny, header_allow], label)
#endregion

#region HSTS enforcement
# deny and allow are not fitting terms here, but does not matter
header_deny = [("Strict-Transport-Security", "max-age=20")]
header_allow = [("Strict-Transport-Security", "max-age=20; includeSubDomains")]
label = "HSTS"
create_responses([header_deny, header_allow], label)
#endregion

#region originAgentCluster/oac header
# related to document.domain and site/origin isolation
label = "OAC"
header_name = "origin-agent-cluster" # https://html.spec.whatwg.org/multipage/browsers.html#origin-agent-cluster
v1 = "?1"
v2 = "?0"
v3 = ""
v4 = "1"
v5 = "0"
v6 = "true"
v7 = "false"
header_deny = [("origin-agent-cluster", v1)]  # Set OAC, secure value
header_allow = [("origin-agent-cluster", v2)] # Disable OAC, insecure value
create_responses([header_deny, header_allow], label)
header_list = [[(header_name, "*")], [], 
               [(header_name, "null")], [(header_name, v1)],
               [(header_name, v2)], [(header_name, v3)],
               [(header_name, v4)], [(header_name, v5)],
               [(header_name, v6)], [(header_name, v7)],
               [(header_name, f"{v1}, {v2}, {v3}, {v4}, {v5}, {v6}, {v7}")],
               [(header_name, f"abc, {v1}")]
            ]
create_responses(header_list, label, resp_type="basic")
# Some basic headers with redirect
header_list = [[(header_name, v1), redirect_empty], [(header_name, v2), redirect_empty]]
create_responses(header_list, label, status_code=302, resp_type="basic")
#endregion

#region Permission access/PP
# https://github.com/w3c/webappsec-permissions-policy/blob/main/features.md
# https://fullscreen.spec.whatwg.org/#fullscreen-is-supported
# https://w3c.github.io/webappsec-permissions-policy/#policy-controlled-feature-default-allowlist
label = "PP"
header_name = "Permissions-Policy" # https://w3c.github.io/webappsec-permissions-policy/#permissions-policy-http-header-field
header_deny = [(header_name, "fullscreen=()")]
header_allow = [(header_name, "fullscreen=(*)")]
create_responses([header_deny, header_allow], label)
header_list = [[(header_name, "*")], [], 
               [(header_name, "null")], [(header_name, "fullscreen=")], [(header_name, "fullscreen=*")], [(header_name, "fullscreen=()")],
               [(header_name, "fullscreen=(self)")], [(header_name, f"fullscreen=({origin_s})")],
               [(header_name, f"fullscreen=({parent_childs})")], [(header_name, f"fullscreen=({self_childs})")],
               [(header_name, "fullscreen=(self none)")], [(header_name, "fullscreen=(self,none)")], [(header_name, "fullscreen=(src)")], [(header_name, f"fullscreen=({home})")],
               [(header_name, f"fullscreen=({home_p})")]
            ]
create_responses(header_list, label, resp_type="basic")
# Some basic headers with redirect
header_list = [[(header_name, "fullscreen=()"), redirect_empty], [(header_name, "fullscreen=(*)"), redirect_empty]]
create_responses(header_list, label, status_code=302, resp_type="basic")
# Alternative header name
header_name = "Feature-Policy" # https://w3c.github.io/webappsec-permissions-policy/#ascii-serialization
header_list = [[(header_name, "fullscreen *")], [(header_name, "fullscreen 'none'")],
               [(header_name, "fullscreen 'self'")], [(header_name, "fullscreen 'src'")],
               [(header_name, f"fullscreen {origin_s}")], [(header_name, f"fullscreen {self_childs}")],
               [(header_name, f"fullscreen {parent_childs}")]]
create_responses(header_list, label, resp_type="basic")
#endregion

#region Referer/Referrer-Policy
label = "RP"
header_name = "Referrer-Policy" # https://w3c.github.io/webappsec-referrer-policy/#referrer-policy-header
v1 = "no-referrer"
v2 = "no-referrer-when-downgrade"
v3 = "same-origin"
v4 = "origin"
v5 = "strict-origin"
v6 = "origin-when-cross-origin"
v7 = "strict-origin-when-cross-origin"
v8 = "unsafe-url"
v9 = ""
header_deny = [(header_name, v1)]
header_allow = [(header_name, v8)]
create_responses([header_deny, header_allow], label)
header_list = [[(header_name, "*")], [], 
               [(header_name, "null")], [(header_name, v1)],
               [(header_name, v2)], [(header_name, v3)],
               [(header_name, v4)], [(header_name, v5)],
               [(header_name, v6)], [(header_name, v7)], [(header_name, v8)], [(header_name, v9)],
               [(header_name, f"{v1}, {v2}, {v3}, {v4}, {v5}, {v6}, {v7}, {v8}")],
               [(header_name, f"abc, {v5}")]
            ]
create_responses(header_list, label, resp_type="basic")
# Some basic headers with redirect
header_list = [[(header_name, v1), redirect_empty], [(header_name, v8), redirect_empty]]
create_responses(header_list, label, status_code=302, resp_type="basic")
#endregion

#region PerformanceAPI timing/TAO
label = "TAO"
header_name = "Timing-Allow-Origin" # https://w3c.github.io/resource-timing/#sec-timing-allow-origin
header_deny = [(header_name, "null")]
header_allow = [(header_name, "*")]
# Debug tests
create_responses([header_deny, header_allow], label)
# Basic tests
header_list = [[(header_name, "*")], [], 
               [(header_name, "null")], [(header_name, origin_s)],
               [(header_name, origin)], [(header_name, parent)],
               [(header_name, home)], [(header_name, origin_sp)],
               [(header_name, site)],
               [(header_name, "null"), (header_name, "*")], [(header_name, origin_s), (header_name, "*")]
            ]

create_responses(header_list, label, resp_type="basic")
# Some basic headers with redirect
header_list = [[(header_name, "*"), redirect_empty], [(header_name, "null"), redirect_empty]]
create_responses(header_list, label, status_code=302, resp_type="basic")


#endregion
