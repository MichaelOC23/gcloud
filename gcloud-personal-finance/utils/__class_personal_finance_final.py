

import os, sys, csv, json, chardet, re, time, uuid
from pathlib import Path

from decimal import Decimal
import psycopg2
import pandas as pd
import urllib.parse as up
from supabase import create_client, Client

def get_column_name_dict():
    return  { 'Date': 'TransactionDate', 'Account Type': 'AccountType', 'Account Name': 'AccountName', 'Account Number': 'AccountNumber', 'Institution Name': 'InstitutionName', 'Name': 'TransactionName', 'Description':  'TranName', 'Amount': 'Amount', 'Category': 'CategoryOld', 'Note': 'Note', 'Ignored From': 'Ignore', 'Tax Deductible': 'TaxDeductible', 'Reference': 'InstitutionTransactionId', 'Card Member': 'AccountName', 'Account #': 'AccountNumber', 'Address': 'MerchantStreetAddress', 'City/State': 'MerchantCity', 'Zip Code': 'MerchantZip', 'Country': 'MerchantCountry', 'Appears On Your Statement As': 'TransactionDescription', 'Transaction Date': 'TransactionDate', 'Purchased By': 'AccountName', 'Merchant': 'MerchantName', 'Amount (USD)': 'Amount', 'Extended Details': 'Note', 'Trade Date': 'TransactionDate', 'Tran Code Description': 'TransactionDescription', 'Amount USD': 'Amount', 'Type': 'TransactionType', 'Check Number': 'CheckNumber'}

class personal_finance():
    def __init__(self):
        pass


