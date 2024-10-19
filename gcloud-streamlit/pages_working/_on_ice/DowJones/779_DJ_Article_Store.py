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



DJ_Session = dj.DJSearch()
DJ_Session.connect()
storage = Storage.PsqlSimpleStorage()


cs.set_up_page(page_title_text="Dow Jones Storage (Product Site)", jbi_or_cfy="jbi", light_or_dark="dark", connect_to_dj=True,
    session_state_variables=["settings", {"divider-color": "gray",}, {"uploaded_fixed_taxonomy": {}}, 
                             {"uploaded_complete_taxonomy": {}}, {"uploaded_ticker_taxonomy": {}}, 
                             {"show_file_history": False}]
                            )



# Get and show the current taxonomy files
table_col, button_col = st.columns([7, 1])
results = asyncio.run(storage.get_data(partitionkey="djcontent", unpack_structdata=False))

table_col.dataframe(pd.DataFrame(results), height=1000, use_container_width=True)
if button_col.button("Refresh", key="refresh_taxonomy_files", type='secondary', use_container_width=True):
    st.rerun()


