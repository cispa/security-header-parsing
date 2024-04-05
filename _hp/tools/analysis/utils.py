import os
import psycopg2
import pandas as pd
from dataclasses import dataclass
from functools import lru_cache, partial
import re


@dataclass
class Config:
    DB_HOST: str="134.96.225.205"
    DB_NAME: str="http_header"
    DB_USER: str="http_header"
    DB_PASSWORD: str="bde50f42d5851a9eb6bf4166e737cb1c"
    DB_PORT: str="5432"

def get_data(config: Config, select_query: str, quiet=False) -> pd.DataFrame:
    param_dict = {
        "host": config.DB_HOST,
        "database": config.DB_NAME,
        "user": config.DB_USER,
        "password": config.DB_PASSWORD,
        "port": config.DB_PORT
    }
    df = None
    conn = connect(param_dict, quiet=quiet)
    df = postgresql_to_dataframe(conn, select_query=select_query)
    conn.close()
    return df

def connect(param_dict=None, quiet=False):
    """ Connect to the PostgreSQL database server """
    conn = None
    if param_dict is None:
        param_dict = {
            "host"      : os.getenv("DB_HOST"),
            "database"  : os.getenv("DB_NAME"),
            "user"      : os.getenv("DB_USER"),
            "password"  : os.getenv("DB_PASSWORD"),
            "port": os.getenv("DB_PORT"),
        }
    try:
        # connect to the PostgreSQL server
        if not quiet:
            print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**param_dict)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    if not quiet:
        print("Connection successful")
    return conn


def postgresql_to_dataframe(conn, select_query, non_cat=None):
    """
    Tranform a SELECT query into a pandas dataframe
    """
    if non_cat is None:
        non_cat = []
    cursor = conn.cursor()
    try:
        cursor.execute(select_query)
        column_names = [desc[0] for desc in cursor.description]
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        cursor.close()
        return 1
    
    # Naturally we get a list of tuples
    tuples = cursor.fetchall()
    cursor.close()
    
    # We just need to turn it into a pandas dataframe
    df = pd.DataFrame(tuples, columns=column_names)
    
    # Convert all string (object) columns to categorical to speed things up
    # df[df.select_dtypes(['object']).columns] = df.select_dtypes(['object']).apply(to_cat, non_cat=non_cat)
    
    return df

def to_cat(column, non_cat=[]):
    """Change all columns that are not in the non_cat list to type category."""
    if column.name in non_cat:
        return column
    else:
        return column.astype('category')


def clean_url(url):
    # Set browser_id=1 (unknown) to not accidentally include them in our real data collection
    url = re.sub(r"browser_id=(\d+)", "browser_id=1", url)
    url = re.sub(r"&first_popup=(\d+)&last_popup=(\d+)&run_no_popup=(yes|no)", "", url)
    url = re.sub(r"&run_id=(\w+)", "", url)
    url = re.sub(r"timeout=(\d+)&", "", url)
    return url

def make_clickable(url):
    # Clickable links for debugging
    url = clean_url(url)
    return clickable(url, url)

def clickable(title=None, url=None):
    if not title:
        title = url
    return f'<a href="{url}" target="_blank">{title}</a>'




def add_columns(df):
    # Create extra columns
    df["outcome_str"] = df["outcome_value"].fillna("None").astype(str)
    df["clean_url"] = df["full_url"].apply(clean_url)
    @lru_cache(maxsize=None)
    def id_to_browser(id):
        """Full browser name (os+version) from the ID"""
        return " ".join(df.loc[df["browser_id"] == id].iloc[0][["name", "os", "version", "automation_mode", "headless_mode"]].to_list())
    df["browser"] = df["browser_id"].apply(id_to_browser)
    df["org_origin"] = df["org_scheme"] + "://" + df["org_host"]
    df["resp_origin"] = df["resp_scheme"] + "://" + df["resp_host"]
    
    # Unify outcomes that are semantically the same (only the exact error string is different in different browsers)
    
    # Fetch fails:
    # Firefox: {'error': 'object "TypeError: NetworkError when attempting to fetch resource."', 'headers': ''}
    # Chromium: {'error': 'object "TypeError: Failed to fetch"', 'headers': ''}
    # Safari: {'error': 'object "TypeError: Load failed"', 'headers': ''}
    df["outcome_str"] = df["outcome_str"].replace("TypeError: Load failed", "TypeError: Failed to fetch", regex=True)
    df["outcome_str"] = df["outcome_str"].replace("TypeError: NetworkError when attempting to fetch resource.", "TypeError: Failed to fetch", regex=True)
    
    # Fetch is aborted:
    # Firefox: AbortError: The operation was aborted.<space>
    # Safari: AbortError: Fetch is aborted
    # Chromium (mobile): AbortError: The user aborted a request.
    df["outcome_str"] = df["outcome_str"].replace(r"AbortError: The operation was aborted\. ?", "AbortError: Fetch is aborted", regex=True)
    df["outcome_str"] = df["outcome_str"].replace("AbortError: The user aborted a request.", "AbortError: Fetch is aborted", regex=True)

    # Popup not-opened/window reference is null:
    # Chromium: {'window.open.opener': 'object "TypeError: Cannot read properties of null (reading \'opener\')"'}
    # Firefox: {'window.open.opener': 'object "TypeError: w is null"'}
    df["outcome_str"] = df["outcome_str"].replace("TypeError: w is null", "No window-reference. Probably popup blocked", regex=True)
    df["outcome_str"] = df["outcome_str"].replace("TypeError: Cannot read properties of null (reading \'opener\')", "No window-reference. Probably popup blocked", regex=True)

    

    
    # For document referrer we do not want to know the exact resp_id and count
    # We only want to know whether it is a origin or the full URl?
    #df['outcome_str'] = df['outcome_str'].replace(r'resp_id=\d+', 'resp_id=<resp_id>', regex=True)
    #df['outcome_str'] = df['outcome_str'].replace(r'count=\d+', 'count=<count>', regex=True)
    df['outcome_str'] = df['outcome_str'].apply(lambda x: 'document.referrer: full_url' if 'responses.py?feature_group' in x else x)
    # The differences always only are between http-origin, https-origin, full-url, none, timeout; there is never a difference between the various origins, thus we can merge them to make our live easier
    df["outcome_str"] = df["outcome_str"].apply(lambda x: "document.referrer: https://origin" if "https://" in x else x)
    df["outcome_str"] = df["outcome_str"].apply(lambda x: "document.referrer: http://origin" if "http://" in x else x)
    return df