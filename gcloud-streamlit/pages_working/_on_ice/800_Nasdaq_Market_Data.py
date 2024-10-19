import nasdaqdatalink
import streamlit as st
import pandas as pd
import csv
from io import StringIO
import time
import json
import datetime
import requests
# import classes._class_streamlit as cs
import os
# nasdaqdatalink.ApiConfig.api_key = 6X82a45M1zJPu2ci4TJP

# cs.set_up_page(page_title_text="Nasdaq Market Data", jbi_or_cfy="jbi", light_or_dark="dark", connect_to_dj=False)
with open("MSFT.csv", "w") as f:
    msft_prices = nasdaqdatalink.get_table('SHARADAR/SFP', date={'gte':'2017-01-01', 'lte':'2024-06-23'}, ticker='MSFT', paginate=True)
    f.write(msft_prices.to_csv())

if st.button("Download All Files"):
        
    nasdaq_tables = ['SF1', 'SFP', 'DAILY', 'TICKERS', 'INDICATORS', 'MEETRICS', 'ACTIONS', 'SP500', 'EVENTS', 
                    'SF3', 'SF3A', 'SF3B', 'SEP']
    st.info("Requesting file preparation")
    download_status = []
    def get_status(table):
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
            return status_dict
    for table in nasdaq_tables: 
        download_status.append(get_status(table))
    with st.expander("File Status"):
        st.data_editor(download_status, height=500, use_container_width=True)
    
    st.info("Beginning download of files that are ready:")
    
    def download_fresh_files(download_status):
        waiting_on = []
        for file in download_status:
            if file["downloaded"] == 0 and file['file.status'] == "fresh":
                st.info(f"Downloading {file['name']}")
                url = file["file.link"]
                response = requests.get(url)
                
                with open(f"nasdaq_download/{file['name']}.csv", "wb") as f:
                    f.write(response.content)
                    st.success(f"Download Complete for {file['name']}")
                file["downloaded"] = 1
            
            elif file["downloaded"] == 1:
                continue
            else:
                waiting_on.append(file)
        return download_status, waiting_on


    download_status, waiting_on = download_fresh_files(download_status)
    while len(waiting_on) > 0:
        download_status, waiting_on = download_fresh_files(download_status)
        time.sleep(5)
        st.write(waiting_on)


    

if st.button("Download"):
    if not os.path.exists('nasdaq_download'):
        os.makedirs('nasdaq_download')    
    
    url = "https://data.nasdaq.com/api/v3/datatables/SHARADAR/INDICATORS.csv?qopts.export=true&api_key=6X82a45M1zJPu2ci4TJP"
    response = requests.get(url)
    csv_response =response.text

    with open("nasdaq_download/SHARADAR_INDICATORS.csv", "wb") as f:
        f.write(response.content)
        


Overview_tab, ticker_tab, price_tab, action_tab, metrics_tab, Other_tab = st.tabs(["Overvuew", "Ticker", "Price", "Actions", "Metrics", "Other Feeds"])

with Overview_tab:
    url = "https://www.quandl.com/api/v3/datatables/SHARADAR/SFP/metadata.json?api_key=6X82a45M1zJPu2ci4TJP"
    
    # st.write((requests.get(url).json()))
    
    st.markdown("""
#### Available Feeds 
##### Core US Fundamentals Data
**SHARADAR/SF1**
- SHARADAR/DAILY
- SHARADAR/TICKERS
- SHARADAR/INDICATORS
- SHARADAR/ACTIONS
- SHARADAR/SP500
- SHARADAR/EVENTS

['SF1', 'DAILY', 'TICKERS', 'INDICATORS', 'ACTIONS', 'SP500', 'EVENTS']
                
SF3: is the most detailed view of the data with a single line item for each combination of ticker, investor, quarter, and security type
SF3A: provides summary statistics aggregated by ticker and quarter
SF3B: provides summary statistics aggregated by investor and quarter

Batch Download:
https://data.nasdaq.com/api/v3/datatables/SHARADAR/SFP.csv?qopts.export=true&api_key=6X82a45M1zJPu2ci4TJP
https://data.nasdaq.com/api/v3/datatables/SHARADAR/SF3A.csv?qopts.export=true&api_key=6X82a45M1zJPu2ci4TJP

                """)


    

