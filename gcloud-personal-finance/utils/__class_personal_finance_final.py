

import os, sys, csv, json, chardet, re, time, uuid
from pathlib import Path

from decimal import Decimal
from datetime import datetime
import pandas as pd
from supabase import create_client, Client

def get_column_name_dict():
    return  {
            "Date,Description,Card Mem": {
                "institution": "Amex",
                "multiplier": 1,
                "map": {
                    "date": "transactiondate",
                    "description": "tranname",
                    "card_member": "accountname",
                    "account_#": "accountnumber",
                    "amount": "amount",
                    "extended_details": "note",
                    "appears_on_your_statement_as": "tranname2",
                    "address": "merchantstreetaddress",
                    "city/state": "merchantcity",
                    "zip_code": "merchantzip",
                    "country": "merchantcountry",
                    "reference": "institutiontransactionid",
                    "category": "categoryalt",
                }
            },
            "Transaction Date,Clearing": {
                "institution": "Apple",
                "multiplier": 1,
                "map": {
                    "transaction date": "transactiondate",
                    "purchased by": "accountname",
                    "merchant": "merchantname",
                    "description": "tranname",
                    "amount (usd)": "amount",
                    "type": "transactiontype",
                    "category": "categoryalt"
                }
            },
            "Trade Date,Post Date,Sett": {
                "institution": "Chase",
                "multiplier": 1,
                "map": {
                    "trade_date": "transactiondate",
                    "account_type": "accounttype",
                    "account_name": "accountname",
                    "account_number": "accountnumber",
                    "description": "tranname",
                    "tran_code_description": "tranname2",
                    "amount_usd": "amount",
                    "type": "transactiontype",
                    "check_number": "checknumber"
                }
            }
        }



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
        
    def get_csv_column_title_file_marker(self, file_path):
        """Returns the first 50 characters of the first row (column titles) of a CSV file."""
        try:
            with open(file_path, mode='r', encoding='utf-8-sig') as file:  # Use 'utf-8-sig' to auto-remove BOM if present
                reader = csv.reader(file)
                header = next(reader)  # Get the first row (column titles)
                header_str = ','.join(header).strip()  # Convert list of titles to a single string and strip whitespace
                marker = header_str[:self.csv_file_market_length]  # Return first characters
                # print(f"{marker} | {file_path}")
                return marker
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def load_folder_of_csvs_to_one_table(self, table_name, folder_path):
        results = []
        if folder_path and  len(folder_path) > 0:
            self.folder_path = folder_path
            
        for file in os.listdir(self.folder_path):
            if file.endswith('.csv'):
                csv_path = os.path.join(self.folder_path, file)              
                result = self.load_csv_to_postgres(csv_file_path=csv_path,  table_name=table_name)
                results.append(result)

        # Returning all results
        return results
    
    def create_table_name_from_csv_file_name(self, csv_path, table_name=None):
        table_name = os.path.basename(csv_path).split('.')[0]
        table_name = table_name.replace(' ', '')   # Replace spaces with blanks
        table_name = table_name.replace('-', '')   # Replace dashes with blanks
        table_name = table_name.replace('_', '')   # Replace unerscores with blanks
        
        return table_name
    
    def load_csv_to_postgres(self, csv_file_path, table_name):

        csv_file_name = os.path.basename(csv_file_path)
        encoding =  self.detect_encoding(csv_file_path)      
        df = self.get_csv_as_dataframe(csv_file_path, encoding.lower())
        
        #! Custom Logic for Transaction Files
        # Get the market do identify which institution the file is from
        marker = self.get_csv_column_title_file_marker(csv_file_path)
        
        # get the specs for the marker
        all_col_dict = get_column_name_dict()
        col_dict = all_col_dict.get(marker, {})
        if not col_dict or col_dict == {}: return [False, csv_file_name]
        
        # Remove any leading or trailing whitespace or invisible characters from column names
        df.columns = df.columns.str.strip()
        first_col_str = f"{df.columns[0]}"
        df.rename(columns={first_col_str: first_col_str.strip()})
        df.columns = [col.replace('\ufeff', '') for col in df.columns]
        # Manually clean any unexpected characters from the first column name
        # df.columns = [col.encode('utf-8').decode('utf-8-sig') for col in df.columns]

        # Now, try selecting the columns as before
        selected_columns = [col for col in col_dict.get('map', {}).keys() if col in df.columns]
        df = df[selected_columns]
        
        # Rename the columns retained to align with the model-schema
        df.rename(columns=col_dict.get('map', {}), inplace=True)
        
        #! Add columns that are standard
        df['isvalid']=True
        df['filesource']=csv_file_name
        df['institutionname']=col_dict.get('institution', 'No Institution on File Map')
        df['fileshape']=marker
        df['cashflowmultiplier'] = col_dict.get('multiplier', 1)
        
        # Convert 'trandate' to a numeric format. Here we use `.astype(int)` on the timestamp.
        # Using .astype(int) will produce nanoseconds since the epoch, so we divide by 1e9 to get seconds.
        df['uniquebusinesskey'] = df['amount'] * (df['transactiondate'].astype('int64') // 1_000_000_000)
        df = df.query('amount != 0')

        
        
        
        self.insert_data('transaction', df)
        
        
        if df is None or df.empty:
            print(f'The DataFrame for {table_name} is empty or not properly loaded.')
            print (f"The CSV {csv_file_name} does not exist or the  file is empty. Aborting load for this file.")
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

    def get_CSV_header_row(self, file_path):

        # Read the first row and extract column names
        with open(file_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            column_names = next(reader)  # Gets the first row (column names)

        return column_names

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
            response2 = supabase.table(table_name).select("*").limit(25000).execute()
            pass
            # print(response2['data'])




            
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
        create_table_statements.append("""
                                    CREATE OR REPLACE FUNCTION update_timestamp_user() 
                                    RETURNS TRIGGER AS $$ BEGIN NEW.updatedat := CURRENT_TIMESTAMP;
                                    NEW.updatedby := CURRENT_USER;
                                    RETURN NEW;
                                    END;
                                    $$ LANGUAGE plpgsql;""")

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
                    field_type = attr_value.get('Type', 'TEXT')
                    field_definitions.append(f"{attr_name} {field_type}")

            # Create the CREATE TABLE statement for the entity
            create_table_sql = f"CREATE TABLE {entity_name} ({', '.join(field_definitions)});"

            # Add the statement to the list
            create_table_statements.append(f"DROP TABLE IF EXISTS {entity_name};")
            create_table_statements.append(create_table_sql.upper())
            create_table_statements.append(f"DROP TRIGGER IF EXISTS set_update_fields ON {entity_name};")
            create_table_statements.append(f"CREATE TRIGGER set_update_fields BEFORE UPDATE ON {entity_name} FOR EACH ROW EXECUTE FUNCTION update_timestamp_user();")
        
        with open (f"{'create-personal-finance-database.sql'}", 'w') as file:
            file.write(f"{';\n\n'.join(create_table_statements)}")
        return create_table_statements
    
    


if __name__ == '__main__':
    
    pfd = personal_finance_database()
    psql = postgres_sql_utils()

    #! create_table_statements = pfd.generate_model_for_database( 'personal-finance', 'postgresql')

    psql.load_folder_of_csvs_to_one_table('transaction', f"{Path.cwd()}/transaction-files")
    
      