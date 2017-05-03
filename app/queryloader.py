"""
Load a SQL query from a file
"""

import os

def query_loader(path):

    # Normalise the path

    path = os.path.abspath(path)
        
    #open the .sql file
    sql_file = open(path,'r')

    # Create an empty command string
    sql_command = ''

    # Iterate over all lines in the sql file
    for line in sql_file:
        # Ignore comented lines
        if not line.startswith('--') and line.strip('\n'):
            # Append line to the command string
            sql_command += line.strip('\n')

    return sql_command
