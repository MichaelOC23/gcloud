
import psycopg2
import csv
import pandas as pd
import urllib.parse as up
import os

database_to_use = os.environ["ELEPHANTSQL_DB_URL"]

#!Function to connect to the specified database
def get_connection_to_db():
    try: 
        up.uses_netloc.append("postgres")
        url = up.urlparse(database_to_use)

        conn = psycopg2.connect(database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
        )

    except psycopg2.Error as e:
        print("Cannot connect to database. Error below:")
        print(e)
        exit()

    return conn

#!Function to properly escape special characters in postgresql
def escape_postgres_params(params):
  
    escaped_params = []
  
    for param in params:
        if isinstance(param, str):
            new_param = param.replace('#', '##')
            new_param = new_param.replace('\\', '\\\\')
            new_param = new_param.replace('\'', '\'\'')
            escaped_params.append(new_param)
        else:
            escaped_params.append(param)

    return tuple(escaped_params)

#!Supporting Function that gets the header row from a CSV file
def get_CSV_header_row(file_path):

  # Read the first row and extract column names
  with open(file_path, newline='') as csvfile:
      reader = csv.reader(csvfile)
      column_names = next(reader)  # Gets the first row (column names)

  return column_names

#?###############################################
#?#    DATABASE INTERACTION FUNCTIONS    ########
#?###############################################

#!Function to load data from a CSV file using the COPY command (CURRENTLY IN USE)
def loadTableDataFromCSV(tableName, csvFilePath):
    columns = get_CSV_header_row(csvFilePath)
    columns = ", ".join(columns)
    
    # SQL command for COPY
    sql = f"""
    COPY {tableName}({columns}) FROM STDIN WITH CSV HEADER DELIMITER AS ','
    """
    
    conn = get_connection_to_db()
    cur = conn.cursor()

    try:
        # Execute COPY command
        with open(csvFilePath, 'r') as f:
            cur.copy_expert(sql, f)
      
      # Commit the transaction
        conn.commit()
        conn.close()

    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        conn.rollback()

#!Function to insert data into any table
def insert_data(tablename, data):

    conn = get_connection_to_db()
    cursor = conn.cursor()

    columns = list(data.keys())
    placeholders = ", ".join(["%s"] * len(columns))

    insert_query = f"""
    INSERT INTO {tablename} ({", ".join(columns)})
    VALUES ({placeholders})
    """

    escaped_data = escape_postgres_params(data.values())
    
    #print(data)
    cursor.execute(insert_query, escaped_data)
    conn.commit()
    conn.close()
    return True

#! Function to DELETE ALL TABLES in the current database
def DELETE_ALL_TABLES():
    try:
        #Connect
        conn = get_connection_to_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        tables = cursor.fetchall()

        # Build list of table names
        table_names = [table[0] for table in tables]

        # Remove system tables
        table_names = [name for name in table_names if not 'pg_' in name and not 'sql_' in name]

        # Generate DROP statements
        drop_queries = [f'DROP TABLE IF EXISTS {name} CASCADE;' for name in table_names]
    
        # Execute DROP queries
        for query in drop_queries:
            print(query)
            cursor.execute(query)
        
        conn.commit()
        conn.close()

        return True
    
    except psycopg2.Error as e:
        print(e)
        return False
    # Get all table names 

#! Function to execute a SQL Command (not for SELECT statements)
def execute_sql(sql):
    try:
        #Connect
        conn = get_connection_to_db()
        cursor = conn.cursor()
        
        #Execute the SQL 
        cursor.execute(sql)
        
        if sql[:6] == "SELECT":

            #Fetch all results
            rows = cursor.fetchall()
            # print(len(rows))
            
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(rows, columns=columns)

            conn.close()
            return df
        else:
           
            conn.commit()
            conn.close()
        
            return True
    
    except psycopg2.Error as e:
        print(f'Error Running SQL Command: {sql}')
        print(e)
        return False

#! Function to get a dataframe from a SQL Select Statement
def getDISTINCTValue(fieldname, tablename):
    try:
        conn = get_connection_to_db()
        cursor = conn.cursor()
        
        sqlCommand = f"SELECT DISTINCT {fieldname} FROM {tablename}"
        
        cursor.execute(sqlCommand)
        
        # Fetch all results
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)

        conn.close()
        return df
    
    except psycopg2.Error as e:
        print(e)
        return False
    



