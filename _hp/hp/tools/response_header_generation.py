#!/usr/bin/env python
# coding: utf-8

# In[1]:


import random
import re
import httpx
import glob
import os
import json
from itertools import permutations, product, chain

from hp.tools.models import Response, Session
from hp.tools.crawler.utils import get_or_create


# In[2]:


def randomize_casing(input_string, seed=42):
    """Randomize the casing of a string (fixed with a seed)."""
    random.seed(seed)
    return ''.join(random.choice([c.upper(), c.lower()]) for c in input_string)

def insert_char_middle(input_string, char):
    """Insert a char in the middle of a string."""
    middle_index = len(input_string) // 2
    return input_string[:middle_index] + char + input_string[middle_index:]


# In[3]:


# All the mutations we apply on strings such as header names and header values
# Some of them may have no effect and result in duplicates; however such duplicates are not saved in the db

all_upper = lambda x: x.upper()
all_lower = lambda x: x.lower()
random_case = lambda x: randomize_casing(x)
leadtrail_space = lambda x: " " + x + " "
in_double_quotes = lambda x: '"' + x + '"'
in_single_quotes = lambda x: "'" + x + "'"
remove_whitespace = lambda x: x.replace(" ", "")
double_spaces = lambda x: x.replace(" ", "  ")
space_to_tab = lambda x: x.replace(" ", "\t")

lead_seqs = []
trail_seqs = []
middle_seqs = []

# All all ASCII chars as leading, trailing, and middle char
ascii_chars = [char for char in map(chr, range(128))]
# Alternatively use less ones? All/Some control chars? + space, comma, ....
# ascii_chars = [char for char in map(chr, range(32))] + [" ", ",", ";", ":"]
for seq in ascii_chars:
    lead_seqs.append(lambda x, s=seq: s + x)
    trail_seqs.append(lambda x, s=seq: x + s)
    middle_seqs.append(lambda x, s=seq: insert_char_middle(x, s))

# Add other interesting leading, trailing, middle chars: Double space, non-breaking space, full-width comma
# MAYBE: add more?
other_chars = ["  ", "\u00A0a", "\uFF0C"]
for seq in other_chars:
    lead_seqs.append(lambda x, s=seq: s + x)
    trail_seqs.append(lambda x, s=seq: x + s)
    middle_seqs.append(lambda x, s=seq: insert_char_middle(x, s))

# Replace some chars with others
chars_to_replace = [";", ",", ":", "=", "'", '"', "-", "_"]
# Replace each of the above with all of the below
replace_chars = [
    "", " ", ";", ",", ":", "=", "-", "_",
    "'", '"', "`", "´",
    '\u2018',  # Left Single Quotation Mark
    '\u2019',  # Right Single Quotation Mark
    '\u201A',  # Single Low-9 Quotation Mark
    '\u201B',  # Single High-Reversed-9 Quotation Mark
    '\u201C',  # Left Double Quotation Mark
    '\u201D',  # Right Double Quotation Mark
    '\u201E',  # Double Low-9 Quotation Mark
    '\u201F',  # Double High-Reversed-9 Quotation Mark
]
replace_funcs = []
for char in chars_to_replace:
    for rp in replace_chars:
        if rp == char:
            continue
        replace_funcs.append(lambda x, c1=char, c2=rp: x.replace(c1, c2))



general_mutations = [
    all_upper,
    all_lower,
    random_case,
    leadtrail_space,
    in_double_quotes,
    in_single_quotes,
    remove_whitespace,
    double_spaces,
    space_to_tab,
    *lead_seqs,
    *trail_seqs,
    *middle_seqs,
    *replace_funcs,
]

basic_mutations = [
    #all_upper,
    all_lower,
    random_case,
    leadtrail_space,
]


def mutate_header_name(header_name):
    header_names = set()
    for mutation in general_mutations:
        header_names.add(mutation(header_name))
    return header_names

def mutate_header_value(header_value, mutation_list=general_mutations):
    header_values = set()
    for mutation in mutation_list:
        header_values.add(mutation(header_value))
    return header_values


# In[4]:


l = mutate_header_value("D EN'Y")
print(l)
print(list(l)[0])


# In[5]:


class HeaderTests:
    def __init__(self, label: str, header_name: str, alt_names: list[str], block_values: list[str], allow_values: list[str], partial_values: list[str], legacy_values: list[str], other_values: list[str], base_resp: list[tuple[str, str]]=None):
        """"HeaderTests class to create lots of responses
        label (str): Additional information about these responses (e.g., XFO)
        header_name (str): The correct lower-case name of the header
        alt_names (list[str]): Legacy and other (invalid) alternative header names
        block_values (list[str]): Valid values to set the header to "blocking" (e.g., DENY for XFO means always disallow framing)
        allow_values (list[str]): Valid values to set the header to "allowing" (e.g., unsafe-none  for COOP means do not activate COOP/always allow)
        partial_values (list[str]): Valid values to set the header to an intermediate mode (e.g., SAMEORIGIN for XFO means allow framing only for same-origin)
        legacy_values (list[str]): Legacy values that should not work anymore
        other_values (list[str]): Other values we want to test as well (can include valid ones if we do not want to put too many in the other categories)
        base_resp (list[tuple[str, str]] | None): Base response that other stuff is only added to (default None)
        """
        self.label = label
        self.header_name = header_name
        self.alt_names = alt_names
        self.block_values = block_values
        self.allow_values = allow_values
        self.partial_values = partial_values
        self.legacy_values = legacy_values
        self.other_values = other_values
        self.base_resp = base_resp
        self.responses = []

    def create_response(self, header, label, status_code=200, resp_type="parsing"):
        if self.base_resp:
            header = header + self.base_resp
        self.responses.append((header, label, status_code, resp_type))

    def save_responses(self):
        create_count = 0
        with Session() as session:
            for header, label, status_code, resp_type in self.responses:
                r, created = get_or_create(session, Response, raw_header=json.dumps(header).encode("utf-8"), status_code=status_code, label=label, resp_type=resp_type)
                if created:
                    create_count += 1
        print(len(self.responses))
        print(f"Created: {create_count}")
        print(self.responses[:5])

    def header_name_tests(self):
        """Test all block, allow, partial values (correct values)
            with the correct header names, with all alternative/legacy header names, and with mutated versions of the correct header_name
        """
        for value_group in [self.block_values, self.allow_values, self.partial_values]:
            for header_value in value_group:
                # Original header name
                self.create_response([(self.header_name, header_value)], self.label)
                # Alt header names
                for header_name in self.alt_names:
                    self.create_response([(header_name, header_value)], self.label)
                # Mutated header names
                for header_name in mutate_header_name(self.header_name):
                    self.create_response([(header_name, header_value)], self.label)

    def parsing_tests(self):
        """Test all header values + mutated versions.
        """
        # Test all legacy and other values (block, allow, partial do not have to be tested as they are already tests by header_name_tests)
        for value_group in [self.legacy_values, self.other_values]:
            for header_value in value_group:
                self.create_response([(self.header_name, header_value)], self.label)
        
        # Mutate/change header values (block, allow, partial)
        for value_group in [self.block_values, self.allow_values, self.partial_values]:
            for org_header_value in value_group:
                # Other status codes
                for code in [201, 203, 204, 300, 302, 400, 403, 404, 418, 500]:
                    if 300 <= code < 400:
                        self.create_response([(self.header_name, org_header_value), redirect_empty], self.label, status_code=code)
                    else:
                        self.create_response([(self.header_name, org_header_value)], self.label, status_code=code)
                # Mutated header values
                for header_value in mutate_header_value(org_header_value):
                    self.create_response([(self.header_name, header_value)], self.label)

    def mult_headers_tests(self):
        """Test involving multiple headers/values
        """
        all_valid_values = self.block_values + self.allow_values + self.partial_values
        all_orders = list(permutations(all_valid_values))
        # Basic1: all legal values in a list in all possible orders (Comma, space, semicolon-separated)
        for order in all_orders:
            self.create_response([(self.header_name, ", ".join(order))], self.label)
            self.create_response([(self.header_name, "; ".join(order))], self.label)
            self.create_response([(self.header_name, " ".join(order))], self.label)
        
        # Basic2: all legal values in separate headers in all possible orders
        for order in all_orders:
            headers = [(self.header_name, header_value) for header_value in order]
            self.create_response(headers, self.label)
        # Basic3: all legal values in both separate headers and in one header with comma?!
        # Only if at least 3 values; split in first and all others and last and all others
        for order in all_orders:
            if len(order) >= 3:
                first, rest1 = order[0], ", ".join(order[1:])
                rest2, last = ", ".join(order[:-1]), order[-1]
                self.create_response([(self.header_name, first), (self.header_name, rest1)], self.label)
                self.create_response([(self.header_name, rest2), (self.header_name, last)], self.label)

        # Basic4: all legal values duplicated
        for value in all_valid_values:
            self.create_response([(self.header_name, value), (self.header_name, value)], self.label)
            self.create_response([(self.header_name, f"{value}, {value}")], self.label)
            
            # Could be extended with mutated versions once, e.g., X-Frame-Options: ALLOWALL, allowall;
            # Browsers should first lowercase and then put each value in a set https://html.spec.whatwg.org/multipage/document-lifecycle.html#the-x-frame-options-header
            # Which means no blocking should occur, if they forget the lowercasing part, the set size would be two and it would be blocked
            # Other extensions possible as well
            self.create_response([(self.header_name, value), (self.header_name, value.lower())], self.label)
            self.create_response([(self.header_name, value), (self.header_name, value.upper())], self.label)
        
        # Advanced1: use different header names (e.g., if a browser accepts both x-frame-options and X-FRAME-OPTIONS which takes precedence?; might be neither if the browser first lower-cases or something like that)
        # Currently only either uppercase the first header or all except the first header (other mutations and header duplication strategies could be added in the future)
        # Could be extended with clearly invalid headers (e.g., leading or trailing space, ...)
        for order in all_orders:
            for (header1, header2) in [(self.header_name, self.header_name.upper()), (self.header_name.upper(), self.header_name)]:
                # headers = [(self.header_name, header_value) for header_value in order]
                headers = []
                for i, header_value in enumerate(order):
                    if i == 0:
                        headers.append((header1, header_value))
                    else:
                        headers.append((header2, header_value))
                self.create_response(headers, self.label)
    
        # Advanced2: use invalid values as well (e.g., a browser might always take the first header while another browser takes the first valid header?)
        for valid_value in all_valid_values:
            # Only use the first two invalid values (should be empty and a clearly invalid value ("INVALID")
            # Could be extended with more complex approaches
            for invalid_value in self.other_values[:2]:
                self.create_response([(self.header_name, valid_value), (self.header_name, invalid_value)], self.label)
                self.create_response([(self.header_name, invalid_value), (self.header_name, valid_value)], self.label)
                self.create_response([(self.header_name, f"{valid_value}, {invalid_value}")], self.label)
                self.create_response([(self.header_name, f"{invalid_value}, {valid_value}")], self.label)
                
    def create_all_tests(self):
        self.header_name_tests()
        self.parsing_tests()
        self.mult_headers_tests()
        self.save_responses()


# In[6]:


class HeaderTestsMultHeader(HeaderTests):
    def __init__(self, header_names, values, label, base_resp=None):
        """
        header_names (list[str]): List of header names
        values (dict[str:str]): List of list of values 
        label (str): Label of the response
        """
        assert len(header_names) == len(values)
        self.header_names = header_names
        self.values = values
        self.label = label
        self.responses = []
        self.base_resp = base_resp
        
    def create_all_tests(self):
        # Test all values in all orders of headers
        all_header_orders = list(permutations(self.header_names))
        all_header_orders = [tuple(zip(pair, pair)) for pair in all_header_orders]
        
        # Mutate the header names (basic mutations only)
        mutated_headers = []
        for org_header in self.header_names:
            mutated_headers.append([(org_header, header) for header in mutate_header_value(org_header, mutation_list=basic_mutations)])
        # All possible orders of the mutated headers
        mutated_order = [
            tuple(product(*(mutated_headers[n] for n in list_order)))
            for list_order in permutations(range(len(mutated_headers)))
        ]
        mutated_order = [item for sublist in mutated_order for item in sublist]
        # For each header choose each value
        for headers in mutated_order:
        #for headers in all_header_orders: # No mutations, only the original headers
            # Do not use all combinations of values (too many) but instead cycle through available value (pairs)
            for i in range(len(max(self.values.values(), key=len, default=0))):
                resp = []
                for (org_header, header) in headers:      
                    index = i % len(self.values[org_header]) # Safe index (cycle the list if some have more values than others)
                    resp.append((header, self.values[org_header][index]))
                
                self.create_response(resp, self.label)
        self.save_responses()


# In[7]:

try:
	wpt_config = json.load(open("/app/_hp/wpt-config.json"))
except OSError:
	try:
		wpt_config = json.load(open("../../wpt-config.json"))
	except OSError:
		wpt_config = json.load(open("../../../wpt-config.json"))

base_host = wpt_config["browser_host"]
alt_host = wpt_config["alternate_hosts"]["alt"]
redirect_empty = ("location", f"https://sub.{base_host}/_hp/common/empty.html")
site = f"sub.{base_host}"
origin_s = f"https://sub.{base_host}"
origin_s_upper = f"HTTPS://SUB.{base_host}".upper()
origin_s_path = f"{origin_s}/abc/"
origin_s_query = f"{origin_s}/?a=a"
origin = f"http://sub.{base_host}"
origin_sp = f"{origin_s}:443"
home = f"{origin_s}/"
home_p = f"{origin_sp}/"
parent = f"https://{base_host}"
child = f"https://sub.sub.{base_host}"
parent_childs = f"*.{base_host}"
self_childs = f"*.sub.{base_host}"
self_childs_https = f"https://*.sub.{base_host}"
cross_site_origin = f"https://{alt_host}"
all_replacements = [site, origin_s, origin_s_upper, origin_s_path, origin_s_query, origin, origin_sp, home, home_p, parent, child, parent_childs, self_childs, self_childs_https, cross_site_origin]
URL_REP = "<!URL!>"


# In[8]:


def expand_urls(other_values):
    """Use different URL, origins, sites variations if the value should allow some sites"""
    return_values = []
    for value in other_values:
        if not URL_REP in value:
            return_values.append(value)
        else:
            # Only if less than 2 occurrences? Else chose a random value for each?

            # Currently: replace all occurrences of URL_REP with the same url_like
            for url_like in all_replacements:
                return_values.append(value.replace(URL_REP, url_like))
    return return_values


# In[9]:


label = ""
header_name = ""
alt_names = []
block_values = []
allow_values = []
partial_values = []
legacy_values = []
# Always start with the empty value and then an INVALID value (e.g., "INVALID"), after that both valid and invalid values can be added
# We use the first two in `mult_headers_test`
other_values = ["", "INVALID"]
other_values = expand_urls(other_values)


# In[10]:


def get_values(url, pattern):
    content = httpx.get(url).text
    content = content.replace("TESTURI", URL_REP)
    content = content.replace("http://randomorigin.com/", URL_REP)
    content = content.replace("http://randomorigin.com", URL_REP)
    content = content.replace("http://much.ninja", URL_REP)
    content = content.replace("http://random.ninja", URL_REP)
    content = content.replace("https://much.ninja", URL_REP)
    content = content.replace("http://*.ninja", URL_REP)
    content = content.replace("*.ninja", URL_REP)
    content = content.replace("much.ninja", URL_REP)
    matches = list(set(re.findall(pattern, content)))
    return matches

# siewert_xfo = get_values("https://raw.githubusercontent.com/hen95/HTTPHeaderBrowserTesting/main/transform_to_testcase.py", r"\'X-Frame-Options: (.*?)\'")
siewert_xfo = ['deny, deny', 'allow-from <!URL!>; allow-from <!URL!>', 'deny, sameorigin', 'deny, allow-from <!URL!>', 'RANDOMDIRECTIVE', 'deny; deny', 'deny; allow-from <!URL!>', 'allowall', 'allow-from <!URL!>, allow-from <!URL!>', 'deny; sameorigin', 'sameorigin, allow-from <!URL!>', 'allow-from <!URL!>', 'allow-from <!URL!>, deny', 'sameorigin', 'sameorigin, deny', 'deny', 'sameorigin, sameorigin', 'sameorigin; deny', 'allow-from <!URL!>, sameorigin', 'sameorigin; sameorigin', 'allow-from <!URL!>; deny']
print(siewert_xfo)
print()
# siewert_csp = get_values("https://raw.githubusercontent.com/hen95/HTTPHeaderBrowserTesting/main/transform_to_testcase.py", r"\'Content-Security-Policy: (.*?)\'")
siewert_csp = ['frame-ancestors https:;', 'frame-ancestors http:;', 'frame-ancestors <!URL!> <!URL!>;', 'frame-ancestors <!URL!>;']
print(siewert_csp)


# In[11]:


def get_wpt_values(dir_path, pattern=r'headerValue: `(.*)`|headerValue2: `(.*)`'):
    # Initialize a list to store matching strings
    values = set()
    # Use glob to find all files with the specified extension recursively
    file_paths = glob.glob(os.path.join(dir_path, '*.html'), recursive=False)
    # Iterate through the list of file paths
    for file_path in file_paths:
        with open(file_path, 'r') as f:
            content = f.read()
            content = content.replace("https://example.com/", URL_REP)
            matches = re.findall(pattern, content)
            for match1, match2 in matches:
                values.add(match1)
                values.add(match2)
    return list(values)

#wpt_xfo = get_wpt_values('../../../x-frame-options/') # We removed all unrelated WPT folders; to rerun clone the original WPT repo and set the correct path
wpt_xfo = ['', 'SAMEORIGIN', '  SAMEORIGIN ', '"SAMEORIGIN,DENY"', '  SAMEORIGIN,    DENY', '  DENY ', 'ALLOWALL', '"DENY"', 'ALLOW-FROM <!URL!>', 'denY', '"SAMEORIGIN"', 'sameOriGin', 'DENY', ',SAMEORIGIN,,DENY,', 'INVALID', 'allowAll', 'sameOrigin', 'ALLOW-FROM=<!URL!>']
wpt_xfo


# In[43]:


def limit_url_occurrences(input_string, max_occurrences):
    # Define the pattern to match <!URL!>
    url_pattern = re.compile(rf'{URL_REP}(?:(\s|,)*(ALLOW-FROM )?(allow-from )?{URL_REP})+')
    #url_pattern = re.compile(rf'{URL_REP}(?:(\s|,)*{URL_REP})+')

    # Find all consecutive occurrences of <!URL!>
    consecutive_url_matches = url_pattern.findall(input_string)

    # Calculate the number of replacements needed
    replacements_needed = max(0, len(consecutive_url_matches) - max_occurrences)

    # Replace excess consecutive occurrences with <!URL!>
    replaced_string = url_pattern.sub('', input_string, count=replacements_needed)

    return replaced_string


def replace_multiple_urls(input_string):
    # Define the pattern to match three or more consecutive <!URL!>
    url_pattern = re.compile(r'((<!URL!>\s*){3,})')

    # Replace three or more consecutive <!URL!> with a single <!URL!>
    replaced_string = re.sub(url_pattern, '<!URL!> ', input_string)

    return replaced_string


def run_replacements(input_string):
    input_string = replace_multiple_urls(input_string)
    input_string = limit_url_occurrences(input_string, 4)
    input_string = re.sub("sha256-\S+", "sha256-default", input_string)
    # Replace 4 digit numbers and higher with 60 (for HSTS; should not affect other headers?)
    input_string = re.sub("\d{4,}", "60", input_string)
    return input_string

def get_crawler_values(url, min_count=0):
    if "https://" in url:
        content = httpx.get(url).text
        content = re.sub(r"(http(s)?|HTTP(S)?)://[\w.*/\-:?=]*|([\w*\-/]+\.)+[\w*\-:/?=]+", URL_REP, content)
        rows = [row.rsplit(" ", maxsplit=1) for row in content.split("\r\n")[1:] if " " in row]
    else:
        content = open(url, 'r', encoding='utf-8', errors="backslashreplace").read()
        content = re.sub(r"(http(s)?|HTTP(S)?)://[\w.*/\-:?=]*|([\w*\-/]+\.)+[\w*\-:/?=]+", URL_REP, content)
        rows = [row.rsplit(" ", maxsplit=1) for row in content.split("\n")[1:] if " " in row]
    # Only use values occuring more than once? Otherwise we have to many possible values?
    filtered_rows = []
    for row in rows:
        try:
            if int(row[1].replace(",", "")) >= min_count:
                filtered_rows.append(row[0])
        except (ValueError, IndexError):
            # Ignore rows that cause errors
            pass
    return list(set([run_replacements(row) for row in filtered_rows]))

#crawler_ninja_xfo = get_crawler_values("https://crawler.ninja/files/xfo-values.txt")
crawler_ninja_xfo = get_crawler_values("cached_crawler-ninja_values/xfo-values.txt")
print(len(crawler_ninja_xfo))
#display(crawler_ninja_xfo)
#crawler_ninja_csp = get_crawler_values("https://crawler.ninja/files/csp-values.txt", min_count=2)
crawler_ninja_csp = get_crawler_values("cached_crawler-ninja_values/csp-values.txt", min_count=2)
print(len(crawler_ninja_csp))
#crawler_ninja_csp


# In[45]:


label = "XFO"
header_name = "x-frame-options"
alt_names = ["frame-options", "x-frame-option", "x-frames-options", "content-security-policy", "x_frame_options", "xframeoptions"]
block_values = ["DENY"]
allow_values = ["ALLOWALL"] # This value does not really exist but has some special meaning for processing multiple values (https://html.spec.whatwg.org/multipage/document-lifecycle.html#the-x-frame-options-header)
partial_values = ["SAMEORIGIN"]
legacy_values = [f"ALLOW-FROM {origin_s}"]