with ticker_tab:
    
    st.header ("Nasdaq Tickers") 
    if st.button("Display Data", use_container_width=True, key="tickers"):
        
        st.markdown("#### Column Definitions")
        st.write(nasdaqdatalink.get_table('SHARADAR/INDICATORS', table='TICKERS'))  
        
        st.markdown("#### One Ticker")
        st.write(nasdaqdatalink.get_table('SHARADAR/TICKERS', table='SFP', ticker='AADR', paginate=True))
        
        st.markdown("#### All Tickers")
        st.write(nasdaqdatalink.get_table('SHARADAR/TICKERS', table='SFP', paginate=True))

with price_tab:
    st.header ("Nasdaq Prices")
    if st.button("Display Data", use_container_width=True, key="prices"):
        st.markdown("#### Column Definitions")
        st.write(nasdaqdatalink.get_table('SHARADAR/INDICATORS', table='SFP'))
        
        st.subheader("By Ticker", divider=True)
        st.write(nasdaqdatalink.get_table('SHARADAR/SFP', ticker='AADR', paginate=True))

        st.subheader("By Multiple Tickers", divider=True)
        st.write(nasdaqdatalink.get_table('SHARADAR/SFP', ticker=['CSCO','BAB'], paginate=True))

        st.subheader("By Date", divider=True)
        st.write(nasdaqdatalink.get_table('SHARADAR/SFP', date='2024-03-27', paginate=True))

        st.subheader("By Date Range", divider=True)
        st.write(nasdaqdatalink.get_table('SHARADAR/SFP', date={'gte':'2017-01-01', 'lte':'2017-10-30'}, ticker='AADR', paginate=True))

        st.subheader("By Last Updated", divider=True)
        st.write(nasdaqdatalink.get_table('SHARADAR/SFP', lastupdated={'gte':'2024-03-25'}, ticker='AADR', paginate=True))

with action_tab:
    st.header ("Nasdaq Corporate Actions")
    if st.button("Display Data", use_container_width=True, key="actions"):
        
        st.markdown("#### Column Definitions")
        st.write(nasdaqdatalink.get_table('SHARADAR/INDICATORS', table='ACTIONS', paginate=True))
        
        st.subheader("Corporate Actions by Ticker", divider=True)
        st.write(nasdaqdatalink.get_table('SHARADAR/ACTIONS', ticker='AADR', paginate=True))

        st.markdown("#### Corporate Actions by Date Range")
        st.write(nasdaqdatalink.get_table('SHARADAR/ACTIONS', date='2018-10-29', paginate=True))

        st.markdown("#### Corporate Actions by Type")
        st.write(nasdaqdatalink.get_table('SHARADAR/ACTIONS', action='split', paginate=True))

        st.markdown("#### All Corporate Actions")
        st.write(nasdaqdatalink.get_table('SHARADAR/ACTIONS', paginate=True))

with metrics_tab:
    st.header ("Nasdaq Metrics")
    if st.button("Display Data", use_container_width=True, key="metrics"):
        st.markdown("#### Column Definitions")
        st.write(nasdaqdatalink.get_table('SHARADAR/INDICATORS', table='METRICS'))
        st.subheader("Metrics", divider=True)
        st.write(nasdaqdatalink.get_table('SHARADAR/METRICS', paginate=True))


