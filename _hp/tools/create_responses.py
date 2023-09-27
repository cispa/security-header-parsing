from models import Response, Session
from sqlalchemy.exc import IntegrityError
# TODO: create responses for each feature group (file in /tests)
# Some feature groups have more than one group of responses (label in the DB), e.g., framing has both XFO, CSP, and XFO vs CSP

# TODO: initially create two responses for each feature group (one always activating the feature, one always blocking the feature)

def create_responses(header_deny, header_allow, label):
    status_code = 200
    http_ver = "1.1"
    with Session() as session:
        for header in [header_deny, header_allow]:
            try:
                r = Response(raw_header=header, status_code=status_code, http_ver=http_ver, label=label)
                session.add(r)
                session.commit()
            except IntegrityError as e:
                session.rollback()
                print("IntegrityError probably response already exists")


# Framing

## XFO only
header_deny = [("X-Frame-Options", "DENY")]
header_allow = [("X-Frame-Options", "INVALID")]
label = "XFO"
create_responses(header_deny, header_allow, label)

## CSP-FA
header_deny = [("Content-Security-Policy", "frame-ancestors 'none'")]
header_allow = [("Content-Security-Policy", "frame-ancestors *")]
label = "CSP-FA"
create_responses(header_deny, header_allow, label)

## XFO vs CSP
header_deny = [("Content-Security-Policy", "frame-ancestors 'none'"), ('X-Frame-Options', 'DENY')]
header_allow = [("Content-Security-Policy", "frame-ancestors *"), ('X-Frame-Options', 'INVALID')]
label = "CSPvsXFO"
create_responses(header_deny, header_allow, label)

# Subresource loading/CORP
header_deny = [("Cross-Origin-Resource-Policy", "same-origin")]
header_allow = [("Cross-Origin-Resource-Policy", "cross-origin")]
label = "CORP"
create_responses(header_deny, header_allow, label)

# COEP?
# TODO: what do we want to test here? which feature?
# CrossOriginIsolation is working? No non-corp ressources allowed while COEP is there?, ...

# Window References/COOP
header_deny = [("Cross-Origin-Opener-Policy", "same-origin")]
header_allow = [("Cross-Origin-Opener-Policy", "cross-origin")]
label = "COOP"
create_responses(header_deny, header_allow, label)

# TODO: CORS and co.
# ACAC
# ACEH
# ....

# TODO: CSP XSS

# TODO: Maybe CSP subresource loading

# TODO: HSTS enforcement

# TODO: document.domain and site isolation?/OAC

# TODO: Permission access/PP

# TODO: Referer/Referrer-Policy

# TODO: PerformanceAPI timing/TAO

