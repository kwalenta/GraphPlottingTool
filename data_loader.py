import os
import sqlite3
import pandas as pd
import helper_functions as h  

def get_data(obj, ):
    """
    
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

