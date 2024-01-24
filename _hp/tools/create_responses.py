from models import Response, Session

from crawler.utils import get_or_create

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


# Some feature groups have more than one group of responses (label in the DB), e.g., framing has both XFO, CSP, and XFO vs CSP
# crawler/utils.py defines which labels belong to which test file

def create_responses(header_list, label, status_code=200, resp_type="debug"):
    with Session() as session:
        for header in header_list:
         r, created = get_or_create(session, Response, raw_header=header, status_code=status_code, label=label, resp_type=resp_type)
         if created:
            print(r)


#region Framing

## XFO only
label = "XFO"
header_name = "x-frame-options" # https://html.spec.whatwg.org/multipage/document-lifecycle.html#the-x-frame-options-header
v1 = "DENY"
v2 = "SAMEORIGIN"
v3 = "INVALID"
v4 = "ALLOWALL"
v5 = ""
v6 = "null"
v7 = "*"
all_values = [v1, v2, v3, v4, v5, v6, v7]
header_deny = [(header_name, v1)]
header_allow = [(header_name, v2)]
create_responses([header_deny, header_allow], label)
header_list = [[(header_name, value)] for value in all_values]
header_list = header_list + [[], 
               [(header_name, f"{v1}, {v3}, {v4}")],
            ]
create_responses(header_list, label, resp_type="basic")
# Some basic headers with redirect
header_list = [[(header_name, v2), redirect_empty], [(header_name, v3), redirect_empty]]
create_responses(header_list, label, status_code=302, resp_type="basic")


## CSP-FA
label = "CSP-FA"
header_name = "Content-Security-Policy" # https://w3c.github.io/webappsec-csp/#csp-header
base = "frame-ancestors"
v1 = f"{base}"
v2 = f"{base} 'none'"
v3 = f"{base} *"
v4 = f"{base} 'self'"
v5 = f"{base} {origin_s}"
v6 = f"{base} {home}"
v7 = f"{base} {parent_childs}"
v8 = ""
v9 = f"{base}=*"
v10 = "default-src *"
v11 = f"{base} http:"
v12 = "null"
v13 = "*"
all_values = [v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13]
header_deny = [(header_name, v2)]
header_allow = [(header_name, v3)]
create_responses([header_deny, header_allow], label)
header_list = [[(header_name, value)] for value in all_values]
header_list = header_list + [[], 
               [(header_name, f"{v2}, {v3}, {v4}")],
            ]
create_responses(header_list, label, resp_type="basic")
# Some basic headers with redirect
header_list = [[(header_name, v2), redirect_empty], [(header_name, v3), redirect_empty]]
create_responses(header_list, label, status_code=302, resp_type="basic")


## XFO vs CSP
label = "CSPvsXFO"
h1 = "Content-Security-Policy"
h2 = "X-Frame-Options"
deny_cf = (h1, "frame-ancestors 'none'")
deny_x = (h2, 'DENY')
allowall_cf = (h1, '*')
allowall_x = (h2, 'INVALID')
allowsome_cf = (h1, f"frame-ancestors {parent_childs}")
allowsome_x = (h2, "SAMEORIGIN")
header_deny = [deny_cf, deny_x]
header_allow = [allowall_cf, allowall_x]
create_responses([header_deny, header_allow], label)
header_list = [[deny_cf, allowall_x], [deny_cf, allowsome_x], [allowall_cf, allowsome_x],
               [deny_x, allowall_cf], [deny_x, allowsome_cf]
            ]
create_responses(header_list, label, resp_type="basic")
# Some basic headers with redirect
header_list = [[(header_name, v2), redirect_empty], [(header_name, v3), redirect_empty]]
create_responses(header_list, label, status_code=302, resp_type="basic")
#endregion

#region CORP
# Subresource loading/CORP
label = "CORP"
header_name = "Cross-Origin-Resource-Policy" # https://fetch.spec.whatwg.org/#cross-origin-resource-policy-header
v1 = "unsafe-none"
v2 = "same-origin"
v3 = "same-site"
v4 = "cross-origin"
v5 = ""
v6 = "null"
v7 = "*"
all_values = [v1, v2, v3, v4, v5, v6, v7]
header_deny = [(header_name, v2)]
header_allow = [(header_name, v4)]
create_responses([header_deny, header_allow], label)
header_list = [[(header_name, value)] for value in all_values]
header_list = header_list + [[], 
               [(header_name, f"{v1}, {v3}, {v4}")],
            ]
