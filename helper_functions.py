import pandas as pd
import os
import yaml
import time
import sqlite3


def extract_table_to_dataframe(con: sqlite3.Connection, table_name: str) -> pd.DataFrame:
    """
    Extracts the contents of a database table into a pandas DataFrame.
    Args:
        con (sqlite3.Connection): 
            The database connection object.
        table_name (str): 
            The name of the table to extract data from.
    Returns:
        pandas.DataFrame: 
            A DataFrame containing the data from the specified table, 
            or None if an error occurs.
    Raises:
        Exception: 
            If there is an issue with the database query or connection, 
            an exception is caught and an error message is printed.
    """
    try:
        # Query the table
        query = f"SELECT * FROM {table_name};"
        df = pd.read_sql(query, con)
        print(f"Extracted table {table_name} with {len(df)} rows and {len(df.columns)} columns.")
        
        return df
    
    except Exception as e:
        print(f"Error extracting table {table_name}: {e}")
        return None

def copy_default_config(config_path: str="config.yml", default_config_path: str="config_template.yml") -> None:
    """
    Copies a default configuration file to a specified path if it does not already exist.
    Args:
        config_path (str): The path where the configuration file should be created. 
                           Defaults to "config.yml".
        default_config_path (str): The path to the default configuration template file. 
                                   Defaults to "config_template.yml".
    Behavior:
        - If the file at `config_path` does not exist, the function reads the content of 
          `default_config_path` and writes it to `config_path`.
        - If the file at `config_path` already exists, no action is taken, and a message 
          is printed to indicate this.
    Prints:
        - A message indicating that the default configuration has been copied, or that 
          the configuration file already exists.
    """
    if not os.path.exists(config_path):
        with open(default_config_path, 'r') as f:
            config = f.read()
        with open(config_path, 'w') as f:
            f.write(config)
        print(f"Copied default configuration to {config_path}. Enter path settings in the file, then rerun.")
        
    else:
        print(f"Configuration file already exists at {config_path}.")

def load_config(config_path: str="config.yml") -> dict:
    """
    Loads a YAML configuration file and returns its contents as a dictionary.

    Args:
        config_path (str): The path to the YAML configuration file. 
                           Defaults to "config.yml".

    Returns:
        dict: The contents of the YAML configuration file as a dictionary.

    Raises:
        FileNotFoundError: If the specified configuration file does not exist.
        yaml.YAMLError: If there is an error parsing the YAML file.
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

