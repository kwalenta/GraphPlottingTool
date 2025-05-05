import os
import sqlite3
import pandas as pd
import helper_functions as h  

def get_data(obj) -> None:
    """
    Loads data from a SQLite database and processes it for further use.
    Parameters:
    obj : object
        An object containing the necessary attributes for data loading and processing.
        The object must have the following attributes:
        - input_type (str): Specifies the type of input. Must be "sqlite" for this function.
        - input_dir (str): The directory path where the SQLite database file is located.
        - tables (list): A list of table names to be loaded from the database.
        - bounds (list): A list that will store the computed geographical bounds.
    Raises:
    FileNotFoundError:
        If the specified input directory does not exist.
        If the SQLite database file ("data.sqlite") does not exist in the input directory.
    Notes:
    - This function connects to the SQLite database, retrieves the specified tables, 
      and loads them into the object as attributes.
    - The node ID column in the DataFrame `i` is set as the index.
    - Geographical bounds are computed based on latitude (`lat`) and longitude (`lon`) columns 
      in the DataFrame `i`.
    Dependencies:
    - Requires the `os`, `sqlite3`, and a helper module `h` with a function 
      `extract_table_to_dataframe` for extracting tables into DataFrames.
    """
 
    self = obj
    if self.input_type == "sqlite":
        # check if the relative path exists
        if not os.path.exists(self.input_dir):
            raise FileNotFoundError(f"Input directory {self.input_dir} does not exist.")
        # check if the file exists
        if not os.path.exists(os.path.join(self.input_dir, "data.sqlite")):
            raise FileNotFoundError(f"File {os.path.join(self.input_dir, 'data.sqlite')} does not exist.")
        
        # connect to the database
        conn = sqlite3.connect(os.path.join(self.input_dir, "data.sqlite"))
        # print out all tables in the database
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

        for table in self.tables:
            # load the data as variable with the table name
            setattr(self, table, h.extract_table_to_dataframe(conn, table))

    # set node id as index
    self.i.set_index('values', inplace=True)
    # set node id as index    

    # Compute bounds for map display
    self.bounds = [
        [min(self.i['lat']), min(self.i['lon'])],
        [max(self.i['lat']), max(self.i['lon'])]
    ]

    # close the connection
    conn.close()
    return None