# Always start with the empty value and then an INVALID value (e.g., "INVALID"), after that both valid and invalid values can be added
# We use the first two in `mult_headers_test`
basic_values = ["", "INVALID", "null", "*", URL_REP]
# https://wpt.fyi/results/x-frame-options?label=master&label=experimental&aligned&q=x-frame
wpt_values = ['', 'SAMEORIGIN', '  SAMEORIGIN ', '"SAMEORIGIN,DENY"', '  SAMEORIGIN,    DENY', '  DENY ', 'ALLOWALL', '"DENY"', 'ALLOW-FROM <!URL!>', 'denY', '"SAMEORIGIN"', 'sameOriGin', 'DENY', ',SAMEORIGIN,,DENY,', 'INVALID', 'allowAll', 'sameOrigin', 'ALLOW-FROM=<!URL!>']
# https://github.com/hen95/HTTPHeaderBrowserTesting
siewert_values = ['deny, deny', 'allow-from <!URL!>; allow-from <!URL!>', 'deny, sameorigin', 'deny, allow-from <!URL!>', 'RANDOMDIRECTIVE', 'deny; deny', 'deny; allow-from <!URL!>', 'allowall', 'allow-from <!URL!>, allow-from <!URL!>', 'deny; sameorigin', 'sameorigin, allow-from <!URL!>', 'allow-from <!URL!>', 'allow-from <!URL!>, deny', 'sameorigin', 'sameorigin, deny', 'deny', 'sameorigin, sameorigin', 'sameorigin; deny', 'allow-from <!URL!>, sameorigin', 'sameorigin; sameorigin', 'allow-from <!URL!>; deny']
# https://crawler.ninja/files/xfo-values.txt
#crawler_ninja_values = get_crawler_values("https://crawler.ninja/files/xfo-values.txt")
crawler_ninja_values = get_crawler_values("cached_crawler-ninja_values/xfo-values.txt")
own_values = []
other_values = basic_values + wpt_values + siewert_values + crawler_ninja_values + own_values
other_values = expand_urls(other_values)
xfo_all = block_values + allow_values + partial_values + legacy_values + other_values
ht = HeaderTests(label, header_name, alt_names, block_values, allow_values, partial_values, legacy_values, other_values)
ht.create_all_tests()


# In[38]:


label = "CSP-FA"
header_name = "content-security-policy"
alt_names = ["x-content-security-policy", "x-webkit-csp", "x-webkit-content-security-policy"]
block_values = ["frame-ancestors 'none'"]
allow_values = ["frame-ancestors *"]
partial_values = ["frame-ancestors 'self'"]
legacy_values = []
# Always start with the empty value and then an INVALID value (e.g., "INVALID"), after that both valid and invalid values can be added
# We use the first two in `mult_headers_test`
basic_values = ["", "INVALID", "null", "*", URL_REP]
# https://wpt.fyi/results/content-security-policy/frame-ancestors?label=master&label=experimental&aligned&q=frame
wpt_values = ["frame-ancestors 'none'", "frame-ancestors 'self'", "frame-ancestors *", f"frame-ancestors {URL_REP}"]
# https://github.com/hen95/HTTPHeaderBrowserTesting
# siewert_values = get_values("https://raw.githubusercontent.com/hen95/HTTPHeaderBrowserTesting/main/transform_to_testcase.py", r"\'Content-Security-Policy: (.*?)\'")
siewert_values = ['frame-ancestors https:;', 'frame-ancestors http:;', 'frame-ancestors <!URL!> <!URL!>;', 'frame-ancestors <!URL!>;']

# https://crawler.ninja/files/csp-values.txt
crawler_ninja_values = []
# Note: add crawler_ninja_values, Problem: Too many? Many are very similar and URL replacement results in a massive number of values
# crawler_ninja_values = get_crawler_values("https://crawler.ninja/files/csp-values.txt", min_count=2)
# crawler_ninja_values = get_crawler_values("cached_crawler-ninja_values/csp-values.txt", min_count=2)

own_values = ["default-src 'none'", "self", "*", "frame-ancestors self", "frame-ancestors", "frame-ancestors none", "frame-src none", "frame-ancestors 'null'", "frame-ancestors null"]
other_values = basic_values + wpt_values + siewert_values + crawler_ninja_values + own_values
other_values = expand_urls(other_values)
csp_fa_all = block_values + allow_values + partial_values + legacy_values + other_values
ht = HeaderTests(label, header_name, alt_names, block_values, allow_values, partial_values, legacy_values, other_values)
ht.create_all_tests()


# In[46]:


# CORS: fixate all header except one, only mutate/rotate this one header

# https://wpt.fyi/results/cors?label=master&label=experimental&aligned&q=cors
wpt_values = [] # Nothing parsing related?
# https://github.com/hen95/HTTPHeaderBrowserTesting
siewert_values = [] # Difficult to extract
# https://crawler.ninja/files/acao-values.txt
crawler_ninja_values = [] # Only ACAO and mostly different origins

label = "CORS"
alt_names = []
full_base_resp = [("Test", "Test"), ("access-control-allow-origin", origin_s), ("access-control-allow-credentials", "true"), ("access-control-allow-methods", "TEST"), ("access-control-allow-headers", "Test"), ("access-control-expose-headers", "Test")]


# ACAO
label = "CORS-ACAO"
header_name = "access-control-allow-origin"
base_resp = [tup for tup in full_base_resp if tup[0] != header_name]
block_values = ["null"]
allow_values = ["*"] 
partial_values = [origin_s]
legacy_values = []
basic_values = ["", "INVALID", "null", "*", "Test", "true", "?1", "?0", "TEST", "test", "false", "https://", "//", URL_REP]
other_values = expand_urls(basic_values)
ht = HeaderTests(label, header_name, alt_names, block_values, allow_values, partial_values, legacy_values, other_values, base_resp)
ht.create_all_tests()

# ACAC
label = "CORS-ACAC"
header_name = "access-control-allow-credentials"
base_resp = [tup for tup in full_base_resp if tup[0] != header_name]
block_values = []
allow_values = ["true"] 
partial_values = []
legacy_values = []
basic_values = ["", "INVALID", "null", "*", "Test", "true", "?1", "?0", "TEST", "test", "false", "https://", "//", URL_REP]
other_values = expand_urls(basic_values)
ht = HeaderTests(label, header_name, alt_names, block_values, allow_values, partial_values, legacy_values, other_values, base_resp)
ht.create_all_tests()

