

# Asynchronous Libraries 
import concurrent.futures
from multiprocessing import Pool, cpu_count
import asyncio
import aiohttp

# Standard Libraries
import os
import json
import csv
import random
import time
from io import StringIO


# Data Processing Libraries
import pandas as pd
from bs4 import BeautifulSoup
import requests

# Databse Libraries
import psycopg2
from psycopg2 import sql

#File Management
import shutil
import zipfile

# Data Source Specific Libraries
import nasdaqdatalink 

# Data Acquisition Libraries
import tldextract
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright

# Load spaCy English model (Title Case Implementation)
import spacy
from titlecase import titlecase

import json
from datetime import datetime, timezone, timedelta
import decimal
import uuid
import csv
nlp = spacy.load("en_core_web_sm")

# This is a unique key for the current execution that can be used to archive files
UNIQUE_DATE_KEY = datetime.now().strftime("%Y%m%d%H%M%S%f")

# Mapping Dictionaries from Source to Model
PositionToChaseMapping = {
    "BaseCurrencyDayChangeUnrealizedFXAccruedIncomeGainLoss": "Today's Value Change",
    "BaseCurrencyDayCostBasis": "Cost",
    "BaseCurrencyDayEndAccruedDividendIncome": "Accrued Income",
    "BaseCurrencyDayEndPriceDate": "Pricing Date",
    "BaseCurrencyDayEndUnrealizedPriceGainLoss": "Unrealized G/L Amt.",
    "BaseCurrencyEndMarketValue": "Value",
    "BaseCurrencyOriginalUnitCost": "Unit Cost",
    "BaseCurrencyYTDRealizedDividendIncome": "Accrued/Income Earned",
    "HasStalePrice": "PriceInd",
    "LocalCurrencyCode": "Local CCY",
    "LocalCurrencyDayEndUnrealizedPriceGainLoss": "Local Unrealized G/L Amt.",
    "LocalCurrencyEndMarketValue": "Local Value",
    "LocalCurrencyEndPrice": "Local Price",
    "LocalCurrencyOriginalUnitCost": "Local Unit Cost",
    "MarketPrice": "Price",
    "OtherSecurityStrategyLevel1": "Asset Strategy",
    "OtherSecurityStrategyLevel2": "Asset Strategy Detail",
    "SymCusip": "CUSIP",
    "SymTicker": "Ticker",
    "UnitsHeld": "Quantity"}

SecMappingToNasdaq = {
    "AssetClassLevel1":"category",
    "GICSSector": "sector",
    "SICCode": "siccode",
    "SICIndustryTitle": "industry",
    "InvestmentType": "category",
    "CompanyWebsiteURL": "companysite",
    "CurrencyCode": "currency",
    "SymCusip": "cusips",
    "PrimaryExchange": "exchange",
    "OtherIndustryLevel2": "sicindustry",
    "OtherSectorLevel3": "sicsector",
    "InceptionDate": "firstadded",
    "NasdaqEarliestPriceDate": "firstpricedate",
    "NasdaqEarliestFinancialQuarter": "firstquarter",
    "IsDelisted": "isdelisted",
    "NasdaqMostRecentPriceDate": "lastpricedate",
    "NasdaqLatestFinancialQuarter": "lastquarter",
    "CountryOfIssuance": "location",
    "SecurityLegalName": "name",
    "SymNasdaqPermanentTicker": "permaticker",
    "RelatedTickers": "relatedtickers",
    "SECFilingURLs": "secfilings",
    "SymTicker": "ticker"}

if True:
    pass
    #def load_file_to_postgres(csv_file_path, table_name, truncate_before_load=False):
            #     import psycopg2
            #     import pandas as pd
            #     from psycopg2 import sql
            #     import numpy as np

            #     # Connect to your PostgreSQL database
            #     conn = psycopg2.connect(
            #         dbname='platform',
            #         user='postgres',
            #         password='test',
            #         host='localhost',
            #         port='5432'
            #     )

            #     cur = conn.cursor()

            #     # Read the CSV file into a pandas DataFrame
            #     df = pd.read_csv(csv_file_path)

            #     # Convert NA values to None
            #     df = df.where(pd.notna(df), None)

            #     # Generate the SQL INSERT statement
            #     schema_name = "metadata"
                
            #     # Optionally truncate the table
            #     if truncate_before_load:
            #         truncate_query = sql.SQL("TRUNCATE TABLE {schema}.{table}").format(
            #             schema=sql.Identifier(schema_name),
            #             table=sql.Identifier(table_name)
            #         )
            #         cur.execute(truncate_query)
            #         conn.commit()
            #         print(f"Table {schema_name}.{table_name} truncated successfully")

            #     # Get table columns info
            #     cur.execute(sql.SQL("""
            #         SELECT column_name, data_type 
            #         FROM information_schema.columns 
            #         WHERE table_schema = %s AND table_name = %s
            #     """), (schema_name, table_name))

            #     table_columns = cur.fetchall()
            #     table_columns_dict = {col[0]: col[1] for col in table_columns}
            #     df_columns = [col for col in df.columns if col in table_columns_dict]

            #     # Ensure correct data formatting for PostgreSQL
            #     for col in df_columns:
            #         if table_columns_dict[col] == 'ARRAY':
            #             df[col] = df[col].apply(lambda x: f'{x}' if x is not None else None)

            #     # Construct the SQL query to insert multiple rows
            #     insert_query = sql.SQL("INSERT INTO {schema}.{table} ({fields}) VALUES {values}").format(
            #         schema=sql.Identifier(schema_name),
            #         table=sql.Identifier(table_name),
            #         fields=sql.SQL(',').join(map(sql.Identifier, df_columns)),
            #         values=sql.SQL(',').join(
            #             sql.SQL("({})").format(sql.SQL(',').join(sql.Placeholder() * len(df_columns)))
            #             for _ in df.itertuples(index=False, name=None)
            #         )
            #     )

            #     # Flatten the list of tuples for the execute method
            #     values = [item if item is not pd.NA else None for row in df[df_columns].itertuples(index=False, name=None) for item in row]

            #     try:
            #         # Execute the INSERT statement
            #         cur.execute(insert_query, values)
            #         conn.commit()
            #         print("Data loaded successfully")
            #     except Exception as e:
            #         print(f"Error: {e}")
            #         conn.rollback()

            #     # Close the cursor and connection
            #     cur.close()
            #     conn.close()



