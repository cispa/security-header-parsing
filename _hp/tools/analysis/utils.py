import os
import psycopg2
import pandas as pd
from dataclasses import dataclass

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