# ACAM, ACAH, ACEH
for header_name in ["access-control-allow-methods", "access-control-allow-headers", "access-control-expose-headers"]:
    label = f"CORS-{''.join([h[0].upper() for h in header_name.split('-')])}"
    base_resp = [tup for tup in full_base_resp if tup[0] != header_name]
    block_values = []
    allow_values = ["*"] 
    if "methods" in header_name:
        partial_values = ["TEST"]
    else:
        partial_values = ["Test"]
    legacy_values = []
    basic_values = ["", "INVALID", "null", "*", "Test", "true", "?1", "?0", "TEST", "test", "false", "https://", "//", URL_REP]
    other_values = expand_urls(basic_values)
    ht = HeaderTests(label, header_name, alt_names, block_values, allow_values, partial_values, legacy_values, other_values, base_resp)
    ht.create_all_tests()


# In[47]:


label = "CORP"
header_name = "cross-origin-resource-policy"
alt_names = ["from-origin", "x-cross-origin-resource-policy"]
block_values = [""]
allow_values = ["cross-origin"]
partial_values = ["same-site", "same-origin"]
legacy_values = []
# Always start with the empty value and then an INVALID value (e.g., "INVALID"), after that both valid and invalid values can be added
# We use the first two in `mult_headers_test`
basic_values = ["", "INVALID", "null", "*", URL_REP]
# https://wpt.fyi/results/fetch/cross-origin-resource-policy?label=master&label=experimental&aligned&q=cross-origin-resource-policy
wpt_values = ["same", "same, same-origin", "SAME-ORIGIN", "Same-Origin", "same-origin, <>", "same-origin, same-origin", URL_REP]
# https://github.com/hen95/HTTPHeaderBrowserTesting
siewert_values = [] # No CORP tested
# https://crawler.ninja/files
crawler_ninja_values = [] # No CORP tested
own_values = ["unsafe-none"]
other_values = basic_values + wpt_values + siewert_values + crawler_ninja_values + own_values
other_values = expand_urls(other_values)
ht = HeaderTests(label, header_name, alt_names, block_values, allow_values, partial_values, legacy_values, other_values)
ht.create_all_tests()


# In[48]:


label = "COEP"
header_name = "cross-origin-embedder-policy"
alt_names = ["x-cross-origin-embedder-policy"]
block_values = ["require-corp"]
allow_values = ["unsafe-none"]
partial_values = ["credentialless"]
legacy_values = []
# Always start with the empty value and then an INVALID value (e.g., "INVALID"), after that both valid and invalid values can be added
# We use the first two in `mult_headers_test`
basic_values = ["", "INVALID", "null", "*", URL_REP]
# https://wpt.fyi/results/html/cross-origin-embedder-policy?label=master&label=experimental&aligned&q=cross-origin-embedder-policy
wpt_values =   ['jibberish', 'require%FFcorp', 'require-corp;', '\u000brequire-corp\u000b', '\u000crequire-corp\u000c', '\u000drequire-corp\u000d', 'Require-corp', '"require-corp"', ':cmVxdWlyZS1jb3Jw:', 'require-corp;\tfoo=bar', 'require-corp require-corp', 'require-corp,require-corp', 'require-corp', ' require-corp ', '\trequire-corp\t', ' \trequire-corp', 'require-corp\t ', 'require-corp; foo=bar', 'require-corp;require-corp', 'require-corp; report-to="data:']
# https://github.com/hen95/HTTPHeaderBrowserTesting
siewert_values = [] # No COEP tested
# https://crawler.ninja/files
crawler_ninja_values = [] # No COEP tested
own_values = ["cross-origin", "same-origin"]
other_values = basic_values + wpt_values + siewert_values + crawler_ninja_values + own_values
other_values = expand_urls(other_values)
ht = HeaderTests(label, header_name, alt_names, block_values, allow_values, partial_values, legacy_values, other_values)
ht.create_all_tests()


# In[49]:


label = "COOP"
header_name = "cross-origin-opener-policy"
alt_names = ["x-cross-origin-opener-policy"]
block_values = []
allow_values = ["unsafe-none"]
partial_values = ["same-origin", "same-origin-allow-popups"]
legacy_values = []
# Always start with the empty value and then an INVALID value (e.g., "INVALID"), after that both valid and invalid values can be added
# We use the first two in `mult_headers_test`
basic_values = ["", "INVALID", "null", "*", URL_REP]
# https://wpt.fyi/results/html/cross-origin-opener-policy?label=master&label=experimental&aligned&q=cross-origin-opener-policy
wpt_values =   ["same-origin;", "\u000bsame-origin\u000b", "\u000csame-origin\u000c", "\u000dsame-origin\u000d", "Same-origin", "same-origin;\tfoo=bar", "same-origin ;foo=bar", "same-origin; foo=bar;", "\"same-origin\"", ":c2FtZS1vcmlnaW4=:", "?1", "1", "$same-origin",  "same-origin same-origin", "same-origin\\,same-origin", "*same-origin ", "same%FForigin", " same-origin", "same-origin ", "\tsame-origin", "same-origin\t", "same-origin;same-origin", "same-origin; foo=bar"]
# https://github.com/hen95/HTTPHeaderBrowserTesting
siewert_values = [] # No COOP tested
# https://crawler.ninja/files
crawler_ninja_values = [] # No COOP tested
own_values = ["cross-origin", "same-origin", "same-origin-plus-COEP"]
other_values = basic_values + wpt_values + siewert_values + crawler_ninja_values + own_values
other_values = expand_urls(other_values)
ht = HeaderTests(label, header_name, alt_names, block_values, allow_values, partial_values, legacy_values, other_values)
ht.create_all_tests()


# In[50]:


label = "CSP-SCRIPT"
header_name = "content-security-policy"
alt_names = ["x-content-security-policy", "x-webkit-csp", "x-webkit-content-security-policy"]
block_values = ["script-src 'none'"]
allow_values = ["script-src *"]
partial_values = ["script-src 'self'"]
legacy_values = []
# Always start with the empty value and then an INVALID value (e.g., "INVALID"), after that both valid and invalid values can be added
# We use the first two in `mult_headers_test`
basic_values = ["", "INVALID", "null", "*", URL_REP]
# https://wpt.fyi/results/content-security-policy?label=master&label=experimental&aligned&q=script-src
wpt_values = [] # Tests are more related to correct ordering and co and not parsing?
# https://github.com/hen95/HTTPHeaderBrowserTesting
siewert_values = [] # not tested
# https://crawler.ninja/files/csp-values.txt
crawler_ninja_values = []
# NOTE: maybe add crawler_ninja_values, Problem: Too many? Many are very similar and URL replacement results in a massive number of values
# crawler_ninja_values = get_crawler_values("https://crawler.ninja/files/csp-values.txt")
own_values = ["default-src 'none'", "self", "*", "script-src self", "script-src", "script-src none", "script-src none", "script-src 'null'", "script-src null", f"script-src-elem {URL_REP}", f"script-src-attr {URL_REP}"]
other_values = basic_values + wpt_values + siewert_values + crawler_ninja_values + own_values
other_values = expand_urls(other_values)
ht = HeaderTests(label, header_name, alt_names, block_values, allow_values, partial_values, legacy_values, other_values)
ht.create_all_tests()


# In[51]:


label = "CSP-IMG"
header_name = "content-security-policy"
alt_names = ["x-content-security-policy", "x-webkit-csp", "x-webkit-content-security-policy"]
block_values = ["img-src 'none'"]
allow_values = ["img-src *"]
partial_values = ["img-src 'self'"]
legacy_values = []
# Always start with the empty value and then an INVALID value (e.g., "INVALID"), after that both valid and invalid values can be added
# We use the first two in `mult_headers_test`
basic_values = ["", "INVALID", "null", "*", URL_REP]
# https://wpt.fyi/results/content-security-policy?label=master&label=experimental&aligned&q=img-src
wpt_values = ["img-src 'none'", "img-src 'self'", "img-src *", f"img-src {URL_REP}"]
# https://github.com/hen95/HTTPHeaderBrowserTesting
siewert_values = [] # Not tested
# https://crawler.ninja/files/csp-values.txt
crawler_ninja_values = []
# NOTE: maybe add crawler_ninja_values, Problem: Too many? Many are very similar and URL replacement results in a massive number of values
# crawler_ninja_values = get_crawler_values("https://crawler.ninja/files/csp-values.txt")
own_values = ["default-src 'none'", "self", "*", "img-src self", "img-src", "img-src none", "frame-src none", "img-src 'null'", "img-src null"]
other_values = basic_values + wpt_values + siewert_values + crawler_ninja_values + own_values
other_values = expand_urls(other_values)
ht = HeaderTests(label, header_name, alt_names, block_values, allow_values, partial_values, legacy_values, other_values)
ht.create_all_tests()


# In[55]:


label = "HSTS"
header_name = "strict-transport-security"
alt_names = ["x-strict-transport-security", "hsts"]
block_values = ["max-age=0"]
allow_values = []
partial_values = ["max-age=60", "max-age=20; includeSubDomains"]
legacy_values = []
# Always start with the empty value and then an INVALID value (e.g., "INVALID"), after that both valid and invalid values can be added
# We use the first two in `mult_headers_test`
basic_values = ["", "INVALID", "null", "*", URL_REP]
# Not in WPT
wpt_values = []
# https://github.com/hen95/HTTPHeaderBrowserTesting
#siewert_values = get_values("https://raw.githubusercontent.com/hen95/HTTPHeaderBrowserTesting/main/transform_to_testcase.py", r"\'Strict-Transport-Security: (.*?)\'")
siewert_values = ['max-age=60; max-age=120', 'max-age=60; someDirective, max-age=60; someDirective', 'max-age=60; preload', 'max-age=0, max-age=60', 'max-age=60, max-age=60; max-age=60; includeSubdomains', 'max-age=60; includeSubDomains', 'random, includeSubdomains; max-age=60; includeSubdomains', 'max-age=60; max-age=0', 'max-age=60, max-age=120', 'max-age=60, max-age=60', 'max-age=60; max-age=60, includeSubdomains', 'max-age=60, includeSubdomains; max-age=60; includeSubdomains', 'includeSubDomains', 'max-age=60; max-age=60', 'max-age=60,; includeSubdomains', 'max-age=60; preload; preload', 'max-age=60', 'max-age=0', 'max-age=60; includeSubDomains; preload', 'max-age=60, x; max-age=60; includeSubdomains', 'max-age=60; includeSubdomains; max-age=60, includeSubdomains', 'max-age=60; includeSubDomains, max-age=60; includeSubDomains', 'max-age=60, includeSubdomains', 'max-age=60; someDirective; someDirective', 'max-age=60, max-age=0', 'max-age=0; max-age=60', 'max-age=120', 'max-age=60; includeSubDomains; includeSubDomains', 'preload', 'max-age=60; preload, max-age=60; preload', 'x, max-age=60; max-age=60; includeSubdomains', 'max-age=60; includeSubdomains, max-age=60', 'max-age=60; ,']
# https://crawler.ninja/files/sts-values.txt
#crawler_ninja_values = get_crawler_values("https://crawler.ninja/files/sts-values.txt")
crawler_ninja_values = get_crawler_values("cached_crawler-ninja_values/sts-values.txt")
own_values = ["includeSubDomains", "max-age=-5", "max-age=60; includeSubDomains; preload"]
other_values = basic_values + wpt_values + siewert_values + crawler_ninja_values + own_values
other_values = expand_urls(other_values)
ht = HeaderTests(label, header_name, alt_names, block_values, allow_values, partial_values, legacy_values, other_values)
ht.create_all_tests()


# In[57]:


label = "PP"
header_name = "permissions-policy"
alt_names = ["x-permissions-policy", "feature-policy"]
block_values = ["fullscreen=()"]
allow_values = ["fullscreen=(*)"]
partial_values = ["fullscreen=(self)"]
legacy_values = []
# Always start with the empty value and then an INVALID value (e.g., "INVALID"), after that both valid and invalid values can be added
# We use the first two in `mult_headers_test`
basic_values = ["", "INVALID", "null", "*", URL_REP]
# https://wpt.fyi/results/permissions-policy/reporting?label=master&label=experimental&aligned&q=fullscreen
wpt_values = [] # Nothing useful?
# https://github.com/hen95/HTTPHeaderBrowserTesting
siewert_values = [] # Not tested
# https://crawler.ninja/files/fp-values.txt, https://crawler.ninja/files/pp-values.txt
#crawler_ninja_values = get_crawler_values("https://crawler.ninja/files/fp-values.txt", min_count=4) + get_crawler_values("https://crawler.ninja/files/pp-values.txt", min_count=4)
crawler_ninja_values = get_crawler_values("cached_crawler-ninja_values/fp-values.txt", min_count=4) + get_crawler_values("cached_crawler-ninja_values/pp-values.txt", min_count=4)
own_values = ["fullscreen=", "fullscreen=*", "fullscreen=()", "fullscreen=(self)", f"fullscreen=({URL_REP})", "fullscreen=(self none)", "fullscreen=(self,none)", "fullscreen=(src)"]
other_values = basic_values + wpt_values + siewert_values + crawler_ninja_values + own_values
other_values = expand_urls(other_values)
ht = HeaderTests(label, header_name, alt_names, block_values, allow_values, partial_values, legacy_values, other_values)
ht.create_all_tests()


# In[58]:


label = "RP"
header_name = "referrer-policy"
alt_names = ["x-referrer-policy", "referer-policy"]
block_values = ["no-referrer"]
allow_values = ["unsafe-url"]
partial_values = ["same-origin"]
legacy_values = []
# Always start with the empty value and then an INVALID value (e.g., "INVALID"), after that both valid and invalid values can be added
# We use the first two in `mult_headers_test`
basic_values = ["", "INVALID", "null", "*", URL_REP]
# https://wpt.fyi/results/referrer-policy?label=master&label=experimental&aligned&q=referrer-policy
wpt_values = [] # Too many?
# https://github.com/hen95/HTTPHeaderBrowserTesting
siewert_values = [] # Not tested
# https://crawler.ninja/files/rp-values.txt
#crawler_ninja_values = get_crawler_values("https://crawler.ninja/files/rp-values.txt")
crawler_ninja_values = get_crawler_values("cached_crawler-ninja_values/rp-values.txt")

own_values = ["no-referrer-when-downgrade", "origin", "strict-origin", "origin-when-cross-origin", "strict-origin-when-cross-origin"]
other_values = basic_values + wpt_values + siewert_values + crawler_ninja_values + own_values
other_values = expand_urls(other_values)
ht = HeaderTests(label, header_name, alt_names, block_values, allow_values, partial_values, legacy_values, other_values)
ht.create_all_tests()


# In[59]:


label = "TAO"
header_name = "timing-allow-origin"
alt_names = ["x-timing-allow-origin"]
block_values = ["null"]
allow_values = ["*"]
partial_values = []
legacy_values = []
# Always start with the empty value and then an INVALID value (e.g., "INVALID"), after that both valid and invalid values can be added
# We use the first two in `mult_headers_test`
basic_values = ["", "INVALID", "null", "*", URL_REP]
# https://wpt.fyi/results/resource-timing?label=master&label=experimental&aligned&q=tao
wpt_values = [] # Nothing crazy?
# https://github.com/hen95/HTTPHeaderBrowserTesting
siewert_values = [] # Not tested
crawler_ninja_values = [] # Not tested
own_values = ["self", "'self'", f"{URL_REP} {URL_REP}", f"{URL_REP},{URL_REP}"]
other_values = basic_values + wpt_values + siewert_values + crawler_ninja_values + own_values
other_values = expand_urls(other_values)
ht = HeaderTests(label, header_name, alt_names, block_values, allow_values, partial_values, legacy_values, other_values)
ht.create_all_tests()


# In[61]:


label = "XCTO"
header_name = "x-content-type-options"
alt_names = ["content-type-options"]
block_values = ["nosniff"]
allow_values = []
partial_values = []
legacy_values = []
# Always start with the empty value and then an INVALID value (e.g., "INVALID"), after that both valid and invalid values can be added
# We use the first two in `mult_headers_test`
basic_values = ["", "INVALID", "nosniff", "no-sniff"]
# https://github.com/web-platform-tests/wpt/blob/master/fetch/nosniff/resources/x-content-type-options.json
wpt_values = ["NOSNIFF", "nosniff,,@#$#%%&^&^*()()11!", "@#$#%%&^&^*()()11!,nosniff", "no", "", ",nosniff", "nosniff\u000C", "nosniff\u000B,nosniff", "'NosniFF'", '"nosniFF"'] 
# https://github.com/hen95/HTTPHeaderBrowserTesting
siewert_values = [] # Not tested
#crawler_ninja_values = get_crawler_values("https://crawler.ninja/files/xcto-values.txt")
crawler_ninja_values = get_crawler_values("cached_crawler-ninja_values/xcto-values.txt")

own_values = ["SNIFF", "no", "always", "maybe"]
other_values = basic_values + wpt_values + siewert_values + crawler_ninja_values + own_values
other_values = expand_urls(other_values)
ht = HeaderTests(label, header_name, alt_names, block_values, allow_values, partial_values, legacy_values, other_values)
ht.create_all_tests()


# In[60]:


label = "CSPvsXFO"
header_names = ["content-security-policy", "x-frame-options"]
values = {
    "content-security-policy": csp_fa_all,
    "x-frame-options": ["DENY", "", "INVALID", "SAMEORIGIN"]
}
ht = HeaderTestsMultHeader(header_names, values, label)
ht.create_all_tests()