create_responses(header_list, label, resp_type="basic")
# Some basic headers with redirect
header_list = [[(header_name, v2), redirect_empty], [(header_name, v3), redirect_empty]]
create_responses(header_list, label, status_code=302, resp_type="basic")

#endregion

#region COEP
# No non-corp ressources allowed while COEP is there, + crossOriginIsolated Flag
label = "COEP"
header_name = "Cross-Origin-Embedder-Policy" # https://html.spec.whatwg.org/multipage/browsers.html#coep
v1 = "unsafe-none"
v2 = "require-corp"
v3 = "credentialless"
v4 = "cross-origin"
v5 = ""
v6 = "null"
v7 = "*"
all_values = [v1, v2, v3, v4, v5, v6, v7]
header_deny = [(header_name, v2)]
header_allow = [(header_name, v1)]
create_responses([header_deny, header_allow], label)
header_list = [[(header_name, value)] for value in all_values]
header_list = header_list + [[], 
               [(header_name, f"{v1}, {v3}, {v4}")],
            ]
create_responses(header_list, label, resp_type="basic")
# Some basic headers with redirect
header_list = [[(header_name, v2), redirect_empty], [(header_name, v3), redirect_empty]]
create_responses(header_list, label, status_code=302, resp_type="basic")
#endregion

#region Window References/COOP
label = "COOP"
header_name = "Cross-Origin-Opener-Policy" # https://html.spec.whatwg.org/multipage/browsers.html#the-coop-headers
v1 = "unsafe-none"
v2 = "same-origin-allow-popups"
v3 = "same-origin"
v4 = "same-origin-plus-COEP"
v5 = ""
v6 = "null"
v7 = "*"
all_values = [v1, v2, v3, v4, v5, v6, v7]
header_deny = [(header_name, v3)]
header_allow = [(header_name, v1)]
create_responses([header_deny, header_allow], label)
header_list = [[(header_name, value)] for value in all_values]
header_list = header_list + [[], 
               [(header_name, f"{v1}, {v3}, {v4}")],
            ]
create_responses(header_list, label, resp_type="basic")
# Some basic headers with redirect
header_list = [[(header_name, v2), redirect_empty], [(header_name, v3), redirect_empty]]
create_responses(header_list, label, status_code=302, resp_type="basic")
#endregion

#region CORS
# For testing we only need one AC-XX headers pair
label = "CORS" # https://fetch.spec.whatwg.org/#http-responses
acao = "Access-Control-Allow-Origin"
acac = "Access-Control-Allow-Credentials"
acam = "Access-Control-Allow-Methods"
acah = "Access-Control-Allow-Headers"
aceh = "Access-Control-Expose-Headers"
base_resp = [("Test", "Test")]
header_deny = [(acao, "null")]
header_allow = [(acao, origin_s),
                 (acac, "true"),
                 (acam, "TEST"),
                 (acah, "Test"),
                 (aceh, "Test"),
                 ("Test", "Test"),
                 # ("Access-Control-Max-Age", "10") # Caching
                ]
create_responses([header_deny, header_allow], label)
header_list = [base_resp + [(acao, origin)],
               base_resp + [(acac, "true")],
               base_resp + [(acao, "*")] + [(acac, "true")],
               base_resp + [(acao, origin_s)] + [(acac, "true")] + [(acam, "TEST")] + [(acah, "Test")] + [(aceh, "Test")]
               ]
create_responses(header_list, label, resp_type="basic")
# Some basic headers with redirect
header_list = [[(acao, origin_s), redirect_empty], [(acao, "*"), redirect_empty]]
create_responses(header_list, label, status_code=302, resp_type="basic")
#endregion

