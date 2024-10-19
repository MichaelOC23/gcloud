from importlib.metadata import files
import streamlit as st
import json
import os
import asyncio
import pandas as pd
import requests
import classes._class_dow_jones as dj
import classes._class_storage as Storage
import classes._class_streamlit as cs

cs.set_up_page(page_title_text="Portfolio News", jbi_or_cfy="jbi", light_or_dark="dark", 
    session_state_variables=[{'page_file_path': __file__}, {'current_token_status': ""}, {'simple_search_results_cache': ""}, 
                             {'search_detail_view_id': ""}, {'DevModeState': False}, {'settings': {"divider-color": "gray"}},
                             {'target_rich_article_count': 1}],
                            connect_to_dj=True)




DJ_Session = dj.DJSearch()
    
storage = Storage.PsqlSimpleStorage()

def remove_underscores(string):
    new_string = string.replace("_", " ")
    return new_string
    
#! ##### SEARCH BY CONFIG #######
config_container = st.expander(expanded=True, label="Portfolio News (Search by Ticker)")

with open ('_archive/tickers.json', 'r') as f:
    tickers = json.load(f).get('tickers', [])
ticker_includes = config_container.multiselect(label="Stocks to Include", options = tickers, key="include_ticker_search", label_visibility="visible", placeholder="Stocks to include ...", format_func=remove_underscores)
# includes = config_container.multiselect("Include Tickers", options=tickers, key="include_tickers", default=None)

search_by_config = config_container.button("Search by Ticker", key="searchbyoneormoretickers", use_container_width=True, type="primary")

includes = []
for item in ticker_includes:
    if len(item.split("(")) != 2:
        st.error(f"Invalid Ticker: {item}")
        st.stop()
    else:
        ticker = item.split("(")[1].replace(")", "")
        includes.append(ticker)

cs.display_dj_search_results()

if not search_by_config or includes == None or len(includes) == 0:
    st.stop()

search_string =""
if search_by_config:
        
    #! ##### UI LOGIC FOR THANASI #######
    new_search_config = DJ_Session.create_user_search_config()
    new_search_config['config']['includeCodes'] = includes
    new_search_config['config']['dateRange'] = "Last6Months"
    
    search_results = DJ_Session.search_by_config(new_search_config)
    #! ##### Stre results in the session state #######
    if  DJ_Session.search_has_results:    
        st.session_state.search_result_cache = search_results
        cs.display_dj_search_results()
    

    