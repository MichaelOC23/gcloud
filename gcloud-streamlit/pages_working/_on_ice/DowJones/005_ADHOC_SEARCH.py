
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




def _search():
        url = "https://api.dowjones.com/content/realtime/search"
        token = token = st.session_state.djtoken

        headers = {
            "accept": "application/vnd.dowjones.dna.content.v_1.0+json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        payload = {
            "data": {
                "id": "Search",
                "type": "content",
                "attributes": {
                "query": {
                    "content_collection": ["Publications"],
                    # "search_string": [
                    # {
                    #     "mode": "Unified",
                    #     "value": f"{'djn=p/pmdm'}"
                    # }
                    # ],
                    "search_string": [
                        {
                            "mode": "Unified",
                            "scope": "Industry",
                            "value": "i814 or i258"
                        }
                        ],

                    "date": {
                                "days_range": "Last2Years"
                            }

                },
                "formatting": {
                    "snippet_type": "Contextual",
                    "markup_type": "None",
                    "sort_order": "-PublicationDateChronological",
                    "is_return_rich_article_id": True
                },
                "navigation": {
                    "is_return_headline_coding": False,
                    "is_return_djn_headline_coding": False
                },
                "page_offset": 0,
                "page_limit": 50,
                }
            }
            }
        
        response = requests.post(url, headers=headers, data=json.dumps(payload))


        if response.status_code != 200:
            st.session_state.bad_urls.append(payload)
            st.write(response.text)
        else:
            st.session_state.good_urls.append(payload)

            response_col, url_col = st.columns([.5, 1])
        
            with response_col:
                st.subheader("Response" ,divider=True   )
                st.write(f"Status Code: {response.status_code}")
                st.write(f"Reason: {response.reason}")
                st.write(f"URL: {response.url}")
                # st.write(f"Headers: {response.headers}")
                st.json(f"{response.json().get('meta','')}")
                st.write(response.json())

            with url_col:
                st.subheader("URLs", divider=True)
                st.dataframe(pd.DataFrame(st.session_state.good_urls, columns=["Good URLs"]))
                st.dataframe(pd.DataFrame(st.session_state.bad_urls, columns=["Bad URLs"]))
                    

if st.button("Search"):
    _search()