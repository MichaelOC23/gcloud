import streamlit as st
import time
if 'time_log' not in st.session_state:
    st.session_state['time_log'] = []
st.session_state['time_log'].append(("RESTART_PAGE", time.time()))
from datetime import datetime, timedelta
import requests
import os
import uuid
import asyncio
import asyncpg
import json
from threading import Thread

import google.generativeai as genai
google_api_key = os.environ["GOOGLE_API_KEY"]
google_api_key = "AIzaSyDCgIEo92h2s1J5GfkfuXZ5MJ7EtUgth-Q"
genai.configure(api_key=google_api_key)


#?############################################
#?#######     HEADER / SETUP     ############# 
#?############################################
def log_time(label):
    current_time = time.time()
    st.session_state['time_log'].append((label, current_time))
    if len(st.session_state['time_log']) > 1:
        prev_label, prev_time = st.session_state['time_log'][-2]
        elapsed_time = current_time - prev_time
        if prev_label == "RESTART_PAGE":
            print(f"\033[1;96mStarted timing for {label}\033[0m")
        else:
            print(f"{round(elapsed_time,5)}  seconds to {label} (Measured from {prev_label}):" )
log_time("Start Script")
def run_asyncio(coroutine):
    return asyncio.run(coroutine)
BASE_URL = "http://localhost:4001"
PAGE_TITLE = "Utils"
# st.set_page_config(
#         page_title=PAGE_TITLE, page_icon=":earth_americas:", layout="wide", initial_sidebar_state="expanded",
#         menu_items={'Get Help': 'mailto:michael@justbuildit.com','Report a bug': 'mailto:michael@justbuildit.com',})    
def set_up_page(page_title_text=PAGE_TITLE, light_or_dark="dark", session_state_variables=[]):    
    def initialize_session_state_variable(variable_name, variable_value):
        if variable_name not in st.session_state:
                    st.session_state[variable_name] = variable_value
    model_dict = {
            "Finance": "nlpaueb/sec-bert-base", 
            "General": "roberta-base",
            "ChatGPT-3.5": "gpt-3.5-turbo",
            "ChatGPT-4": "gpt-4-turbo",
            }
    LOGO_URL = "https://devcommunifypublic.blob.core.windows.net/devcommunifynews/jbi-logo-name@3x.png"
    for variable in session_state_variables:
        if isinstance(variable, dict):
            for key in variable.keys():
                initialize_session_state_variable(key, variable[key])    
    initialize_session_state_variable("show_session_state", False)
    initialize_session_state_variable("settings", {"divider-color": "gray",})
    # Page Title Colors
    border_color = "#FFFFFF"
    text_color = "#FFFFFF"
    background_color = "#1D1D1D"
    # Display the page title and logo and top buttons
    title_col, button_col1, button_col2 = st.columns([8, 1,1])
    st.markdown(f"""
            <div style="
            display: flex; 
            align-items: start; 
            width: 100%; 
            padding: 10px; 
            border: 1px solid {border_color}; 
            border-radius: 10px; 
            height: 80px; background-color: {background_color}; 
            margin-bottom: 20px;"> 
            
            <img src="{LOGO_URL}" alt="{PAGE_TITLE}" 
            style="width: 80px; 
            height: auto; 
            margin: 10px 40px 5px 20px;">  
            
            <span style="flex: 1; 
            font-size: 30px; 
            margin: 2px 0px 10px 10px; 
            font-weight: 400; 
            text-align: top; 
            align: right; 
            white-space: nowrap; 
            overflow: hidden; 
            color: {text_color}; 
            text-overflow: ellipsis;
            ">{PAGE_TITLE}</span>  </div>""", 
            unsafe_allow_html=True)
set_up_page()
log_time("Completed Page Setup")
def fire_and_forget(flask_path, params=None, ):
            """Make an asynchronous GET request to the specified URL."""
            url = BASE_URL + flask_path
            def request_thread(url, params):
                """The thread function that performs the request."""
                try:
                    requests.get(url, params=params)
                    print("Request sent successfully to Flask Background")
                except Exception as e:
                    print(f"Failed to send request: {e}")

            # Create and start a thread to make the request
            thread = Thread(target=request_thread, args=(url, params))
            thread.start()


#!Button to update O365 Token
def update_office_365_token():
    fire_and_forget("/create_task_auth")


st.button("Update O365 Token", key="updateo365token", on_click=update_office_365_token, use_container_width=True)
