

import streamlit as st
import classes._class_storage as allstorage
import classes._class_search_web as cf_search
import asyncio
import pandas as pd
import time
from threading import Thread
import requests

#!  #####   Streamlit App   #####  
#*  #############################
#*  ######   PAGE HEADER   ######
#*  #############################    

PAGE_TITLE = "View Dow Jones Articles"

LOGO_URL = "https://devcommunifypublic.blob.core.windows.net/devcommunifynews/cfy-blk.png"



st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=":earth_americas:",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'mailto:michael@justbuildit.com',
            'Report a bug': 'mailto:michael@justbuildit.com',
            #'About': "# This is a header. This is an *extremely* cool app!"
            })

st.sidebar.title("Communify")


st.markdown(f"""
<div style="display: flex; align-items: start; width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 5px; 
            height: 80px; background-color: lightblue; margin-bottom: 20px;"> 
  <img src="{LOGO_URL}" alt="{PAGE_TITLE}" style="width: 150px; height: auto; margin: 10px 15px 5px 0;">  
                                     <span style="flex: 1; font-size: 30px; margin: 0px 0px 10px 10px; 
                                     font-weight: 400; text-align: top; white-space: nowrap; 
  overflow: hidden; text-overflow: ellipsis;">{PAGE_TITLE}</span>  </div>
""", unsafe_allow_html=True)


storage = allstorage._storage()



    
    
    
st.subheader("Test Web Service", divider=True)
if st.button('Call Development Endpoint'):
    if 'search_query' in st.session_state and st.session_state.search_query != "":
        params = {'search_query': st.session_state.search_query}
        cf_search.request_scrape_for_query(params)
    else:
        st.write("No search query set.")

st.subheader("Search Results", divider=True)
if st.button('Recreate Table'):
    asyncio.run(storage.delete_table(storage.url_results_table_name))
    time.sleep (30)
    asyncio.run(storage.create_table_safely(storage.url_results_table_name))

# urls = asyncio.run(storage.get_all_urls())
# st.dataframe(urls)

st.subheader("Blobs", divider=True)
if st.button('Recreate Blob Store'):
    asyncio.run(storage.recreate_container(storage.table_field_data_extension))

blobs = asyncio.run(storage.get_last_n_blobs(storage.table_field_data_extension))
st.dataframe(blobs)

test_data = asyncio.run(storage.get_some_entities("TestTable"))
st.dataframe(test_data)





# async def get_logs():
#     return await storage.get_last_n_blobs('content')

# log_list = asyncio.run(get_logs())
#     # print(log_list)
# log_df = pd.DataFrame(log_list)
# st.dataframe(log_df)

