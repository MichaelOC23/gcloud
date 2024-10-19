from importlib.metadata import files

from re import search
from unittest import result
import streamlit as st
import pandas as pd
import requests
import urllib.parse

import json

from sympy import div
import classes._class_dow_jones as dj
import classes._class_streamlit as cs


cs.set_up_page(page_title_text="Dow Jones AD HOC API", jbi_or_cfy="jbi", light_or_dark="dark", 
    session_state_variables=[{'good_urls', None}, {'bad_urls', None}],
                            connect_to_dj=True) 
if st.session_state.get("good_urls") == None:
    st.session_state.good_urls = []

if st.session_state.get("bad_urls") == None:
    st.session_state.bad_urls = []


def search_taxonomy(url):
    
    token = st.session_state.djtoken
    
    # Headers
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        st.session_state.bad_urls.append(url)
    else:
        st.session_state.good_urls.append(url)

    response_col, url_col = st.columns([.5, 1])
    
    with response_col:
        st.subheader("Response" ,divider=True   )
        st.write(f"Status Code: {response.status_code}")
        st.write(f"Reason: {response.reason}")
        st.write(f"URL: {response.url}")
        st.write(f"Headers: {response.headers}")
        st.write(f"Text: {response.text}")
        st.write(f"JSON: {response.json()}")

    with url_col:
        st.subheader("URLs", divider=True)
        st.dataframe(pd.DataFrame(st.session_state.good_urls, columns=["Good URLs"]))
        st.dataframe(pd.DataFrame(st.session_state.bad_urls, columns=["Bad URLs"]))
    
apiurl = st.text_input("API URL")
if st.button("Search"):
    search_taxonomy(apiurl)
