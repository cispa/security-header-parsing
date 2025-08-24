import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
import json

from datetime import datetime

from utils import get_data, Config, clean_url, make_clickable, add_columns

initial_data = """
SELECT "Result".*, 
"Response".raw_header, "Response".status_code, "Response".label, "Response".resp_type,
"Browser".name, "Browser".version, "Browser".headless_mode, "Browser".os, "Browser".automation_mode, "Browser".add_info
FROM "Result"
JOIN "Response" ON "Result".response_id = "Response".id JOIN "Browser" ON "Result".browser_id = "Browser".id;
"""
df = get_data(Config(), initial_data)
df = add_columns(df)

print(f"Collected {len(df)} results:")

print(df.groupby(['browser'])['test_name'].value_counts())

print(f"Example row:\n {df.iloc[-1]}")