def refresh_nasdaq_data():
        
    # @st.cache_data
    def get_databases(databases):
        

        database_dict = {}
        for d in databases:
            
            database_dict[d.code]= {}
            database_dict[d.code]["bulk_download_url"]= d.bulk_download_url()
            database_dict[d.code]['datasets']= d.datasets()
            n=0
            dls = d.to_list()
            for df in d.data_fields():
                database_dict[d.code][df] = dls[n]
                n+=1
        return database_dict
        
    def date_handler(obj):
        """Converts datetime.date objects to strings."""
        if isinstance(obj, datetime.date):
            return obj.isoformat()  # Or any other string format you prefer
        raise TypeError("Type not serializable")

    def get_data_sets(all_databases_dict, db):
        
        start_time = time.time()
        data_sets = all_databases_dict[db].get('datasets', [])
        all_data_sets = {}
        

        
        for set in data_sets:
            data_set_code = set.code
            i = 0
            ds = {}
            set_data_fields = set.data_fields()
            set_fields = set.to_list()
            for set_field in set_fields:
                if not isinstance(set_field, list):
                    ds[set_data_fields[i]] = set_field
                i+=1
            
            all_data_sets[ds.get("dataset_code", "")] = ds
        
        all_databases_dict[db]["datasets"] = all_data_sets    
            
        with open(f'NasdaqData/{db}.json', 'w') as f:
            json.dump(all_data_sets, f, default=date_handler)
        
        time_to_process = time.time() - start_time
        print(f"Got Datasets for database {db} in {time_to_process} seconds")
        return all_databases_dict
    
    
    if os.path.exists('NasdaqData/all_datasets.json'):
        with open('NasdaqData/all_datasets.json', 'r') as f:
            all_databases_dict = json.load(f)
            return all_databases_dict
        
    if not os.path.exists('NasdaqData'):
        os.makedirs('NasdaqData')    
        
    databases = nasdaqdatalink.Database.all()
    all_databases_dict = get_databases(databases)
    for db in all_databases_dict.keys():
        all_databases_dict = get_data_sets(all_databases_dict, db)
        time.sleep(.3)
        
    with open('NasdaqData/all_datasets.json', 'w') as f:
        json.dump(all_databases_dict, f, default=date_handler)
    return all_databases_dict


with Other_tab:
    "Nasdaq Other Feeds/tools"
    if st.button("Refresh Nasdaq Data"):
        all_databases_dict = refresh_nasdaq_data()
        st.write(all_databases_dict)
    if st.button("Get entire SFP Table"):
        st.subheader("Entire Table", divider=True)
        st.write(data = nasdaqdatalink.get_table('SHARADAR/SFP', paginate=True))
    st.markdown("#### Indicator Column Definitions")
    st.write(nasdaqdatalink.get_table('SHARADAR/INDICATORS', table='INDICATORS'))









# st.data_editor(
#     pd.DataFrame(databases),
#     column_config={
#         "database_code": st.column_config.TextColumn("DB Code", help="The database code"),
#         "id": st.column_config.NumberColumn("Id", format="%i"),
#         "name": st.column_config.TextColumn("Name"),
#         "image": st.column_config.ImageColumn("Preview Image", help="Streamlit app preview screenshots"),
#         "description": st.column_config.TextColumn("Description", width=300),
#         "downloads": st.column_config.NumberColumn("Downloads", format="%f"),
#         "datasets_count": st.column_config.NumberColumn("# of Datasets", format="%f"),
#         "favorite": st.column_config.CheckboxColumn("Favorite"),
#         "bulk_download_url": st.column_config.LinkColumn("Bulk Download", display_text="Bulk Download"),
#         "url_name": st.column_config.TextColumn("URL Name"),
#         "exclusive": st.column_config.CheckboxColumn("Exclusive"),
        
        
#     },
#     hide_index=False, height=2000, use_container_width=True  
# )


# st.data_editor(
#     pd.DataFrame(all_data_sets),
#     column_config={
#         "database_code": st.column_config.TextColumn("DB Code", help="The database code"),
#         "id": st.column_config.NumberColumn("Id", format="%i"),
#         "name": st.column_config.TextColumn("Name"),
#         "image": st.column_config.ImageColumn("Preview Image", help="Streamlit app preview screenshots"),
#         "description": st.column_config.TextColumn("Description", width=300),
#         "downloads": st.column_config.NumberColumn("Downloads", format="%f"),
#         "datasets_count": st.column_config.NumberColumn("# of Datasets", format="%f"),
#         "favorite": st.column_config.CheckboxColumn("Favorite"),
#         "bulk_download_url": st.column_config.LinkColumn("Bulk Download", display_text="Bulk Download"),
#         "url_name": st.column_config.TextColumn("URL Name"),
#         "exclusive": st.column_config.CheckboxColumn("Exclusive"),
        
        
#     },
#     hide_index=False, height=2000, use_container_width=True  
# )


        
        
        

        
        