class postgres_sql_utils():
    def __init__(self, path_to_folder_of_csvs=None, schema='postgres', table_prefix='t_', column_prefix='c_'):
        
        # self.connection_str = os.environ["SUPABASE_HORIZON_POSTGRES_DB_CONNECTION_STRING"]
        # self.database_to_use = os.environ["SUPABASE_HORIZON_POSTGRES_DB_CONNECTION_STRING"]
        

        # Replace with your Supabase project URL and API key
        self.url = "https://kioveujteqsynueojotj.supabase.co"
        self.key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imtpb3ZldWp0ZXFzeW51ZW9qb3RqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mjk4ODY0NTcsImV4cCI6MjA0NTQ2MjQ1N30.PIbqA1DIJ9GMLCAdcFV-rSo5gc8AkbDubxFH_jF9gP0"
        self.supabase = Client = create_client(self.url, self.key)
        
        if not path_to_folder_of_csvs:
            path_to_folder_of_csvs = sys.argv[1] if len(sys.argv) > 1 else  f"{os.getcwd()}/transaction-files"
        self.folder_path = path_to_folder_of_csvs
        self.dataframe_list = []
        self.force_repickling = True
        self.schema = schema
        self.table_prefix = table_prefix
        self.column_prefix = column_prefix
        self.dataframe_analysis = None
        self.csv_file_market_length = 25
        
    def clean_column_names(self, columns):
        # Clean column names to comply with PostgreSQL conventions
        return [re.sub(r'\W+', '_', col.lower()) for col in columns]
        
    def get_csv_column_title_file_marker(self, file_path):
        """Returns the first 50 characters of the first row (column titles) of a CSV file."""
        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                header = next(reader)  # Get the first row (column titles)
                header_str = ','.join(header)  # Convert list of titles to a single string
                marker =  header_str[:self.csv_file_market_length]  # Return first characters
                print(f"{marker} | {file_path}")
                return marker
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def generate_create_table_query(self, df, table_name, schema=None ):
        
        self._create_schema( schema)
        
        if not schema:
            schema = self.schema
        # Clean up the dataframe column names
        cleaned_columns = self.clean_column_names(df.columns)
        df.columns = cleaned_columns

        # Start building the create table query
        create_query = f'CREATE TABLE IF NOT EXISTS {schema}.{table_name} ('
        
        # Add the GUID primary key
        # create_query += 'id serial4 NOT NULL, '
        create_query += ''

        # Add columns based on DataFrame dtypes
        for col in df.columns:
            dtype = df[col].dtype
            if dtype == 'O':
                create_query += f'{col} TEXT, '
            elif dtype == 'float64' or dtype == 'int64' or isinstance(df[col].iloc[0], Decimal):
                create_query += f'{col} DECIMAL, '
            elif dtype == 'datetime64[ns]':
                create_query += f'{col} TEXT, '  # Treat dates as strings

        # Remove trailing comma and space
        create_query = create_query.rstrip(', ') + ');'

        return create_query
    
    def load_folder_of_csvs_to_one_table(self, table_name, folder_path):
        results = []
        if folder_path and  len(folder_path) > 0:
            self.folder_path = folder_path
            
        for file in os.listdir(self.folder_path):
            if file.endswith('.csv'):
                csv_path = os.path.join(self.folder_path, file)
                self.get_csv_column_title_file_marker(csv_path)
                #     
                #     result = self.load_csv_to_postgres(csv_file_path=csv_path,  table_name=table_name)
                #     results.append(result)
                # # except:
                #     print('Error loading CSV file: ', file)
                #     pass
        

        

        # Returning all results
        return results
    
    def create_table_name_from_csv_file_name(self, csv_path, table_name=None):
        table_name = os.path.basename(csv_path).split('.')[0]
        table_name = table_name.replace(' ', '')   # Replace spaces with blanks
        table_name = table_name.replace('-', '')   # Replace dashes with blanks
        table_name = table_name.replace('_', '')   # Replace unerscores with blanks
        
        return table_name
    
    def load_csv_to_postgres(self, csv_file_path, table_name):

        csv_folder_path = os.path.dirname(csv_file_path)
        csv_file_name = os.path.basename(csv_file_path)
        clean_csv_export_path = os.path.join(csv_folder_path, 'clean', csv_file_name)
        clean_csv_folder = os.path.join(csv_folder_path, 'clean')
        if not os.path.exists(clean_csv_folder):
            os.makedirs(clean_csv_folder)
        
        
        encoding =  self.detect_encoding(csv_file_path)
        
        df = self.get_csv_as_dataframe(csv_file_path, encoding)
        df.rename(columns=get_column_name_dict(), inplace=True)
        
        
        self.insert_data('transaction', df)
        
        
        if df is None or df.empty:
            print(f'The DataFrame for {table_name} is empty or not properly loaded.')
            print (f"The CSV does not exist at {clean_csv_export_path} or file is empty. Aborting load for this file.")
            return [False, csv_file_name]

        
        return {table_name: True, "csv": csv_file_path}

    def detect_encoding(self, file_path):
        with open(file_path, 'rb') as f:
            result = chardet.detect(f.read())
            return result['encoding']

    def get_csv_as_dataframe(self, csv_path, encoding=None):
        def inspect_and_cast( df, max_rows=50):
            def is_date_or_empty(val):
                if pd.isnull(val):
                    return True
                val_str = str(val).strip()
                if val_str == '':
                    return True
                try:
                    pd.to_datetime(val_str)
                    return True
                except (ValueError, TypeError):
                    return False
            def is_numeric_or_empty(s):
                try:
                    s_float = pd.to_numeric(s, errors='coerce')
                    return s_float.notna() | s.isna()
                except ValueError:
                    return False
            def optimize_dataframe(df, max_rows):
                for col in df.columns:
                    sample = df[col].iloc[:max_rows]
                    if is_numeric_or_empty(sample).all():
                        df[col] = df[col].replace(r'^\s*$', '0', regex=True)
                        df[col] = df[col].fillna('0')
                        try:
                            df[col] = df[col].astype(float)
                        except ValueError:
                            continue
                return df
            df = optimize_dataframe(df, max_rows)
            for col in df.columns:
                if df[col].apply(is_date_or_empty).all():
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            df = df.fillna('')  
            return df
        
        dtype_path = csv_path.replace('.csv', '_dtype.json')
        pickle_path = csv_path.replace('.csv', '.pkl')

        # If a pickle file exists, load from it
        if os.path.exists(pickle_path):
            df = pd.read_pickle(pickle_path)
            print(f"\033[1;96mLoaded {csv_path} from pickle.\033[0m")
            return df

        # Otherwise, load the CSV
        start_time = time.time()
        if os.path.exists(dtype_path):
            with open(dtype_path, 'r') as dtype_file:
                dtype_dict = json.load(dtype_file)
            df = pd.read_csv(csv_path, dtype=dtype_dict)
            print(f"\033[1;96mLoaded {csv_path} with specified dtypes from CSV.\033[0m")
        else:
            # CSV Will be processed as new
            if not encoding:
                encoding = self.detect_encoding(csv_path)
            with open(csv_path, encoding=encoding) as f:
                
                # Read , lower case and remove spaces from header
                header = f.readline().strip().split(',')
                clean_header = [col.strip().replace(' ', '_').lower() for col in header]

                # Load the rest of the file into a DataFrame using the cleaned header
                df = pd.read_csv(f, names=clean_header, dtype=str)
                
            # Drop rows where all elements are NaN
            df = df.dropna(how='all')
            
            # Remove \n from all fields in the DataFrame
            df = df.apply(lambda col: col.apply(lambda x: x.replace('\n', ' ').replace('\r', ' ') if isinstance(x, str) else x))
            
            # Reset the index after dropping rows
            df = df.reset_index(drop=True)
            
            # Cast the DataFrame Columns as their appropriate types
            df = inspect_and_cast(df, 50)
            
            # Save dtypes
            dtype_dict = df.dtypes.apply(lambda x: x.name).to_dict()
            with open(dtype_path, 'w') as dtype_file:
                json.dump(dtype_dict, dtype_file)
            print(f"\033[1;96mSaved dtypes for {csv_path}.\033[0m")

        # Save the processed DataFrame as a pickle
        df.to_pickle(pickle_path)
        print(f"\033[1;96mSaved {csv_path} as pickle.\033[0m")
        print(f"\033[1;96mTime to process {csv_path}: {time.time() - start_time}\033[0m")
        return df
    
    #!Supporting Function that gets the header row from a CSV file
    def get_CSV_header_row(self, file_path):

        # Read the first row and extract column names
        with open(file_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            column_names = next(reader)  # Gets the first row (column names)

        return column_names

    #! Function to execute a SQL Command (not for SELECT statements)
    def insert_data(self,table_name, data):
        
        try:
            self.url = "https://kioveujteqsynueojotj.supabase.co"
            self.key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imtpb3ZldWp0ZXFzeW51ZW9qb3RqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mjk4ODY0NTcsImV4cCI6MjA0NTQ2MjQ1N30.PIbqA1DIJ9GMLCAdcFV-rSo5gc8AkbDubxFH_jF9gP0"
            supabase = Client = create_client(self.url, self.key)
            
            if isinstance(data, pd.DataFrame):
                timestamp_columns = [col for col in data.columns if pd.api.types.is_datetime64_any_dtype(data[col])]
                for col in timestamp_columns:
                    data[col] = pd.to_datetime(data[col]).dt.date.astype(str)  # Converts to date only (YYYY-MM-DD)
                data_list_of_dicts = data.to_dict(orient='records')
                
            if isinstance(data, dict):
                data_list_of_dicts = [data_list_of_dicts]
            
            if isinstance(data, list):
                data_list_of_dicts = []
                for item in data:
                    if isinstance(item, dict):
                        data_list_of_dicts.append(item)
            
            response = supabase.table(table_name=table_name).insert(data_list_of_dicts).execute()
            
        except Exception as e:
               print(e)
        
    


class personal_finance_database():
    def __init__(self):
        self.models_file_path = "utils/models.json"

    def generate_model_for_database(self, model_name, database):
        # Read the model file
        with open(self.models_file_path) as json_file:
            models = json.load(json_file)

        entities = models['models'][model_name]['entities']
        field_types = models['databasedefinitions'][database]['fieldtypes']
        default_fields = models['databasedefinitions'][database]['defaultfields']
        
        create_table_statements = self.generate_create_table_statements(entities, field_types, default_fields)

        return create_table_statements
        
    def generate_create_table_statements(self, entities, field_types, default_fields):

        # Initialize an empty list to store CREATE TABLE statements
        create_table_statements = []

        # Iterate through each entity in the JSON input
        for entity_name, entity_info in entities.items():
            entity_attributes_list = entity_info['attributes']

            # Create a list to store the field definitions for the CREATE TABLE statement
            field_definitions = []

            # Add the default fields to the field definitions
            for key, value in default_fields.items():
                field_definitions.append(f"{key} {value}")

            # Iterate through the attributes of the entity and generate field definitions
            for attribute in entity_attributes_list:
                for attr_name, attr_value in attribute.items():
                    field_type = attr_value.get('type', 'TEXT')
                    field_definitions.append(f"{attr_name} {field_type}")

            # Create the CREATE TABLE statement for the entity
            create_table_sql = f"CREATE TABLE {entity_name} ({', '.join(field_definitions)});"

            # Add the statement to the list
            create_table_statements.append(create_table_sql.upper())

        return create_table_statements
    
    


if __name__ == '__main__':
    
    pfd = personal_finance_database()
    psql = postgres_sql_utils()
    # psql.execute_sql("")
    
    psql.load_folder_of_csvs_to_one_table('transaction', f"{Path.cwd()}/transaction-files")
    
    #! Create the table statements to generate the base tables
    # create_table_statements = pfd.generate_model_for_database( 'personal-finance', 'postgresql')
    # home_folder = Path.home()
    # with open (f'{home_folder}/supabase/migrations/20241026155049_create_initial_tables.sql', 'w') as f:
    #     for sql in create_table_statements:
    #         f.write(f"\n{sql}\n\n")
        

    
    
    
    
    
    # if table_name not in existing_tables or recreate_table:
    #         table_is_new = True
    #         create_table_query =  self.generate_create_table_query(df, table_name, schema=self.schema)
    #         with self.connect() as conn:
    #             conn.cursor().execute(f'DROP TABLE IF EXISTS {self.schema}.{table_name};')
    #             conn.commit()
    #             conn.cursor().execute(create_table_query)
    #             conn.commit()
        
    #     if table_is_new:
    #         primary_key_sql = f"ALTER TABLE {self.schema}.{table_name} ADD COLUMN id SERIAL4;"
        
    #         for col in list(df.columns):
    #             try:
    #                 if df[col].is_unique:
    #                     print(f"{col} in unique in table {table_name}. Assigning it as primary key instead of creating an id field.")
    #                     primary_key_sql = f"ALTER TABLE {self.schema}.{table_name} ADD PRIMARY KEY ({col});"
    #                     break
    #                 print(f'{table_name} loaded and assign pk of {col}')
    #             except KeyError:
    #                 pass
    #         with self.connect() as conn:
    #             print(f"\n{primary_key_sql}")
    #             conn.cursor().execute(primary_key_sql)
    #             conn.commit()
        
        
        
        
    # #!Function to insert data into any table
    # def insert_data(self, tablename, data):

    #     conn = self.get_connection_to_db()
    #     cursor = conn.cursor()

    #     columns = list(data.keys())
    #     placeholders = ", ".join(["%s"] * len(columns))

    #     insert_query = f"""
    #     INSERT INTO {tablename} ({", ".join(columns)})
    #     VALUES ({placeholders})
    #     """

    #     escaped_data = self.escape_postgres_params(data.values())
        
    #     #print(data)
    #     cursor.execute(insert_query, escaped_data)
    #     conn.commit()
    #     conn.close()
    #     return True




    # def execute_sql(self, sql):
    #     with self.connect() as conn:
    #         try:
    #             # conn.cursor()o create the schema
    #             conn.cursor().execute(sql)
    #             conn.commit()
    #         except Exception as e:
    #             # Log the error for debugging purposes (or handle it differently)
    #             print(f"Error executing sql statement:\n{sql}\n\nError:\n\n{e}")

    # #! Function to get a dataframe from a SQL Select Statement
    # def getDISTINCTValue(self, fieldname, tablename):
    #     try:
    #         conn = self.get_connection_to_db()
    #         cursor = conn.cursor()
            
    #         sqlCommand = f"SELECT DISTINCT {fieldname} FROM {tablename}"
            
    #         cursor.execute(sqlCommand)
            
    #         # Fetch all results
    #         rows = cursor.fetchall()
            
    #         columns = [desc[0] for desc in cursor.description]
    #         df = pd.DataFrame(rows, columns=columns)

    #         conn.close()
    #         return df
        
    #     except psycopg2.Error as e:
    #         print(e)
    #         return False
    
    
    #     #! Function to DELETE ALL TABLES in the current database
    # def DELETE_ALL_TABLES(self, ):
    #     try:
    #         #Connect
    #         conn = self.get_connection_to_db()
    #         cursor = conn.cursor()
            
    #         cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    #         tables = cursor.fetchall()

    #         # Build list of table names
    #         table_names = [table[0] for table in tables]

    #         # Remove system tables
    #         table_names = [name for name in table_names if not 'pg_' in name and not 'sql_' in name]

    #         # Generate DROP statements
    #         drop_queries = [f'DROP TABLE IF EXISTS {name} CASCADE;' for name in table_names]
        
    #         # Execute DROP queries
    #         for query in drop_queries:
    #             print(query)
    #             cursor.execute(query)
            
    #         conn.commit()
    #         conn.close()

    #         return True
        
    #     except psycopg2.Error as e:
    #         print(e)
    #         return False
    #     # Get all table names 
    
    
    
    
    # #!Function to properly escape special characters in postgresql
    # def escape_postgres_params(self, params):
    
    #     escaped_params = []
    
    #     for param in params:
    #         if isinstance(param, str):
    #             new_param = param.replace('#', '##')
    #             new_param = new_param.replace('\\', '\\\\')
    #             new_param = new_param.replace('\'', '\'\'')
    #             escaped_params.append(new_param)
    #         else:
    #             escaped_params.append(param)

    #     return tuple(escaped_params)





    # def fetch_all_rows(self, table_name, filters=None):
    #     filters = filters or {}
    #     where_clause = ""
        
    #     # Generate where clause if filters exist
    #     if filters:
    #         conditions = [f"{key} = ${i+1}" for i, key in enumerate(filters.keys())]
    #         where_clause = f"WHERE {' AND '.join(conditions)}"

    #     # Query to fetch all rows
    #     query = f"SELECT * FROM {table_name} {where_clause};"

    
    #     with self.connect() as conn:
    #         cursor = conn.cursor()
            
    #         if filters:
    #             cursor.execute(query, *filters.values())
    #             rows = cursor.fetchall()
    #             cursor.close()
    #         else:
    #             cursor.execute(query)
    #             rows = cursor.fetchall()
    #             cursor.close()

    
    #     # Convert fetched rows to a list of dictionaries
    #     row_dicts = [dict(row) for row in rows]
        
    #     # Convert list of dictionaries to DataFrame
    #     df = pd.DataFrame(row_dicts)
        
    #     return df
          
    # def execute_select_query(self, sql):
    #     try:
    #         with self.connect() as conn:
    #             cursor = conn.cursor()
    #             cursor.execute(sql)
    #             rows = cursor.fetchall()
    #             cursor.close()
                
    #             if not rows:
    #                 return pd.DataFrame()  # Return an empty DataFrame if no rows were fetched
                
    #             # Retrieve column names
    #             colnames = [desc[0] for desc in cursor.description]
                
    #             # Convert fetched rows to a DataFrame
    #             df = pd.DataFrame(rows, columns=colnames)
                
    #             return df

    #     except Exception as e:
    #         print(f"Error during SQL query execution: {e}")
    #         return pd.DataFrame()  # Return an empty DataFrame in case of error



        # df.to_csv(
        #         clean_csv_export_path,
        #         sep=',',                 # CSV separator
        #         index=False,             # No index in the CSV
        #         header=True,             # Include headers (column names)
        #         na_rep='',               # Empty string for NaN values
        #         float_format='%.2f',     # Format floats with 2 decimal places (for SQL compatibility)
        #         mode='w',                # Write mode (overwrite)
        #         encoding='utf-8'         # UTF-8 encoding
        #     )


    # def clean_str(self, str_text, prefix=None):
    #     if prefix is None:
    #         prefix = self.column_prefix
    #     clean_col = re.sub(r'\W+', '', str_text.lower())
    #     clean_col = f"{prefix}{clean_col.replace('"', '')}"
    #     return clean_col
    
                

        # # Bulk insert using psycopg2 and COPY
        # with psycopg2.connect(dsn=self.connection_str) as pg_conn:
        #     cursor = pg_conn.cursor()
        #     with open(clean_csv_export_path, 'r') as f:
        #         cursor.copy_expert(f'COPY {self.schema}.{table_name} FROM STDIN WITH CSV HEADER', f)
        #     cursor.close()
        #     pg_conn.commit()