class DataLoader:

    def __init__(self,  default_table=None):
        self.connection_string = f"postgresql://postgres:lnRipjfDXV07KjgiWXyvv@michael.ch6qakwu269h.us-east-1.rds.amazonaws.com:5432/postgres"
        # self.connection_string = 'postgresql://mytech:mytech@localhost:5400/mytech' # Personal/MyTech Local
        self.default_table = default_table
        self.required_system_fields = ["UpdatedBy", "CreatedBy", "UpdatedOn", "CreatedOn", "NGUpdatedBy", "NGCreatedBy", "NGUpdatedOn", "NGCreatedOn", "id", "Id"]
        self.required_bus_fields = ["LocalCurrencyCode"]
        
        self.from_environment_dict = {
            "local":    {"connection_string": f'postgresql://postgres:test@localhost:5432/platform'},
            # "test":     {"connection_string": f'postgresql://postgres:{"df"}@communify-test.ch6qakwu269h.us-east-1.rds.amazonaws.com/platform'},
            "product":  {"connection_string": f"postgresql://postgres:lnRipjfDXV07KjgiWXyvv@michael.ch6qakwu269h.us-east-1.rds.amazonaws.com:5432/postgres"},
            # "prod":     {"connection_string": f"postgresql://postgres:lnRipjfDXV07KjgiWXyvv@michael.ch6qakwu269h.us-east-1.rds.amazonaws.com:5432/postgres"},
            }
        
        # self.to_environment_dict = {
        #     "local":    {"connection_string": f'postgresql://postgres:test@localhost:5432/platform'},
        #     "test":     {"connection_string": f'postgresql://postgres:{"uWeCFceGccLhpwJN23"}@communify-test.ch6qakwu269h.us-east-1.rds.amazonaws.com/platform'},
        #     "product":  {"connection_string": f"postgresql://postgres:cz6hDSdZ2KNXd5UgUq@communify-production.ch6qakwu269h.us-east-1.rds.amazonaws.com:5432/platform"},
           
        #     }
        
        self.table_col_defs = {}
        

        # Investment Account Numbers (Excludes Private Asset Accounts)
        self.ACCOUNT_LIST = ["218550733086", "705625596201", "937914441711", "134367817996", "538776741796", 
                        "6953450", "999244", "6958039", "1003833", "6962628", "1008422"]

        # Nasdaq Data Tables: These will be downloaded
        self.NASDAQ_TABLES = ['TICKERS', 'INDICATORS', 'METRICS', 'ACTIONS', 'SP500', 'EVENTS',  'SEP','SF1', 'SFP', 'DAILY']
                                 # 'SF3', 'SF3A', 'SF3B', 
        # folder names
        self.source_folder = f"sources"
        self.archive_folder = f"archive"

        self.HOME = os.path.expanduser("~") #User's home directory
        self.DATA = f"{self.HOME}/code/data" # Working directory for data
        self.ARCHIVE = f"{self.DATA}/{self.archive_folder}" # Archive directory for prior executions
        self.SOURCE_DATA = f"{self.DATA}/{self.source_folder}" # Source data directory (downloaded and created data from current execution)
        self.LOGS = 'logs' # Directory for logs

        self.sic_code_file_path = f"{self.SOURCE_DATA}/sic_industry_codes.json"
        self.positions_chase_path = f"{self.SOURCE_DATA}/positions-chase.csv"
        self.securitymaster_nasdaq_path = f"{self.SOURCE_DATA}/NASDAQ_TICKERS.csv"
        self.company_description_path = f"{self.SOURCE_DATA}/ticker_desc_list.json"
        self.company_description_dictionary_path = f"{self.SOURCE_DATA}/ticker_desc_dictionary.json"
        self.sec_ticker_dictionary_path = f"{self.SOURCE_DATA}/sec_tickers.json"
        self.single_stock_price_history_path = f"{self.SOURCE_DATA}/single_stock_price_history.csv"

        # Data Model Entity Files
        self.securitymaster_entity_path = f"{self.SOURCE_DATA}/SecurityMasterEntity.csv"
        self.position_entity_path = f"{self.SOURCE_DATA}/PositionEntity.csv"

        # Data File Outputs (to be loaded)
        self.Security_Master_To_Load = f"{self.DATA}/SecurityMasterToLoad.csv" 
        self.Positions_To_Load = f"{self.DATA}/PositionsToLoad.csv" 

        # Create the directories if they do not exist
        if not os.path.exists(self.DATA): os.makedirs(self.DATA)
        if not os.path.exists(f"{self.ARCHIVE}"): os.makedirs(f"{self.ARCHIVE}")
        if not os.path.exists(f"{self.ARCHIVE}"): os.makedirs(f"{self.SOURCE_self.DATA}")
        if not os.path.exists(self.LOGS): os.makedirs('logs')

    # Shared functions
    def log_it(self, message, print_it=True, color='black'):
        def got_dict(input_value):
                if isinstance(input_value, dict):
                    return True, input_value
                try:
                    type_value = type(input_value)
                    input_value = json.loads(input_value)
                except Exception as e:
                    return False, f"Type is: {type_value}.  Could not convert input to dictionary: {e}"
                return True, input_value

        is_dict, dict_value = got_dict(message)
        if is_dict:
            message = json.dumps(dict_value, indent=4)
        else:
            message = f"{message}"
            
        with open(os.path.join(LOGS, 'data_gen_log.txt'), 'a') as f:
            f.write(message)
            print(message)
    
    def multi_process_csv_chunk(self, chunk, key_column):
        chunk_dict = {}
        for key, group in chunk.groupby(key_column):
            if key not in chunk_dict:
                chunk_dict[key] = {}
            for _, row in group.iterrows():
                chunk_dict[key].update(row.dropna().to_dict())  # Merge rows
        return chunk_dict
    
    def csv_to_dict_merge_multiprocessing(self, csv_file_path, key_column, chunk_size=10000):
        merged_dict = {}

        def read_chunks(csv_file_path, chunk_size):
            return pd.read_csv(csv_file_path, chunksize=chunk_size)

        with Pool() as pool:
            chunks = read_chunks(csv_file_path, chunk_size)
            results = pool.starmap(self.multi_process_csv_chunk, [(chunk, key_column) for chunk in chunks])

        for chunk_dict in results:
            for key, row in chunk_dict.items():
                if key in merged_dict:
                    merged_dict[key].update(row)
                else:
                    merged_dict[key] = row

        return merged_dict
    
    def csv_to_dict(self, csv_file_path, key_column='AttributeName'):
        result_dict = {}
        with open(csv_file_path, mode='r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            print(reader.fieldnames)
            for row in reader: # Assuming 'AttributeName' is the name of the column to be used as the key
                key = row.get(key_column, 'ROW_HAS_NO_KEY')
                result_dict[key] = row
        return result_dict
    
    async def async_scrape_single_url(self, url):
            async def extract_same_domain_urls(page, base_url):
                # Get all anchor elements
                anchor_elements = await page.query_selector_all('a')

                # Extract href attributes and filter for same domain
                same_domain_urls = []
                diff_domain_urls = []
                for anchor in anchor_elements:
                    href = await anchor.get_attribute('href')
                    if href:
                        # Resolve relative URLs
                        url = urljoin(base_url, href)
                        # Parse URLs
                        base_domain = urlparse(base_url).netloc
                        url_domain = urlparse(url).netloc
                        # Check if the domain matches
                        if base_domain == url_domain:
                            same_domain_urls.append(url)
                        else: 
                            diff_domain_urls.append(url)
                            
                urls = {}
                urls['same_domain'] = same_domain_urls
                urls['diff_domain'] = diff_domain_urls            

                return urls

            def extract_text_from_html(html_body):
                soup = BeautifulSoup(html_body, 'html.parser')
                return soup.get_text(separator=' ', strip=True)

            def is_a_valid_url(may_be_a_url):
                try:
                    result = urlparse(may_be_a_url)
                    return all([result.scheme, result.netloc])
                except Exception as e:
                    data_loader.log_it(f"Error: URL |{url}|is invalid: {str(e)}", color="RED")
                    return ""

            def get_domain_name(url):
                ext = tldextract.extract(url)
                return f"{ext.domain}.{ext.suffix}"
            try:
                if "http" not in url:
                    url = f"https://{url}"
                                        
                if url == "" or not is_a_valid_url(url):
                    return ""
                
                unique_date_key = datetime.now().strftime("%Y%m%d%H%M%S%f")
                simple_domain_key = get_domain_name(url).replace(".", "_")
                base_domain = f"https://{get_domain_name(url)}"
                text_file_name = f"scrapes/{simple_domain_key}_{unique_date_key}.json"
            
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    try:
                        await page.goto(url)
                        await page.wait_for_selector('body')
                        body = await page.content()
                        body_text = extract_text_from_html(body)
                        urls = await extract_same_domain_urls(page, base_domain)
                        
                        data_loader.log_it(f"Successfully got full webpage for {url} with {len(body_text)} characters.")
                            
                        return_dict = {}
                        return_dict['url'] = url
                        return_dict['found_urls'] = urls
                        return_dict['body_text'] = body_text
                        return_dict['body'] = body
                        
                        with open(text_file_name, "w") as f:
                            f.write( json.dumps(return_dict, indent=4))
                            
                        return return_dict
                    
                    except Exception as e:
                        error_message = f"Error getting full webpage for {url}: {str(e)}"
                        data_loader.log_it(error_message, color="RED")
                        return {}
                    
                    finally:
                        await browser.close()
            except Exception as e:
                error_message = f"Error getting full webpage for {url}: {str(e)}"
                data_loader.log_it(error_message, color="RED")
                print(error_message)
                return {}
    
    def fetch_sec_url_once(self, url):
            headers = {
                'User-Agent': 'JustBuildIt admin@justbuildit.com',
                'Accept-Encoding': 'gzip, deflate',
                'Host': 'www.sec.gov'
                }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response
            else:
                raise Exception(f"Failed to fetch URL with status code {response.status_code}")
    
    def custom_title_case_securityname(self, text):
        
        # Define a dictionary of exceptions for specific terms
        exceptions = {
            " INC":      "Inc.",
            " LLC":      "LLC",
            " LLP":      "LLP",
            " PLC":      "PLC",
            " CORP":     "Corp",
            " CO.":       "Co.",
            " LTD":      "Ltd",
            "N.V.":     "N.V.",
            "S.A.":     "S.A.",
            "AG":       "AG",
            "S.P.A.":   "S.p.A."
        }
        # Convert the title to title case using the titlecase library
        title_cased = titlecase(text)

        # Replace exceptions with correct capitalization
        for term, replacement in exceptions.items():
            title_cased = title_cased.replace(term.title(), replacement)
        
        return title_cased
    
    def archive_source_file(self, file_path):
        if os.path.exists(file_path):
            # get the file type-extension including the. from the end of the path
            file_extension = os.path.splitext(file_path)[1]
            archive_file_path = file_path.replace(f"{source_folder}/", f"{archive_folder}/")
            archive_file_path = f"{archive_file_path.replace(file_extension, "")}_{UNIQUE_DATE_KEY}{file_extension}"
            shutil.copy(file_path, f"{ARCHIVE}/{os.path.basename(file_path)}")
            os.remove(file_path)

    #!######    SEC Ticker:  Get and Create Dictionary    ######
    def get_listed_tickers(self):
        def process_titles(data):
            for key, value in data.items():
                title = value.get('title', '')
                if title.isupper() or title.islower():  # Also handle titles that are all lowercase
                    value['title'] = data_loader.custom_title_case_securityname(title)
            return data
        self.archive_source_file(sec_ticker_dictionary_path)

        url = "https://www.sec.gov/files/company_tickers.json"


        response = self.fetch_sec_url_once(url)
        data_dict = response.json()
        
        # Process the titles in the data dictionary
        data = process_titles(data_dict)
        
        # Save the new file to the data folder
        with open(sec_ticker_dictionary_path, "w") as f:
            json.dump(data, f, indent=4)
        
        return data

    #!######    SIC Industry: Get and Create Dictionary    ######
    def get_sic_table(self):
        def clean_sic_dict(sic_dict):
            for key in sic_dict.keys():
                sic_dict[key]['Office'] = sic_dict[key]['Office'].replace('Office of', '').strip()
                sic_dict[key]['Office'] = sic_dict[key]['Office'].replace('and Services', '').strip()
                sic_dict[key]['Office'] = sic_dict[key]['Office'].replace('and Services', '').title()
                
                sic_dict[key]['Industry Title'] = sic_dict[key]['Industry Title'].replace('SERVICES-', '').strip()
                sic_dict[key]['Industry Title'] = sic_dict[key]['Industry Title'].replace('RETAIL-', '').strip()
                sic_dict[key]['Industry Title'] = sic_dict[key]['Industry Title'].replace('WHOLESALE-', '').strip()
                sic_dict[key]['Industry Title'] = sic_dict[key]['Industry Title'].replace('WHOLESALE-', '').title()
            
            return sic_dict
        
        # Define the URL
        url = 'https://www.sec.gov/corpfin/division-of-corporation-finance-standard-industrial-classification-sic-code-list'
        
        response = self.fetch_sec_url_once(url)

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the table
        table = soup.find('table', class_='list')
        
        # Extract table headers
        headers = [th.text.strip() for th in table.find('thead').find_all('th')]
        
        # Extract table rows
        rows = []
        for tr in table.find('tbody').find_all('tr'):
            cells = [td.text.strip() for td in tr.find_all('td')]
            rows.append(cells)
        
        # Convert to DataFrame
        df = pd.DataFrame(rows, columns=headers)
        
        # Convert DataFrame to dictionary with formatted keys
        sic_dict = {
            f"{int(row['SIC Code']):04d}": {
                "Office": row["Office"],
                "Industry Title": row["Industry Title"]
            }
            for _, row in df.iterrows()
        }
        # Trim the Office and Industry values to remove unnecessary repetition
        sic_dict_4digit = clean_sic_dict(sic_dict)
        
        # Create a dictionary with 2-digit SIC codes to get approximate industry categories when
        # the 4-digit SIC code is not in the dictionary
        sic_dict_2digit = {}
        for key in sic_dict_4digit.keys():
            d2key = f"{key[:2]}"
            sic_dict_2digit[d2key] = sic_dict_4digit.get(key, {})
        
        sic_dict = { "TWO_DIGIT": sic_dict_2digit, "FOUR_DIGIT": sic_dict_4digit}
        
        self.archive_source_file(sic_code_file_path)
        # Save the new file to the data folder
        with open(sic_code_file_path, "w") as f:
            json.dump(sic_dict, f, indent = 4)

        
        return sic_dict

    #!######    Company Description: Create Dictionary    ######
    def get_company_description(self):
        with open(company_description_path, "r") as f:
            desc_list_dict = json.loads(f.read())
            desc_dict = {}
            for sec_data in desc_list_dict.get('data', []):
                desc_dict[sec_data.get('ticker', "")] = sec_data.get('description', "")
            with open(company_description_dictionary_path, "w") as f:
                f.write(json.dumps(desc_dict, indent=4))
        return desc_dict

    #!######    NASDAQ: Get CSVs    ######
    def get_nasdaq_data(self):      
        # format a dat 14 days ago in YYYY-MM-DD format
        
        async def download_file(session, url, destination):
            
            """
            Asynchronous download a file from a URL.
            """
            start_time = time.time()
            print(f"Starting download of {destination} at {start_time}")
            async with session.get(url) as response:
                # Ensure the response is successful
                response.raise_for_status()
                
                # Write the content to a destination file
                with open(destination, 'wb') as f:
                    while True:
                        chunk = await response.content.read(1024)  # Read chunks of 1KB
                        if not chunk:
                            break
                        f.write(chunk)
                # if the file is a zip file, extract it
                if destination.endswith('.zip'):
                    with zipfile.ZipFile(destination, 'r') as zip_ref:
                        filenames = zip_ref.extractall(SOURCE_DATA)
                    os.remove(destination)
                print(f"Completed download of {destination} in {time.time() - start_time} seconds")
            
        async def dowload_list_of_files_async(download_status):
            
            waiting_on = []
            download_next_list = []
            # Create a session and download files concurrently
            
            async with aiohttp.ClientSession() as session:

                for file in download_status:
                    if 'downloaded' not in file or 'file.status' not in file:
                        continue
                    if file["downloaded"] == 0 and file['file.status'] == "fresh":
                        download_next_list.append(download_file(session, file["file.link"], f"{SOURCE_DATA}/{file['name']}.zip"))
                        file["downloaded"] == 1
                    elif file["downloaded"] == 1:
                        continue
                    else:
                        waiting_on.append(file)
                        
                await asyncio.gather(*download_next_list)
                
                return download_status, waiting_on

        def download_nasdaq():

            print("Beginning download of NASDAQ files")
            
            print("Getting status of NASDAQ files")
            download_list = []
        
            def create_download_item(table):
                url = f"https://data.nasdaq.com/api/v3/datatables/SHARADAR/{table}.csv?qopts.export=true&api_key=6X82a45M1zJPu2ci4TJP"
                response = requests.get(url)
                status_dict = {}
                status_dict["name"] = table
                status_dict["status"] = response.status_code
                status_dict["link"] = url
                status_dict["downloaded"] = 0
                if response.status_code == 200:
                    reader = csv.DictReader(StringIO(response.text))
                    for row in reader:
                        for column_name in reader.fieldnames:
                            status_dict[column_name] = row[column_name]
                    return status_dict
                else:
                    status_dict["status"] = "Failed"
                    status_dict["error"] = response.text
                    print(Exception(f"ERROR ... Failed to get a download link for table {table}: {response.text}"))
                    return None
        
        
            for table in self.NASDAQ_TABLES: 
                item = create_download_item(table)
                if item is not None:
                    download_list.append(item)
            
            print("Beginning download of files that are ready")

            download_list, waiting_on = asyncio.run(dowload_list_of_files_async(download_list))
            while len(waiting_on) > 0:
                download_list, waiting_on = asyncio.run(dowload_list_of_files_async(download_list))
                print(f"Still waiting on: waiting_on {waiting_on}")
                time.sleep(5)

        def rename_files():
            for csvfile in os.listdir(SOURCE_DATA):
                if csvfile.endswith('.csv'):
                    if "SHARADAR" in csvfile:
                        for filecode in self.NASDAQ_TABLES:
                            if filecode in csvfile:
                                current_name = os.path.join(SOURCE_DATA, csvfile)
                                new_name = os.path.join(SOURCE_DATA, f"NASDAQ_{filecode.upper()}.csv")
                                os.rename(current_name, new_name)
                                time.sleep(1)
                                
        download_nasdaq()   
        rename_files()

        # Open the TICKER.csv file (Nasdaq) and iterate through the rows. 
        # Securities that are old and no longer priced do not need to be included in the SecurityMaster
        # for current positions.
        nasdaq_ticker_dict = {}
        with open(securitymaster_nasdaq_path, 'r') as f:
            date_14_days_ago = datetime.now() - timedelta(days=14) 
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('table', "") != "SF1":
                    continue
                
                last_price_date_str = row.get('lastpricedate', "")
                if last_price_date_str != "":
                    last_price_date = datetime.strptime(last_price_date_str, "%Y-%m-%d")
                    # if the timedelta is greater than 14 days ago, skip the row
                    if last_price_date < date_14_days_ago:
                        continue
                if row.get('ticker', "") == "":
                    continue
                if row.get('category', "") == "": #AssetClassLevel1
                    row['category'] = "Domestic Common Stock"
                if row.get('currency', "") == "": #CurrencyCode
                    continue
                ticker = row.get('ticker', "")
                nasdaq_ticker_dict[ticker] = row
        return nasdaq_ticker_dict

    def merge_chase_data(self, row, EmptyPositionEntity):
        position = EmptyPositionEntity.copy()
        ticker = row.get("Ticker", "")
        
        security_row = nasdaq_ticker_dict.get(ticker, {})
                
        for key in position.keys():
            mapped_chase_field = PositionToChaseMapping.get(key, "")
            if mapped_chase_field:
                position[key] = row.get(mapped_chase_field, "")
            
            sec_key_map = SecMappingToNasdaq.get(key, "")
            if sec_key_map != "":
                position[key] = security_row.get(sec_key_map, "")
            
        if position['SICCode'] != "":
            office_code = f"{position['SICCode']}"[0] + "000"
            position['SICOffice'] = sic_dict.get(office_code, {}).get("Office", "")
            
        random.shuffle(ACCOUNT_LIST)
        position['ExternalSystemKeyCustody'] = ACCOUNT_LIST[0]

        return position

    def get_price_history_for_stock(self, stock_to_price):
        nasdaqdatalink.ApiConfig.api_key = "6X82a45M1zJPu2ci4TJP"
        prices = nasdaqdatalink.get_table('SHARADAR/SEP', ticker=stock_to_price, paginate=True)
        with open(single_stock_price_history_path, "w") as f:
            f.write(prices.to_csv())
        return prices
    
    def get_connection(self):
        conn = psycopg2.connect(self.connection_string)
        return conn

    def isnull_or_empty(self, value):
        return value is None or value == "" 

    def get_column_types_dict(self):
        if self.table_col_defs:
            return self.table_col_defs

        conn = self.get_connection()
        query = """SELECT table_name, column_name, data_type, udt_name
                    FROM information_schema.columns c 
                    WHERE c.table_name NOT LIKE 'pg%'
                    AND c.table_schema <> 'information_schema';"""
        cur = conn.cursor()

        cur.execute(query)
        column_types = cur.fetchall()

        column_types_by_table = {}
        for record in column_types:
            table_name, column_name, data_type, udt_name = record
            if table_name not in column_types_by_table:
                column_types_by_table[table_name] = {}
            column_types_by_table[table_name][column_name] = udt_name

        with open("column_types_by_table.json", "w") as f:
            json.dump(column_types_by_table, f, indent=4)

        cur.close()
        conn.close()
        self.table_col_defs = column_types_by_table
        return self.table_col_defs

    def csv_to_list_of_dicts(self, file_path):
        with open(file_path, mode='r', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            return [row for row in reader]
    
    def apply_upsert(self, base_row, new_row, merge_or_replace="MERGE"):
        if merge_or_replace == "REPLACE":
            return new_row

        for key in base_row.keys():
            if new_row.get(key) is not None:
                if merge_or_replace == "APPEND":
                    if not self.isnull_or_empty(new_row[key]):
                        if not isinstance(new_row[key], list):
                            base_row[key] = new_row[key]
                        else:
                            if base_row[key] != new_row[key] and new_row[key] not in base_row[key]:
                                base_row[key].append(new_row[key])
                elif merge_or_replace == "MERGE":
                    if not self.isnull_or_empty(new_row[key]):
                        base_row[key] = new_row[key]

        for key in new_row.keys():
            if key not in base_row:
                base_row[key] = new_row[key]
        return base_row

    def get_safe_insert_value(self, value, field_type, field_name):
        if value is None or value == "":
            return None

        try:
            if field_type == "smallint":
                return int(value)
            
            if field_type == "name":
                return str(value)
            
            if field_type == "boolean" or field_type == "bool":
                return bool(value)
            
            if field_type == "numeric":
                return decimal.Decimal(value)
            
            if field_type in ["timestamp with time zone", "timestamptz"]:
                if isinstance(value, datetime):
                    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
                return datetime.fromisoformat(value)
            
            if field_type == "bigint":
                return int(value)
            
            if field_type == "date":
                return datetime.strptime(value, '%Y-%m-%d').date()
            
            if field_type == "xid":
                return int(value)
            
            if field_type == "char":
                return str(value)
            
            if field_type in ["character varying", "text"]:
                return str(value)
            
            if field_type in ["anyarray", "ARRAY", "_ARRAY", "_text"] or field_type.startswith("_"):
                if isinstance(value, list): 
                    return value
                return [value]
            
            if field_type == "double precision" or field_type == "real":
                return float(value)
            
            if field_type in ["jsonb", "_jsonb"]:
                return json.dumps(value) if field_type == 'jsonb' else [json.dumps(item) for item in value]
            
            if field_type == "bytea":
                return bytes(value, 'utf-8')  # Ensure value is byte encoded
            
            if field_type in ["integer", "int4"]:
                return int(value)
            
            return value  # Default case, return the value as is

        except Exception as e:
            print(f"Error converting {value} in filed {field_name} of type {field_type}: {e}")
            return None

    def load_data(self, data_items, table_name, schema="metadata", operation="TRUNCATE", column_name_of_current_record_key=None, merge_or_replace="MERGE"):
        
        conn = self.get_connection()

        try:
            with conn:
                cur = conn.cursor()

                if operation == "TRUNCATE":
                    cur.execute(f'TRUNCATE TABLE {schema}."{table_name}";')
                    rows_to_load = data_items

                elif operation == "UPSERT":
                    rows_to_load = []
                    for item in data_items:
                        row_to_upsert = item.copy()
                        if column_name_of_current_record_key and item.get(column_name_of_current_record_key):
                            cur.execute(f'SELECT * FROM {schema}."{table_name}" WHERE "{column_name_of_current_record_key}" = %s',
                                        (item[column_name_of_current_record_key],))
                            existing_data = cur.fetchone()
                            if existing_data:
                                existing_data = dict(existing_data)
                                row_to_upsert = self.apply_upsert(existing_data, item, merge_or_replace)
                        rows_to_load.append(row_to_upsert)

                table_def = self.get_column_types_dict().get(table_name, {})
                load_guid = f"{uuid.uuid4()}"
                
                for row in rows_to_load:
                    for sysfield in self.required_system_fields:
                        if sysfield in table_def.keys():
                            print(f"Setting {sysfield} of type {table_def.get(sysfield)}")
                            if sysfield in[ 'Id', 'id']: 
                                row[sysfield] = f"{uuid.uuid4()}"
                                continue
                            if table_def.get(sysfield) == 'timestamptz': 
                                row[sysfield] = datetime.now()
                            else:
                                row[sysfield] = load_guid
                                
                key_list = [key for key in row.keys() if key in table_def.keys()]
                columns_list_of_dicts = [{key: f'"{key}"'} for key in key_list]
                placeholder_list = [f"%s" for _ in columns_list_of_dicts]
                values_list = []
                columns_list = []
                insert_log_list = []

                for row in rows_to_load:
                    row_values = []
                    row_columns = []
                    for col in columns_list_of_dicts:
                        col_key = list(col.keys())[0]
                        row_columns.append(col[col_key])
                        if col_key in self.required_system_fields:
                            pass
                        value = self.get_safe_insert_value(row[col_key], table_def[col_key], col_key)
                        row_values.append(value)
                        insert_log_list.append([col[col_key], value, table_def[col_key]])

                    insert_query = f'''
                        INSERT INTO {schema}."{table_name}" 
                        ({', '.join(row_columns)})
                        VALUES ({', '.join(placeholder_list)})
                    '''
                    if operation == "UPSERT":
                        pass 
                        # Not tested
                        # update_columns = [f"{col} = EXCLUDED.{col}" for col in columns]
                        # insert_query += f'ON CONFLICT ({column_name_of_current_record_key}) DO UPDATE SET {", ".join(update_columns)}'

                    with open("insert_query.txt", "w") as f:
                        f.write(f"{insert_query}" )
                    with open("insert_query_values.txt", "w") as f:
                        for log in insert_log_list:
                            f.write(f"{log}\n")
                    print("Executing query:", insert_query)
                    print("With values:", row_values)
                    cur.execute(insert_query, row_values)

                cur.close()

        except Exception as e:
            print("Error: ", e)
            raise

        finally:
            conn.close()
    #!  ------>  Load To Postgres Local  <------  !#

    def load_file_to_postgres(self, csv_file_path, table_name):
        import psycopg2

        # Connect to your PostgreSQL database
        conn = psycopg2.connect(
            dbname='platform',
            user='postgres',
            password='postgres',
            host='localhost',
            port='5432'
        )

        cur = conn.cursor()

        # SQL COPY command
        sql = f"""
        COPY {table_name} FROM '{csv_file_path}' WITH (FORMAT csv, HEADER true);
        """

        try:
            # Execute the COPY command
            cur.execute(sql)
            conn.commit()
            print("Data loaded successfully")
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()

        # Close the cursor and connection
        cur.close()
        conn.close()

    def get_data_from_env(self, environment_from, table_name, schema="metadata", csv_file_path=None):
            conn = self.get_connection()
            try:
                with conn:
                    cur = conn.cursor()
                    cur.execute(f'SELECT * FROM {schema}."{table_name}"')
                    data = cur.fetchall()
                    cur.close()
                    return data
            except Exception as e:
                print("Error: ", e)
                raise
            finally:
                conn.close()


if __name__ == "__main__":

    data_loader = DataLoader()


    ##################################
    #####     GLOBALS / SETUP    #####
    ##################################

    #!#  ------>  Global Variables  <------  !#
    #! Investment Account Numbers (Excludes Private Asset Accounts)
    ACCOUNT_LIST = ["218550733086", "705625596201", "937914441711", "134367817996", "538776741796", 
                    "6953450", "999244", "6958039", "1003833", "6962628", "1008422"]

    #! Nasdaq Data Tables: These will be downloaded
    NASDAQ_TABLES = ['TICKERS', 'INDICATORS'] #, 'METRICS', 'ACTIONS', 'SP500', 'EVENTS', 'SF3', 
                                            # 'SF3A', 'SF3B', 'SEP','SF1', 'SFP', 'DAILY']
    # folder names
    source_folder = f"sources"
    archive_folder = f"archive"

    HOME = os.path.expanduser("~") #User's home directory
    DATA = f"{HOME}/code/data" # Working directory for data
    ARCHIVE = f"{DATA}/{archive_folder}" # Archive directory for prior executions
    SOURCE_DATA = f"{DATA}/{source_folder}" # Source data directory (downloaded and created data from current execution)
    LOGS = 'logs' # Directory for logs

    sic_code_file_path = f"{SOURCE_DATA}/sic_industry_codes.json"
    positions_chase_path = f"{SOURCE_DATA}/positions-chase.csv"
    securitymaster_nasdaq_path = f"{SOURCE_DATA}/NASDAQ_TICKERS.csv"
    company_description_path = f"{SOURCE_DATA}/ticker_desc_list.json"
    company_description_dictionary_path = f"{SOURCE_DATA}/ticker_desc_dictionary.json"
    sec_ticker_dictionary_path = f"{SOURCE_DATA}/sec_tickers.json"
    single_stock_price_history_path = f"{SOURCE_DATA}/single_stock_price_history.csv"

    # Data Model Entity Files
    securitymaster_entity_path = f"{SOURCE_DATA}/SecurityMasterEntity.csv"
    position_entity_path = f"{SOURCE_DATA}/PositionEntity.csv"

    # Data File Outputs (to be loaded)
    Security_Master_To_Load = f"{DATA}/SecurityMasterToLoad.csv" 
    Positions_To_Load = f"{DATA}/PositionsToLoad.csv" 

    # Create the directories if they do not exist
    if not os.path.exists(DATA): os.makedirs(DATA)
    if not os.path.exists(f"{ARCHIVE}"): os.makedirs(f"{ARCHIVE}")
    if not os.path.exists(f"{ARCHIVE}"): os.makedirs(f"{SOURCE_DATA}")
    if not os.path.exists(LOGS): os.makedirs('logs')

    #############################################
    #####     Data Acquisition Functions    #####
    #############################################
    #!  ------>  Acquire All Data  <------  !#
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Functions below will run #! in parallel
        # Each function returns a dictionary and also writes the dictionary to a file for reference 
        
        # SEC Official Ticker List
        future_get_listed_tickers = executor.submit(data_loader.get_listed_tickers)
        
        # SIC Codes
        future_get_sic_table = executor.submit(data_loader.get_sic_table)
        
        # Company Descriptions #!FIXME This data is stored and not reqacqured ... ok for development)
        future_get_company_description = executor.submit(data_loader.get_company_description)

        # Nasdaq Ticker File (includes security reference data)
        future_get_nasdaq_data = executor.submit(data_loader.get_nasdaq_data)
        
    # Gather results of parallel functions
    sec_ticker_dict = future_get_listed_tickers.result()
    nasdaq_ticker_dict = future_get_nasdaq_data.result()
    sic_dict = future_get_sic_table.result()
    company_desc_dict = future_get_company_description.result()
        
    FullSecurityMaster = {}
    
    
    
    #!  ------>  Process the Security Master Data  <------  !#
    #!SECURITYMASTER ENTITY
    
    # Iterate through the SEC Ticker List and create 
    # Open the SecurityMasterEntity.csv file and turn it into a dictionary with the key being the AttributeName
    SecurityMasterEnitty = data_loader.csv_to_dict(securitymaster_entity_path)
    for key in SecurityMasterEnitty.keys():
        SecurityMasterEnitty[key] = ""
    
        
    # The FullSecurityMaster dictionary will be a dictionary where each key's value is a SecurityMasterEntity
    # It is the final output of the section.
    # !FIXME: The key is the ticker (temporarily) and needs to be our definition of a unique security
    # !We will use the SEC as a base but remove any SEC tickers for which there is no nasdaq data
    # Nasdaq Tickers
    nasdaq_ticker_dict_keys = list(set(nasdaq_ticker_dict.keys()))
    #SEC Tickers
    sec_ticker_dict_keys = {}
    for key in sec_ticker_dict.keys():
        sec_ticker_dict_keys[sec_ticker_dict.get(key, {}).get('ticker', "NO-TICKER-FOUND")] = key
    #Remove any SEC tickers for which there is no nasdaq data
    for key in sec_ticker_dict_keys:
        if key not in nasdaq_ticker_dict_keys:
            sec_ticker_dict.pop(sec_ticker_dict_keys.get(key, "NO-TICKER-FOUND"))
    # a SecurityMasterEntity for each ticker
    # Notes: The SEC File is only active securities. Ticker is unique.. CIKs can be used for acquring more data
    # Notes: Nasdaq has a lot of historical securities (which will be needed to load historical positions)
        
    for key in sec_ticker_dict.keys():
        # Empty Entity
        SME = SecurityMasterEnitty.copy()
        
        # Get the ticker to match the NASDAQ data
        ticker_str = sec_ticker_dict.get(key, {}).get('ticker', "NO-TICKER-FOUND")
        
        # Utilize the mapping dict to map the Nasdaq data to the SecurityMasterEntity
        for mapped_field in SecMappingToNasdaq.keys():

            SME[mapped_field] = nasdaq_ticker_dict.get(ticker_str, {}).get(SecMappingToNasdaq[mapped_field], "")
        
        # Override the Nasdaw data (if there was any) with the SEC data
        SME['SymTicker'] = ticker_str
        SME['CIK'] = sec_ticker_dict.get(key, {}).get('cik_str', "")
        SME['SecurityLegalName'] = sec_ticker_dict.get(key, {}).get('title', "")
        
        #Yahoo Finance Data
        SME['CompanyDescription'] = company_desc_dict.get(ticker_str, "")

        if SME.get('LocalCurrencyCode', "") == "":
            SME['LocalCurrencyCode'] = "USD"
        
        #! FIXME:  Currently, for test data, we are using the ticker as the unique identifier.  
        #! This will need to be changed 
        #! Note: this is the SEC's ticker and not the Nasdaq ticker so accuracy and completeness is as good as it gets
        FullSecurityMaster[ticker_str] = SME
        

    with open(Security_Master_To_Load, mode='w', encoding='utf-8', newline='', errors='replace') as f:

        # All of the SecurityMasterEntities have the same dictionary keys, 
        # so we can use the first one to get the fieldnames for the field names ( ie column headers)
        first_key = list(FullSecurityMaster.keys())[0]
        field_names = FullSecurityMaster[first_key].keys()
        
        # Create a DictWriter object
        writer = csv.DictWriter(f, fieldnames=field_names)
        
        # Write the header
        writer.writeheader()
        
        # Write the data
        for key in FullSecurityMaster.keys():
            writer.writerow(FullSecurityMaster[key])
    
    




#!  ------>  Process the Position Data  <------  !#

    PositionEntityDefinition = data_loader.csv_to_dict(position_entity_path)

    # Preparation: Read in the Chase positions data and convert it to a list of dictionaries

    # Get the source position data to load
    with open(positions_chase_path, 'r') as f:
        reader = csv.DictReader(f)
        positions_chase_dict = list(reader)

    # Create and empty PositionEntity dictionary to populate with the source data
    # Add/modify fields as needed to match the PositionEntity. Ignore fields that
    # that will not be mapped to the PositionEntity
    EmptyPositionEntity ={}
    for key in PositionEntityDefinition.keys():
        if key in PositionToChaseMapping.keys():
            EmptyPositionEntity[key] = ""
        if key in SecMappingToNasdaq.keys():
            EmptyPositionEntity[key] = ""
        EmptyPositionEntity['SICOffice'] = ""
        EmptyPositionEntity['SICCode'] = ""
        EmptyPositionEntity['ExternalSystemKeyCustody'] = ""

    # Get the mapping of the PositionEntity Attributes to the Chase positions data
    posmap = PositionToChaseMapping

    # Use multiprocessing to process the data in parallel
    # print(f"cpu_count: {cpu_count()}")
    # with Pool(cpu_count()) as pool:
    #     Position_List_Master = pool.map(merge_chase_data, positions_chase_dict, EmptyPositionEntity)
    Position_List_Master = []
    positions_dict = {}
    for row in positions_chase_dict:
        position = data_loader.merge_chase_data(row, EmptyPositionEntity)
        if position.get('AssetClassLevel1', "") == "":
            position['AssetClassLevel1'] = "Other"
        if position.get('SecurityLegalName', "") == "":
            continue
        Position_List_Master.append(position)
        positions_dict[position['SymTicker']] = position

    # Write the data to a csv file
    
  
    def nested_dict_to_csv(nested_dict, file_path= f'{DATA}/PositionsToLoad.csv'):
        """
        Write a nested dictionary to a CSV file using pandas.
        
        :param nested_dict: The nested dictionary to be written to CSV
        :param file_path: The path where the CSV file will be saved
        """
        # Flatten the nested dictionary
        flattened_data = []
        for outer_key, inner_dict in nested_dict.items():
            inner_dict['Index'] = outer_key  # Add the outer key as 'Index' if you want to keep it
            flattened_data.append(inner_dict)
        
        # Convert the flattened data to a DataFrame
        df = pd.DataFrame(flattened_data)
        
        # Optionally, set 'Index' as the index and drop it from the columns
        # df.set_index('Index', inplace=True)
        
        # Write the DataFrame to a CSV file
        df.to_csv(file_path, index=False)  # Set index=True if you want to include the 'Index' column
        
        print(f"CSV file has been created at: {file_path}")
        
    
    nested_dict_to_csv(positions_dict)
    
        
    # with open(f'{DATA}/PositionsToLoad.csv', 'w') as f:
        # writer = data_loader.writer(f)
        # writer.writerow(EmptyPositionEntity.keys())
        # for position in Position_List_Master:
        #     writer.writerow(position.values())