#region CSP script-execution
label = "CSP-SCRIPT"
header_name = "Content-Security-Policy" # https://w3c.github.io/webappsec-csp/#csp-header
base = "script-src"
v1 = f"{base}"
v2 = f"{base} 'none'"
v3 = f"{base} *"
v4 = f"{base} 'self'"
v5 = f"{base} {origin_s}"
v6 = f"{base} {home}"
v7 = f"{base} {parent_childs}"
v8 = ""
v9 = f"{base}=*"
v10 = "default-src *"
v11 = f"{base} http:"
v12 = "null"
v13 = "*"
all_values = [v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13]
header_deny = [(header_name, v2)]
header_allow = [(header_name, v3)]
create_responses([header_deny, header_allow], label)
header_list = [[(header_name, value)] for value in all_values]
header_list = header_list + [[], 
               [(header_name, f"{v2}, {v3}, {v4}")],
            ]
create_responses(header_list, label, resp_type="basic")
# Some basic headers with redirect
header_list = [[(header_name, v2), redirect_empty], [(header_name, v3), redirect_empty]]
create_responses(header_list, label, status_code=302, resp_type="basic")
#endregion

#region CSP subresource loading (image)
label = "CSP-IMG"
header_name = "Content-Security-Policy" # https://w3c.github.io/webappsec-csp/#csp-header
base = "img-src"
v1 = f"{base}"
v2 = f"{base} 'none'"
v3 = f"{base} *"
v4 = f"{base} 'self'"
v5 = f"{base} {origin_s}"
v6 = f"{base} {home}"
v7 = f"{base} {parent_childs}"
v8 = ""
v9 = f"{base}=*"
v10 = "default-src *"
v11 = f"{base} http:"
v12 = "null"
v13 = "*"
all_values = [v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13]
header_deny = [(header_name, v2)]
header_allow = [(header_name, v3)]
create_responses([header_deny, header_allow], label)
header_list = [[(header_name, value)] for value in all_values]
header_list = header_list + [[], 
               [(header_name, f"{v2}, {v3}, {v4}")],
            ]
create_responses(header_list, label, resp_type="basic")
# Some basic headers with redirect
header_list = [[(header_name, v2), redirect_empty], [(header_name, v3), redirect_empty]]
create_responses(header_list, label, status_code=302, resp_type="basic")
#endregion

#region HSTS enforcement
# deny and allow are not fitting terms here, but does not matter
label = "HSTS"
header_name = "Strict-Transport-Security" # https://www.rfc-editor.org/rfc/rfc6797#section-6.1
v1 = "max-age=20"
v2 = "max-age=20; includeSubDomains"
v3 = "includeSubDomains"
v4 = ""
v5 = "max-age=20; includeSubDomains; preload"
v6 = "max-age=0"
v7 = "max-age=-5"
header_deny = [(header_name, v1)]
header_allow = [(header_name, v2)]
create_responses([header_deny, header_allow], label)
header_list = [[(header_name, "*")], [], 
               [(header_name, "null")], [(header_name, v1)],
               [(header_name, v2)], [(header_name, v3)],
               [(header_name, v4)], [(header_name, v5)],
               [(header_name, v6)], [(header_name, v7)],
               [(header_name, f"{v1}, {v2}, {v3}, {v4}, {v5}, {v6}, {v7}")],
               [(header_name, f"abc, {v1}")]
            ]
# TODO
# [["Strict-Transport-Security", "max-age=20"], ["Strict-Transport-Security", "max-age=20; includeSubDomains"], ["Strict-Transport-Security", "includeSubDomains"], ["Strict-Transport-Security", ""], ["Strict-Transport-Security", "max-age=20; includeSubDomains; preload"], ["Strict-Transport-Security", "max-age=0"], ["Strict-Transport-Security", "max-age=-5"]]
create_responses(header_list, label, resp_type="basic")
# Some basic headers with redirect
header_list = [[(header_name, v1), redirect_empty], [(header_name, v2), redirect_empty]]
create_responses(header_list, label, status_code=302, resp_type="basic")
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
header_deny = [(header_name, v1)]  # Set OAC, secure value
header_allow = [(header_name, v2)] # Disable OAC, insecure value
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
