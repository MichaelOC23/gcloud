import streamlit as st
import json
import asyncio
import pandas as pd
import classes._class_dow_jones as dj
import classes._class_storage as Storage
import classes._class_streamlit as cs



DJ_Session = dj.DJSearch()
storage = Storage.PsqlSimpleStorage()

cs.set_up_page(page_title_text="Communify Taxonomy Storage", jbi_or_cfy="jbi", light_or_dark="dark", connect_to_dj=True,
    session_state_variables=["settings", {"divider-color": "gray",}, {"uploaded_fixed_taxonomy": {}}, 
                             {"uploaded_complete_taxonomy": {}}, {"uploaded_ticker_taxonomy": {}}, 
                             {"show_file_history": False}]
                            )



st.subheader("Current Taxonomy Files", divider=True)


# Get and show the current taxonomy files
table_col, button_col = st.columns([7, 1])
results = asyncio.run(storage.get_data(partitionkey="communify_files"))
table_col.dataframe(pd.DataFrame(results))
if button_col.button("Refresh", key="refresh_taxonomy_files", type='secondary', use_container_width=True):
    st.rerun()



static_col, complete_col, ticker_col= st.columns([1, 1, 1])



with static_col:
    st.subheader("Upload New Static Taxonomy", divider=True)
    file_mgt = st.form(key="file_mgt_form")

    uploaded_file = file_mgt.file_uploader("Upload the Static Taxonomy", type=['json'], accept_multiple_files=False, key="static_taxonomy_upload", label_visibility="collapsed")
    uploaded_file_button = file_mgt.form_submit_button(label='View/Validate', type='secondary', use_container_width=True)
    save_button = static_col.empty()
    if uploaded_file_button and uploaded_file is not None:
        with uploaded_file as f: 
            static = f.read()
            static = json.loads(static)
            st.session_state.uploaded_fixed_taxonomy = static
            
            static_col.write(static)
        
        save_button.button("Save Static Taxonomy", key="save_static_taxonomy", type='primary', use_container_width=True)        
        
  
    if save_button and st.session_state.uploaded_fixed_taxonomy != {}:
        static_taxonomy_dict = {
            'partitionkey': "communify_files",
            'rowkey': "static_taxonomy",
            'structdata' : st.session_state.uploaded_fixed_taxonomy
            }
        asyncio.run(storage.upsert_data(data_items=static_taxonomy_dict))
        st.session_state.uploaded_fixed_taxonomy = {}


with complete_col:
    st.subheader("Upload New Complete Taxonomy", divider=True)
    complete_taxonomy_form = st.form(key="complete_taxonomy_form")  

    uploaded_file2 = complete_taxonomy_form.file_uploader("Upload the Complete Taxonomy", type=['json'], accept_multiple_files=False, key="complete_taxonomy_upload", label_visibility="collapsed")
    uploaded_file_button2 = complete_taxonomy_form.form_submit_button(label='View/Validate', type='secondary', use_container_width=True)
    save_button2 = complete_col.empty()
    if uploaded_file_button2 and uploaded_file2 is not None:
        with uploaded_file2 as f: 
            static = f.read()
            static = json.loads(static)
            st.session_state.uploaded_complete_taxonomy = static
            
            complete_col.write(static)
        
        save_button2.button("Save Complete Taxonomy", key="save_complete_taxonomy", type='primary', use_container_width=True)        
        
  
    if save_button2 and st.session_state.uploaded_complete_taxonomy != {}:
        complete_taxonomy_dict = {
            'partitionkey': "communify_files",
            'rowkey': "complete_taxonomy",
            'structdata' : st.session_state.uploaded_complete_taxonomy
            }
        asyncio.run(storage.upsert_data(data_items=complete_taxonomy_dict))
        st.session_state.uploaded_complete_taxonomy = {}
    
    
with ticker_col:
    st.subheader("Upload New Ticker Taxonomy", divider=True)
    ticker_taxonomy_form = st.form(key="ticker_taxonomy_form")  

    uploaded_file3 = ticker_taxonomy_form.file_uploader("Upload the Ticker Taxonomy", type=['json'], accept_multiple_files=False, key="complete_ticker_upload", label_visibility="collapsed")
    uploaded_file_button3 = ticker_taxonomy_form.form_submit_button(label='View/Validate', type='secondary', use_container_width=True)
    save_button3 = ticker_col.empty()
    if uploaded_file_button3 and uploaded_file3 is not None:
        with uploaded_file3 as f: 
            ticker = f.read()
            ticker = json.loads(ticker)
            st.session_state.uploaded_ticker_taxonomy = ticker
            
            ticker_col.write(ticker)
        
        save_button3.button("Save Ticker Taxonomy", key="save_ticker_taxonomy", type='primary', use_container_width=True)        
        
  
    if save_button3 and st.session_state.uploaded_ticker_taxonomy != {}:
        ticker_dict = {
            'partitionkey': "communify_files",
            'rowkey': "ticker_taxonomy",
            'structdata' : st.session_state.uploaded_ticker_taxonomy
            }
        asyncio.run(storage.upsert_data(data_items=ticker_dict))
        st.session_state.uploaded_ticker_taxonomy = {}
            
