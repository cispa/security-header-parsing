from models import Response, Session
from sqlalchemy.exc import IntegrityError
# TODO: create responses for each feature group (file in /tests)
# Some feature groups have more than one group of responses (label in the DB), e.g., framing has both XFO, CSP, and XFO vs CSP

# TODO: initially create two responses for each feature group (one always activating the feature, one always blocking the feature)

def create_responses(header_deny, header_allow, label, status_code=200):
    with Session() as session:
        for header in [header_deny, header_allow]:
            try:
                r = Response(raw_header=header, status_code=status_code, label=label)
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
create_responses(header_deny, header_allow, label)

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
create_responses(header_deny, header_allow, label)

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
create_responses(header_deny, header_allow, label)

#endregion

#region CORP
# Subresource loading/CORP
header_deny = [("Cross-Origin-Resource-Policy", "same-origin")]
header_allow = [("Cross-Origin-Resource-Policy", "cross-origin")]
label = "CORP"
create_responses(header_deny, header_allow, label)

#endregion

#region TODO COEP?
# TODO: what do we want to test here? which feature?
# CrossOriginIsolation is working? No non-corp ressources allowed while COEP is there?, ...

#endregion

#region Window References/COOP
header_deny = [("Cross-Origin-Opener-Policy", "same-origin")]
header_allow = [("Cross-Origin-Opener-Policy", "unsafe-none")]
label = "COOP"
create_responses(header_deny, header_allow, label)

#endregion

#region TODO: CORS and co.

# ACAC
# ACEH
# ....
#endregion

#region TODO: CSP XSS

#endregion

#region TODO: Maybe CSP subresource loading
#endregion

#region HSTS enforcement
# deny and allow are not fitting terms here, but does not matter
header_deny = [("Strict-Transport-Security", "max-age=20")]
header_allow = [("Strict-Transport-Security", "max-age=20; includeSubDomains")]
label = "HSTS"
create_responses(header_deny, header_allow, label)
#endregion

#region TODO: document.domain and site isolation?/OAC
#endregion

#region Permission access/PP
# https://github.com/w3c/webappsec-permissions-policy/blob/main/features.md
# https://fullscreen.spec.whatwg.org/#fullscreen-is-supported
# https://w3c.github.io/webappsec-permissions-policy/#policy-controlled-feature-default-allowlist
header_deny = [("Permissions-Policy", "fullscreen=()")]
header_allow = [("Permissions-Policy", "fullscreen=(*)")]
label = "PP"
create_responses(header_deny, header_allow, label)
#endregion

#region TODO: Referer/Referrer-Policy
#endregion

#region TODO: PerformanceAPI timing/TAO
#endregion
