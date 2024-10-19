# Imports

from enum import auto, unique
import re
import numpy as np

from ollama._client import Client, AsyncClient
from ollama._types import (
  GenerateResponse,
  ChatResponse,
  ProgressResponse,
  Message,
  Options,
  RequestError,
  ResponseError,
)
import ollama
from pandas.io import excel
from langchain_core.pydantic_v1 import NoneBytes
from numpy import True_, exp, isin, place
import asyncio
# from proto import Field
import streamlit as st
from openai import OpenAI
import streamlit_extras
from streamlit_extras.dataframe_explorer import dataframe_explorer 
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode, ColumnsAutoSizeMode
import os

from openai import OpenAI

import json
from datetime import datetime
import requests
import pandas as pd

import psycopg2
import uuid
import asyncpg
# from flask import redirect, url_for, session
import urllib
from urllib.parse import urlencode
# import msal

from sympy import true, use
from sympy.matrices.expressions.kronecker import validate

DEFAULT_BMM_EXCEL_ITEM_ID = os.environ.get('AZURE_APP_ITEM_ID', None) 
DEFAULT_BMM_EXCEL_DRIVE_ID = os.environ.get('AZURE_APP_DRIVE_ID', None) 


#?############################################
#?#######     HEADER / SETUP     #############
#?############################################
PAGE_TITLE = "JBI Business Model"
st.set_page_config(
        page_title=PAGE_TITLE, page_icon=":earth_americas:", layout="wide", initial_sidebar_state="collapsed",
        menu_items={'Get Help': 'mailto:michael@justbuildit.com','Report a bug': 'mailto:michael@justbuildit.com',})    

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
    

    # Standard Session state    
    initialize_session_state_variable("show_session_state", False)
    initialize_session_state_variable("AdminMode", False) 
    initialize_session_state_variable("settings", {"divider-color": "gray",})
    initialize_session_state_variable("temperature", .1)
    
    initialize_session_state_variable("sharepoint_site_list", [])
    initialize_session_state_variable("sharepoint_site_drive_list", [])
    initialize_session_state_variable("sharepoint_site_drive_item_list", [])
    
    initialize_session_state_variable("current_site_id", '')
    initialize_session_state_variable("current_drive_id", DEFAULT_BMM_EXCEL_DRIVE_ID)
    initialize_session_state_variable("current_item_id", DEFAULT_BMM_EXCEL_ITEM_ID)
    initialize_session_state_variable("current_worksheet_id", '')
    initialize_session_state_variable("current_entity_definition", None)
    
    
    
    initialize_session_state_variable("entity_list", [])
    initialize_session_state_variable("entitytype_list", [])
    initialize_session_state_variable("entitycategory_list", [])
    
    initialize_session_state_variable("possible_new_item_id", '')
    
    initialize_session_state_variable("access_token", '')
    initialize_session_state_variable("worksheet_list", '')
    
    initialize_session_state_variable("show_detail", False)
    initialize_session_state_variable("entity_detail", None)
    
    initialize_session_state_variable("excel_file_search_results", None)
    initialize_session_state_variable("excel_file_selected", {})

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

        
        # Enable the below to see border around the page and all the columns
        # st.markdown("""<code style="background-color: #FFFFFF; padding: 30px; border-radius: 6px;color: red;">Your HTML content here</code>""", unsafe_allow_html=True)

    # def display_data_tools():
    #     cs = PsqlSimpleStorage()

    #     st.session_state.models = {}
    #     st.session_state.entities = {}
    #     st.session_state.attributes = {}
        
    #     model_list, entity_list, attribute_list = cs._create_test_data()
        
    #     bcol, datacol = st.columns(2)
    #     with bcol:
            
    #         b_show_stored_data = st.button("Show Stored Data")
    #         if b_show_stored_data:    
    #             datacol.subheader("Stored Data", divider=True)
    #             data = asyncio.run(cs.get_data())
    #             datacol.write(data)
                    
    #         b_store_models = st.button("Store Models")
    #         if b_store_models:
    #             datacol.subheader("Store Models", divider=True)
    #             asyncio.run(cs.upsert_data(model_list))
    #             datacol.write("Stored Models")
            
    #         b_store_entities = st.button("Store Entities")
    #         if b_store_entities:
    #             datacol.subheader("Store Entities", divider=True)
    #             asyncio.run(  cs.upsert_data(entity_list))
    #             datacol.write("Stored Entities")
            
    #         b_store_attributes = st.button("Store Attributes")
    #         if b_store_attributes:
    #             datacol.subheader("Store Attributes", divider=True)
    #             asyncio.run(  cs.upsert_data(attribute_list))
    #             datacol.write("Stored Attributes")
            
    #         b_delete_data = st.button("dDlete Data")
    #         if b_delete_data:
    #             all_pkeys = asyncio.run(cs.get_unique_pkeys())
    #             all_rkeys = asyncio.run(cs.get_unique_rkeys())
    #             Pcol, rcol = datacol.columns(2)
    #             Pcol.selectbox("Select Partition Key", all_pkeys)
    #             p = Pcol.button("Delete Data")
    #             if p:
    #                 datacol.subheader("Delete Data", divider=True)
    #                 asyncio.run(cs.delete_data({"partitionkey": p} ))
    #                 datacol.write("Deleted Data")
    #             rcol.selectbox("Select Row Key", all_rkeys)

    #             models = datacol.st.selectbox()
    #             datacol.subheader("Delete Data", divider=True)
    #             asyncio.run(cs.delete_data({"partitionkey": "pk"} ))
    #             datacol.write("Deleted Data")

set_up_page()

####################################
#####    OFFICE 365 CLASS    #######
####################################    
class _office_365_data():
    def __init__(self):
        
        self.CLIENT_ID = os.environ.get('AZURE_APP_CLIENT_ID', 'No Key or Connection String found')
        self.TENANT_ID = os.environ.get('AZURE_APP_TENANT_ID', 'No Key or Connection String found') 
        self.CLIENT_SECRET = os.environ.get('AZURE_APP_CLIENT_SECRET', 'No Key or Connection String found') 
        self.GRAPH_ENDPOINT = 'https://graph.microsoft.com/v1.0'
        self.AUTH_ENDPOINT = f'https://login.microsoftonline.com/{self.TENANT_ID}/oauth2/v2.0/authorize'
        self.TOKEN_ENDPOINT = f'https://login.microsoftonline.com/{self.TENANT_ID}/oauth2/v2.0/token'
        self.drive_id = os.environ.get('AZURE_APP_DRIVE_ID', 'No Key or Connection String found')
        self.file_id = os.environ.get('AZURE_APP_ITEM_ID', 'No Key or Connection String found')

        self.max_rows = 12
        self.default_range = f'A1:P{self.max_rows}'
        self.non_entity_worksheets = ['Entity', 'EntityCategory', 'EntityType']
        
        
        
        #Get all the folders in a drive
        # https://graph.microsoft.com/v1.0/drives/b!OF9v-xFL-kG8ph01lMWz16BV0f71fkBCrsbU_Cqk-hv1igd2DcFLRpRTHAep_qYm/root/children
        # https://graph.microsoft.com/v1.0/drives/b!OF9v-xFL-kG8ph01lMWz16BV0f71fkBCrsbU_Cqk-hv1igd2DcFLRpRTHAep_qYm/root:/content

        self.end_points = {
            "Email": {
                "Get": "/me/messages",
                "Post": "/me/sendMail"
            },
            "Calendar": {
                "Get": "/me/events",
                "Post": "/me/events"
            },
            "Tasks": {
                "Get": "/me/todo/lists/{listId}/tasks",
                "Post": "/me/todo/lists/{listId}/tasks"
            },
            "Contacts": {
                "Get": "/me/contacts",
                "Post": "/me/contacts"}}

    def is_authenticated_to_o365(self):
        # get the home directory for the current user
        if 'access_token' in st.session_state:
            if st.session_state.access_token != "" and st.session_state.access_token is not None:
                return True
        
        home = os.path.expanduser("~")
        
        if not os.path.exists(f"{home}/.jbi"):
            os.makedirs(f"{home}/.jbi")
        
        if not os.path.exists(f"{home}/.jbi/at.json"):
            self.authenticate_to_o365()

        if os.path.exists(f"{home}/.jbi/at.json"):
            with open(f"{home}/.jbi/at.json", 'r') as f:
                at = json.load(f)
                st.session_state.access_token = at.get('access_token', None)
        
        if st.session_state.access_token is None or st.session_state.access_token == '':
            self.authenticate_to_o365()
            if st.session_state.access_token is None or st.session_state.access_token == '':
                return False
        else:
            return True
            # site_list = self.get_all_sharepoint_site_ids()
            # if len(site_list) > 0:
            #     self.jbi_site_id = site_list[0]
            #     st.session_state.access_token = at.get('access_token', None)
            #     return True
            # else:
            #     self.authenticate_to_o365()
            #     if st.session_state.access_token is None or st.session_state.access_token == '':
            #         return False
            #     else:
            #         site_list = self.get_all_sharepoint_site_ids()
            #         if len(site_list) > 0:
            #             self.jbi_site_id = site_list[0]
            #             st.session_state.access_token = at.get('access_token', None)
            #             return True
            #         else:
            #             return False

    def authenticate_to_o365(self, retry=False):
        import requests
        import msal
        try:
            # get the home directory for the current user
            home = os.path.expanduser("~")
            
            if not os.path.exists(f"{home}/.jbi"):
                os.makedirs(f"{home}/.jbi")

            # Authenticate and get an access token
            authority = f"https://login.microsoftonline.com/{self.TENANT_ID}"
            scopes = ["https://graph.microsoft.com/.default"]

            app = msal.ConfidentialClientApplication(
                self.CLIENT_ID,
                authority=authority,
                client_credential=self.CLIENT_SECRET,
            )

            token_response = app.acquire_token_for_client(scopes=scopes)

            if 'access_token' in token_response:
                with open(f"{home}/.jbi/at.json", 'w') as f:
                    json.dump(token_response, f)    
                st.session_state.access_token = token_response['access_token']
                return True
            else:
                print("Failed to obtain access token")
                if retry: st.stop()
                return False
        except Exception as e:
            print("Error obtaining access token:", e)
            if retry: st.stop()
            return False

    def get_all_sharepoint_site_ids(self):
        if st.session_state.sharepoint_site_list != []:
            return st.session_state.sharepoint_site_list
        
        headers = {'Authorization': f'Bearer {st.session_state.access_token}'}
        site_response = requests.get('https://graph.microsoft.com/v1.0/sites?search=*', headers=headers)
        if site_response.status_code != 200:
            print(f"Failed to fetch sites: {site_response.status_code} {site_response.text}")
            return []
        Site_List = []  
        response_json = site_response.json()
        for item in response_json['value']:
            Site_List.append(f"{item['displayName']} | {item['id']}" )
        st.session_state.sharepoint_site_list= Site_List
        return Site_List

    def get_all_drive_ids_for_one_site(self, site_id=None):
        if site_id is None or site_id == '':
            site_id = self.jbi_site_id
        headers = {'Authorization': f'Bearer {st.session_state.access_token}'}
        response = requests.get(f'https://graph.microsoft.com/v1.0/sites/{site_id}/drives', headers=headers)
        drive_list = []
        if response.status_code == 200:
            for item in response.json()['value']:
                drive_list.append(item['id'])
            st.session_state.sharepoint_site_drive_list = drive_list
            return drive_list   
        else:
            print(f"Failed to fetch drives: {response.status_code} {response.text}")
    
    def get_drive_items_by_search(self, search_string="*", name_contains=""):
        if not self.is_authenticated_to_o365():
            self.authenticate_to_o365()
        search_url = f'https://graph.microsoft.com/v1.0/drives/{st.session_state.current_drive_id}/root/search(q=\'{search_string}\')'

        headers = {'Authorization': f'Bearer {st.session_state.access_token}'}
        response = requests.get(search_url, headers=headers)

        if response.status_code == 200:
            search_results = response.json()
            if name_contains == "":
                return search_results['value']
            else:
                filtered_results = [item for item in search_results['value'] if name_contains.lower() in item['name'].lower()]
                return filtered_results
        else:
            st.session_state.access_token = None
            self.authenticate_to_o365(retry=True)
            self.get_drive_items_by_search(search_string, name_contains)
            raise Exception(f"Error searching files: {response.status_code}, {response.text}")
    
    def get_drive_item_id(self, drive_id=None, item_path=None):
        if drive_id is None or drive_id == '':
            drive_id = self.drive_id
        
        if item_path is None or item_path == '':
            item_path = self.item_path
        headers = {'Authorization': f'Bearer {st.session_state.access_token}'}
        
        item_response = requests.get(f'https://graph.microsoft.com/v1.0/drives/{drive_id}/root:{item_path}', headers=headers)
        item_data = item_response.json()
        item_id = item_data['id']
        return item_id
    
    def get_sites_by_display_name_search(self, display_name=""):
        
        if display_name == '':
            site_url = 'https://graph.microsoft.com/v1.0/sites?search=*'
        else:
            site_url = f'https://graph.microsoft.com/v1.0/sites?search={display_name}'
        
        headers = {'Authorization': f'Bearer {st.session_state.access_token}'}
        site_response = requests.get(site_url, headers=headers)
        sites_dict = site_response.json()
        site_list = []
        for site in sites_dict['value']:
            site_list.append(f"{site['displayName']} | {site['id']}")
        st.session_state.sharepoint_site_list = site_list
        return site_list

    def get_worksheet_dict(self):
        worksheet_list = self.get_worksheets()
        worksheet_dict = {}
        for worksheet in worksheet_list:
            worksheet_dict[worksheet['name']] = worksheet['id']
        if 'worksheet_dict' not in st.session_state:
            st.session_state.worksheet_dict = worksheet_dict
        return worksheet_dict
    
    def get_worksheets(self):
        url = f'https://graph.microsoft.com/v1.0/drives/{self.drive_id}/items/{self.file_id}/workbook/worksheets'
        headers = {'Authorization': f'Bearer {st.session_state.access_token}'}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            worksheets = response.json()['value']
            st.session_state.worksheet_list = worksheets
            return worksheets
        elif response.status_code == 401:
            st.session_state.access_token = None
            

        else:
            raise Exception(f"Error getting worksheets: {response.status_code}, {response.text}")
    
    def set_current_worksheet_id(self, worksheet_name):
        for worksheet_dict in st.session_state.worksheet_list:
            if worksheet_dict['name'] == worksheet_name:
                st.session_state.current_worksheet_id = worksheet_dict['id']
                st.session_state.current_worksheet_id = worksheet_dict['id']   #.replace('{', '').replace('}', '')
                return worksheet_dict['id']
    
    def get_worksheet_id(self, worksheet_name):
        for worksheet_dict in st.session_state.worksheet_list:
            if worksheet_dict['name'] == worksheet_name:
                return worksheet_dict['id']
                
    def get_cell_value(self, cell_address):
        url = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/items/{self.file_id}/workbook/worksheets/{st.session_state.current_worksheet_id}/range(address='{cell_address}')"
        headers = {'Authorization': f'Bearer {st.session_state.access_token}'}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            cell_value = response.json()['values'][0][0]
            return cell_value
        else:
            raise Exception(f"Error getting cell value: {response.status_code}, {response.text}")

    def get_range_values(self, range_address, worksheet_id=None ):
        if worksheet_id is None:
            worksheet_id = st.session_state.current_worksheet_id
        encoded_worksheet_id = urllib.parse.quote(worksheet_id)

        url = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/items/{self.file_id}/workbook/worksheets/{encoded_worksheet_id}/range(address='{range_address}')"
        
        headers = {'Authorization': f'Bearer {st.session_state.access_token}'}
        response = requests.get(url, headers=headers)
        # st.write(url)
        if response.status_code == 200:
            # print(f"{response.text}")
            range_values = response.json().get('values', [])
            return range_values
        else:
            if response.status_code == 401:
                st.session_state.access_token = None
                return []
            st.write(f"Error getting range values: {response.status_code}, {response.text}")
            raise Exception(f"Error getting worksheets: {response.status_code}, {response.text}")

    def set_cell_value(self, worksheet_id, cell_address, value):
        url = f'https://graph.microsoft.com/v1.0/drives/{self.drive_id}/items/{self.file_id}/workbook/worksheets/{worksheet_id}/range(address=\'{cell_address}\')'
        headers = {
            'Authorization': f'Bearer {st.session_state.access_token}',
            'Content-Type': 'application/json'
        }
        payload = {
            "values": [[value]]
        }
        response = requests.patch(url, headers=headers, json=payload)

        if response.status_code == 200:
            return True
        else:
            raise Exception(f"Error setting cell value: {response.status_code}, {response.text}")

    def set_range_values(self, worksheet_id, range_address, values):
        url = f'https://graph.microsoft.com/v1.0/drives/{self.drive_id}/items/{self.file_id}/workbook/worksheets/{worksheet_id}/range(address=\'{range_address}\')'
        headers = {
            'Authorization': f'Bearer {st.session_state.access_token}',
            'Content-Type': 'application/json'
        }
        payload = {
            "values": values
        }
        response = requests.patch(url, headers=headers, json=payload)

        if response.status_code == 200:
            return True
        else:
            raise Exception(f"Error setting range values: {response.status_code}, {response.text}")

    def set_range_fill(self, worksheet_id, range_address, fill_colors):
        encoded_worksheet_id = urllib.parse.quote(worksheet_id)
        url = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/items/{self.file_id}/workbook/worksheets/{encoded_worksheet_id}/range(address='{range_address}')/format/fill"
        headers = {'Authorization': f'Bearer {st.session_state.access_token}', 'Content-Type': 'application/json'}
        payload = {"color": fill_colors}
        response = requests.patch(url, headers=headers, json=payload)

        if response.status_code == 200: return True
        else: raise Exception(f"Error setting fill color: {response.status_code}, {response.text}")
    
    def clear_range_fill(self, worksheet_id, range_address):
        encoded_worksheet_id = urllib.parse.quote(worksheet_id)
        url = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/items/{self.file_id}/workbook/worksheets/{encoded_worksheet_id}/range(address='{range_address}')/format/fill/clear"
        headers = {'Authorization': f'Bearer {st.session_state.access_token}', 'Content-Type': 'application/json'}
        response = requests.patch(url, headers=headers)
        if response.status_code == 200: return True
        else: raise Exception(f"Error clearing fill color: {response.status_code}, {response.text}")
   
    def validate_business_model_worksheet(self, worksheet_name):
        def validate_cell_value(cell_value, col_idx):
            cell_fill = None
            comment_text = None
            if col_idx == 5:
                if cell_value == "":
                    cell_fill = "yellow"
                    comment_text = "This cell should not be empty"
            return cell_fill, comment_text
        
        # Get the worksheet ID
        worksheet_id = self.get_worksheet_id(worksheet_name)
        
        # Clear the fill color for the entire range
        self.clear_range_fill(worksheet_id, self.default_range)
        
        # Get the range values
        range_values = self.get_range_values(self.default_range, worksheet_id)
        fill_colors = [['none' for _ in range(len(range_values[0]))] for _ in range(len(range_values))]

        
        for row_idx, row in enumerate(range_values):
            for col_idx, cell_value in enumerate(row):
                # Placeholder for column-specific validation logic
                cell_fill, comment_text = validate_cell_value(cell_value, col_idx)
                if cell_fill is not None:
                    fill_colors[row_idx][col_idx] = cell_fill
                if comment_text is not None:
                    range_values[row_idx][12] = range_values[row_idx][12] + f"\n{comment_text}" 
                    # add_comment_to_cell(worksheet_id, f'{chr(col_idx + 65)}{row_idx+1}', comment_text)
        
        # Step 4: Apply the formatting array to the range
        success = self.set_range_fill(worksheet_id, self.default_range, fill_colors)
                
    
#####################################
#####     POSTGRESS CLASS     #######
#####################################
class _postgres():
    def __init__(self ):
        
        self.connection_string = os.environ.get('LOCAL_POSTGRES_CONNECTION_STRING1', 'postgresql://mytech:mytech@localhost:5400/mytech')    
        self.unique_initialization_id = uuid.uuid4()
        self.bmm_table = "business_model"
        self.parameter_table_name = "parameter"
        self.access_token_table_name = "accesstoken"
        self.default = self.bmm_table
        self.column_type_dict = {}

    async def get_column_types_dict(self, connection, table_names):
        query = """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_name = ANY($1::text[]);
        """
        column_types = await connection.fetch(query, table_names)
        
        # Organize the results in a dictionary
        column_types_by_table = {}
        for record in column_types:
            table_name = record['table_name']
            column_name = record['column_name']
            data_type = record['data_type']
            
            if table_name not in column_types_by_table:
                column_types_by_table[table_name] = []
            
            column_types_by_table[table_name].append((column_name, data_type))
    
        return column_types_by_table    
        
    def get_ngrok_public_url(self, get_new_url=False):
        def get_new_connection_string(self):
            ngrok_tcp_url = self.get_ngrok_public_url()
        
        if 'NGROK_TCP_URL_POSTGRES' in os.environ and not get_new_url:
            return os.environ['NGROK_TCP_URL_POSTGRES']
        elif get_new_url:
            return self.extract_ngrok_public_url(get_new_url=True)
        
        if 'NGROK_API_KEY' not in os.environ:
            print("NGROK_API_KEY not found in environment variables.")
            raise ValueError("NGROK_API_KEY not found in environment variables.")
        
        NGROK_API_KEY = os.getenv("NGROK_API_KEY")
        headers = {
            "Authorization": f"Bearer {NGROK_API_KEY}",
            "Ngrok-Version": "2"
        }
        url = "https://api.ngrok.com/endpoints"

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raises a HTTPError for bad responses
            data = response.json()
            
            if "endpoints" in data and len(data["endpoints"]) > 0:
                public_url = data["endpoints"][0]["public_url"]
                print(f"Extracted Public URL: {public_url}")
                os.environ['NGROK_TCP_URL_POSTGRES'] = public_url
                return public_url
            else:
                print("Failed to extract the public URL.")
                return None
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None
    
    def get_database_connection_string(self):
        return self.connection_string
    
    def get_parameter(self, parameter_name, parameter_value=None):
        try:
            conn = psycopg2.connect(self.connection_string)
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"SELECT * FROM {self.parameter_table_name} WHERE partitionkey = '{self.parameter_partition_key}' AND rowkey = '{parameter_name}'")
                    record = cursor.fetchone()
                    if record:
                        return record[2]
                    else:
                        return parameter_value
        except psycopg2.Error as e:
            print(f"An error occurred: {e}")
            return parameter_value  
        
    async def get_data(self, partitionkey=None, rowkey=None, table_name=None, unpack_structdata=True):
        
        def try_to_dict(record):
            try:
                return json.loads(record)
            except:
                return record
        
        if table_name is None or table_name == "": table_name = self.default
        
        
        
        query = f"SELECT * FROM {table_name}"
        conditions = [" iscurrent = TRUE "]
        params = []

        
        if partitionkey:
            conditions.append("partitionkey = $1")
            params.append(partitionkey)
        
        if rowkey:
            conditions.append("rowkey = $2" if partitionkey else "rowkey = $1")
            params.append(rowkey)
        
        if conditions:
            query += " WHERE" + " AND ".join(conditions)
            
        try:
            conn = await asyncpg.connect(self.connection_string)
            try:

                async with conn.transaction():
                    records = []
                    all_records = await conn.fetch(query, *params)
                    for record in all_records:
                        # Convert Record to a dict. merge with 'structdata' JSON (if unpack_structdata is True)
                        full_record = dict(record)
                        full_record['structdata'] = try_to_dict(record['structdata'])
                        if unpack_structdata:
                            full_record.update(json.loads(record['structdata'].lower()))
                        records.append(full_record)
                return records

            finally:
                await conn.close()
        except Exception as e:
            print(f"Database error during Get Data: {e}")
            return []

    async def get_unique_pkeys(self, rowkey = None, table_name=None):
        if table_name is None or table_name == "": table_name = self.default
        if rowkey is None or rowkey == "": rowkey_condition = ""
        else: rowkey_condition = f"AND rowkey = '{rowkey}'"
        
        query = f"SELECT DISTINCT partitionkey FROM {table_name} WHERE iscurrent = TRUE {rowkey_condition}"
        try:
            conn = await asyncpg.connect(self.connection_string)
            try:
                async with conn.transaction():
                    records = await conn.fetch(query)
                return [record['partitionkey'] for record in records]
            finally:
                await conn.close()
        except Exception as e:
            print(f"Database error during Get Unique PKeys: {e}")
            return []
    
    async def get_unique_rkeys(self, partitionkey = None, table_name=None):
        if table_name is None or table_name == "": table_name = self.default
        if partitionkey is None or partitionkey == "": partitionkey_condition = ""
        else: partitionkey_condition = f"AND partitionkey = '{partitionkey}'"
        
        query = f"SELECT DISTINCT rowkey FROM {table_name} WHERE iscurrent = TRUE {partitionkey_condition}"
        try:
            conn = await asyncpg.connect(self.connection_string)
            try:
                async with conn.transaction():
                    records = await conn.fetch(query)
                return [record['rowkey'] for record in records]
            finally:
                await conn.close()
        except Exception as e:
            print(f"Database error during Get Unique rowkeys: {e}")
            return []
            
    async def upsert_data(self, data_items, table_name=None):
        if table_name is None or table_name == "": table_name = self.default
        
        if not isinstance(data_items, list):
            data_items = [data_items]
            conn = await asyncpg.connect(self.connection_string)
            
            column_type_dict = await self.get_column_types_dict(conn, [table_name])
            
        # try:
            for item in data_items:
                async with conn.transaction():
                    # Fetch the current data for merging
                    existing_data = await conn.fetchrow(f"""
                        SELECT * FROM {table_name} 
                        WHERE partitionkey = $1 AND rowkey = $2 AND iscurrent = TRUE
                    """, item['partitionkey'], item['rowkey'])
                    
                    # Prepare the merged data
                    merged_data = {}
                    
                        
                    # If there is an existing record, merge the data
                    if existing_data:
                        #Iterate field by field and retain the existing data if the incoming data does not have a value for that field
                        for key in existing_data.keys():
                            
                            # Check if the incoming data has a value for the field. We retain the prior value
                            # if empty because this is a MERGE operation
                            if item.get(key, None) is None or item.get(key, None) != "":
                                merged_data[key] = existing_data[key]
                                continue
                            
                            # We now assume that the incoming data has a value for the field
                            # In order to handle the merge, we have to know what type of field it is
                            # We will use the column_type_dict to determine the field type
                            field_type = column_type_dict.get(table_name, {}).get(key, None)
                            if field_type is None:
                                ValueError(f"Field type not found for {key} in {table_name} during MERGE operation")

                            with open ("field_types.json", "w") as f:
                                f.write(json.dumps(column_type_dict, indent=4))
                            
                            
                            merged_data[key] = item.get(key, existing_data[key])
                        
                        
                        for key in existing_data.keys():
                            if item.get(key, None) is not None and item.get(key, None) != "":
                                merged_data[key] = existing_data[key]
                            merged_data[key] = item.get(key, existing_data[key])

                        
                        # Merge text[] fields (add unique values)
                        text_array_fields = ['authors', 'topics', 'speakers', 'entities']
                        for field in text_array_fields:
                            existing_array = existing_data[field] or []
                            new_array = item.get(field, [])
                            merged_array = list(set(existing_array) | set(new_array))
                            merged_data[field] = merged_array
                    else:
                        # If no existing data, use incoming data as is
                        for key, value in item.items():
                            if key in ['structdata', 'bypage', 'allpages', 'alltext', 'summaryparts']:
                                merged_data[key] = json.dumps(value)  # Convert to JSON string
                            else:
                                merged_data[key] = value

                    # Archive the existing current record if it exists
                    await conn.execute(f"""
                        UPDATE {table_name} SET archivedon = NOW() AT TIME ZONE 'UTC', iscurrent = FALSE
                        WHERE partitionkey = $1 AND rowkey = $2 AND iscurrent = TRUE
                    """, item['partitionkey'], item['rowkey'])

                    # Insert the new record
                    columns =  list(merged_data.keys()) + ['iscurrent']
                    values_placeholders = ', '.join([f"${i+1}" for i in range(len(columns))])
                    insert_sql = f"""
                        INSERT INTO {table_name} ({', '.join(columns)})
                        VALUES ({values_placeholders})
                    """
                    values = list(merged_data.values()) + [True]
                    await conn.execute(insert_sql, *values)
        # finally:
        #     await conn.close()
  
    async def add_update_or_delete_some_entities(self, table_name=None, entities_list=None, instruction_type="UPSERT_MERGE", alternate_connection_string="", attempt=1):
        def create_unique_blob_name():
            return f"{uuid.uuid4()}"
        
        #Check the validity of the parameters
        if table_name is None or table_name == "":
            table_name = self.default
        if table_name is None or table_name == "":
            raise ValueError("Table name cannot be None or empty")
        if entities_list is None or entities_list == [] or entities_list == {}:
            return ""
        if instruction_type not in ["DELETE", "UPSERT_MERGE", "UPSERT_REPLACE", "INSERT"]:
            raise ValueError("Instruction type must be either 'DELETE' 'UPSERT_REPLACE', 'INSERT', 'UPSERT_MERGE' ")
        
        #entities_list should ideally be a list of dicts
        if not isinstance(entities_list, list):
            # If it isn't and it's one dict, just turn that into a one-tem list
            if isinstance(entities_list, dict):
                entities_list = [entities_list]
            #Not sure what to do with the input value
            else:
                raise ValueError("Entities must be a list or dictionary")
        
        # Initialize the blob extension dictionary.
        # We will put large dictionary values into blobs and store the blob name in the entity.
        blob_extension = {}
        
        entity_count = len(entities_list)
        prior_percent_complete = 0
        percent_complete = 0
        on_entity = 0
        #Iterate through each entity in the list
        for entity in entities_list:
            on_entity += 1
            
            prior_percent_complete = percent_complete
            percent_complete = (on_entity / entity_count)
            
            # if round(percent_complete, 1) > round(prior_percent_complete, 1):
            #     print(f"Percent Complete: {round(percent_complete * 100, 2)}%")

            #rowkey is required for each Entity
            if entity.get("rowkey", '') == '' or entity.get("rowkey", None) == None:
                raise ValueError("rowkey cannot be None or empty")
            
            #partitionkey is required for each Entity
            if entity.get("partitionkey") == '' or entity['partitionkey'] == None:
                raise ValueError("partitionkey cannot be None or empty")
            
            #If the instruction type is not DELETE, then check for blob fields in the entity
            # Not point in checking for blobs if we are deleting the entity
            if instruction_type not in ["DELETE"]:    
                pass
                # # Iterate through each key in the entity. If the field has _blob in it,
                # # that is the indicator that the size could be too large for the entity.
                # for key in entity.keys():
                #     if "_blob".lower() in key.lower():
                #         # If the value in the field is empty, skip it
                #         blob_value = entity.get(key, None)  
                #         if blob_value is None:
                #             continue
                #         # if not isinstance(blob_value, list) and blob_value == "":
                #         #     continue
                #         # if (isinstance(blob_value, list) and len(blob_value) == 0):
                #         #     continue
                #         # If it's not empty, then create a new unique key for the blob field
                #         blob_field_key = f"{key}|{create_unique_blob_name()}"        
                #         # Put the value of the field in the blob_extension dictionary
                #         blob_extension[blob_field_key] = entity[key]
                #         # Replace the value in the entity with the new blob field key
                #         entity[key] = blob_field_key
                
                # # If there are any blob fields in the entity, then upload the blob to the storage account
                # if blob_extension != {}:
                #     for key in blob_extension.keys():
                #         raise ValueError("Blob extension is created yet")
                #         # resp = await self.upload_blob(self.table_field_data_extension, blob_field_key, blob_extension[blob_field_key], overwrite_if_exists=True, alternate_connection_string=self.transaction_pf_con_string)
                #         # print(f"Uploaded blob: {blob_field_key}")
            
            

            resp_list = []
            #The entity is now ready to be added, updated, or deleted in the tale
            conn = await asyncpg.connect(self.connection_string)
            async with conn.transaction():
                try:
                        
                    if instruction_type == "DELETE":
                        raise ValueError("DELETE Not Implemented Yet")
                    
                    if instruction_type == "UPSERT_MERGE":
                        resp = await self.upsert_data(entity, table_name)
                        
                    if instruction_type == "UPSERT_REPLACE":
                        raise ValueError("UPSERT_REPLACE Not Implemented Yet")
                        # resp = await table_client.upsert_entity(mode=UpdateMode.REPLACE, entity=entity)
                        # print(f"UPSERT_REPLACE entity: {entity['rowkey']}: {resp}")
                    
                    if instruction_type == "INSERT":
                        raise ValueError("INSERT Not Implemented Yet")
                    
                    resp_list.append(resp)
                
                except Exception as e:
                    print(f"Error: {e}")

        return resp_list
    
           #! get_entities_by_partition_key
     
    async def delete_data(self, keys, table_name=None):
        if table_name is None or table_name == "": table_name = self.default
        
        if not isinstance(keys, list):
            keys = [keys]

        try:
            conn = await asyncpg.connect(self.connection_string)
            for key in keys:
                # Construct the WHERE clause based on input keys
                where_clause = []
                values = []
                if 'partitionkey' in key:
                    where_clause.append("partitionkey = $1")
                    values.append(key['partitionkey'])
                if 'rowkey' in key:
                    where_clause.append(f"rowkey = ${len(values) + 1}")
                    values.append(key['rowkey'])

                # Construct and execute the update query to mark records as archived
                if where_clause:
                    query = f"""
                        UPDATE {table_name}
                        SET iscurrent = FALSE, archivedon = (NOW() AT TIME ZONE 'UTC')
                        WHERE {" AND ".join(where_clause)}
                    """
                    deleted_result = await conn.execute(query, *values)
                    print(f"Deleted data: {key} and got result: {deleted_result}")

            await conn.close()
        except Exception as e:
            print(f"Database error during delete: {e}")

    def _setup_BMM_table(self, table_name):

        conn = psycopg2.connect(self.connection_string)
        cursor = conn.cursor()
        
        create_table_dict = {

        "create_table": f"""CREATE TABLE IF NOT EXISTS {table_name} (

                id serial4 NOT NULL,
                partitionkey varchar(100) NULL,
                rowkey varchar(100) NULL,
                modelname varchar(100) NULL,
                modeldefinition text NULL,
                entityname varchar(100) NULL,
                entitydefinition text NULL,
                attributename varchar(100) NULL,
                attributedefinition text NULL,
                fieldtype varchar(100) NULL,
                fieldformat varchar(100) NULL,
                isrequired bool NULL,
                defaultvalue varchar(100) NULL,
                allowedvalues text[] NULL,
                comment text NULL,
                relatedurls text[] NULL,
                relateddocuments bytea NULL,
                testdata jsonb NULL,
                createdon timestamp DEFAULT CURRENT_TIMESTAMP NULL,
                archivedon timestamp NULL,
                iscurrent bool DEFAULT true NULL,
                createdby varchar(50) NULL,
                archivedby varchar(50) NULL,
                loadsource varchar(10) NULL,
                CONSTRAINT {table_name}_pkey PRIMARY KEY (id)
            );""",

            "index1": f"CREATE UNIQUE INDEX idx_partitionkey_rowkey_businessmodel ON {table_name} USING btree (partitionkey, rowkey) WHERE (iscurrent = true);"
        }
        
        conn = psycopg2.connect(self.connection_string)
        with conn:
            with conn.cursor() as cursor:
                for key, command in create_table_dict.items():
                    try:
                        cursor.execute(command)
                    except Exception as e:
                        print(f"Database error during table setup: {e} with statement: {command}")
                        break  # Or decide how to handle the error

    def _setup_parameter_table(self, table_name):

        conn = psycopg2.connect(self.connection_string)
        cursor = conn.cursor()
        
        create_table_dict = {

        "create_table": f"""CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            parametername VARCHAR(50),
            parametervalue VARCHAR(50),
            parametervaluelong VARCHAR(200),
            recordcontext VARCHAR(15) DEFAULT 'PARAMETER',
            createdon TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            archivedon TIMESTAMP,  
            iscurrent BOOLEAN DEFAULT TRUE,  
            createdby VARCHAR(50),
            archivedby VARCHAR(50),
            loadsource VARCHAR(10)
        );""",
            
            "index1": f"CREATE UNIQUE INDEX idx_partitionkey_rowkey_current ON {table_name} (parametername) WHERE iscurrent = TRUE;"


        }
        
        conn = psycopg2.connect(self.connection_string)
        with conn:
            with conn.cursor() as cursor:
                for key, command in create_table_dict.items():
                    try:
                        cursor.execute(command)
                    except Exception as e:
                        print(f"Database error during table setup: {e} with statement: {command}")
                        break  # Or decide how to handle the error
        
    def _delete_all_tables(self, limit_to_table=None):
        
        # Safety check or environment check could go here
        # e.g., confirm deletion or check if running in a production environment

        try:
            # Connect to the database
                conn = psycopg2.connect(self.connection_string)
                with conn:
                    with conn.cursor() as cursor:
                        if limit_to_table:
                            cursor.execute(f"DROP TABLE IF EXISTS {limit_to_table} CASCADE;")
                        else:
                            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                            tables = cursor.fetchall()

                            # Build list of table names, excluding system tables
                            table_names = [table[0] for table in tables if not table[0].startswith(('pg_', 'sql_'))]

                            # Generate and execute DROP TABLE statements in a single transaction
                            if table_names:
                                drop_query = "DROP TABLE IF EXISTS " + ", ".join(table_names) + " CASCADE;"
                                print(drop_query)  # Optional: for logging or confirmation
                                cursor.execute(drop_query)
                                
                        # Commit changes
                        conn.commit()
                    
        except psycopg2.Error as e:
            print(f"An error occurred: {e}")
            return False
        
        return True
    

if __name__ == '__main__':
    

    #?#################################
    #?####     STREAMLIT BODY    ######
    #?#################################
    def format_sidebar():   
        pass
    
    def connect_to_office365():    
        if not office.is_authenticated_to_o365():
            # In red, write that the user is not authenticated to Office 365
            st.markdown("Server connection: :orange[Not Connected]")
            st.stop()
        else:
            st.markdown("Server connection: :green[Connected]")
    
    def display_admin_tools(admin_mode=False):
        if admin_mode:
            admin_container = st.container(border=True)
            admin_container.markdown("Admin mode: :green[Enabled] | Server connection: :green[Connected]")
            admin_col1, admin_col2, admin_col3, admin_col4 = admin_container.columns([1, 3, 3, 1])
            
            # Initialize Postgres
            btn_postgres_init = admin_col1.button("Initialize Postgres")
            if btn_postgres_init:
                st.write("Initializing Postgres")
                pg._setup_BMM_table("BusinessModel")
                st.write("Postgres Initialized") 
            
            ss = admin_col2.expander("Session State Value", expanded=False)
            ss.write(st.session_state)

            select_excel_sheet_expander = admin_container.expander(f"Id of currently connected Excel Sheet:  :violet[{DEFAULT_BMM_EXCEL_ITEM_ID}]", expanded=False)
            select_excel_sheet_expander.markdown(" #### :orange[Step 1: Choose a Sharepoint Site]")
            exp_col1, exp_col2, exp_col3= select_excel_sheet_expander.columns([5, 1, 6])

            def get_drives_for_site():
                st.session_state.current_site_id = st.session_state.sharepoint_site.split(" | ")[1].strip().split(",")[1].strip()
                st.session_state.sharepoint_site_drive_list = office.get_all_drive_ids_for_one_site(st.session_state.current_site_id)
            
            def set_current_drive_id():
                st.session_state.current_drive_id = st.session_state.selected_drive.split(" | ")[1].strip().split(",")[1].strip()
                st.session_state.sharepoint_site_drive_item_list = office.get_drive_items_by_search()
            
            
            #Search JBI Websites:
            site_search_string = exp_col1.text_input(label="Search Site", placeholder="Search for a site ...", label_visibility="collapsed")
            search_site_btn = exp_col2.button("Filter", type='secondary', use_container_width=True)
            if search_site_btn:
                st.session_state.sharepoint_site_list = office.get_sites_by_display_name_search(site_search_string)
            
            sel_col1, sel_col2 = select_excel_sheet_expander.columns([5, 5])
            if st.session_state.sharepoint_site_list != []:
                sharepoint_site = sel_col1.selectbox("Select Site", key="sharepoint_site", options=st.session_state.sharepoint_site_list, on_change=get_drives_for_site)
            
            
            #Search Drives for the selected site:
            if st.session_state.sharepoint_site_drive_list is not None and st.session_state.sharepoint_site_drive_list != [] and len(st.session_state.sharepoint_site_drive_list)>1 :
                selected_drive = select_excel_sheet_expander.selectbox("Select Drive", key="selected_drive", options=st.session_state.sharepoint_site_drive_list, on_change=set_current_drive_id)
            else:
                if st.session_state.sharepoint_site_drive_list != [] and st.session_state.current_drive_id == "":
                    st.session_state.current_drive_id = st.session_state.sharepoint_site_drive_list[0]
            
            if st.session_state.current_drive_id != "":
                select_excel_sheet_expander.divider()
                select_excel_sheet_expander.markdown(" #### :orange[Step 2: Choose a drive on the Sharepoint Site]")
                selected_drive = select_excel_sheet_expander.text_input("Drive Selected:", value=st.session_state.current_drive_id, disabled=True)
                
                select_excel_sheet_expander.divider()
                select_excel_sheet_expander.markdown(" #### :orange[Step 3: Select a file and update the default Excel Sheet Id]")
                if st.session_state.current_item_id == "":
                    place_holder_text = "Select a row from the table below ...."
                else:
                    place_holder_text = os.environ.get('AZURE_APP_ITEM_ID')
                
                def get_value_from_dataframe(df, row_number, column_title):

                    try:
                        value = df.at[row_number, column_title]
                        return value
                    except KeyError:
                        st.error(f"Column title '{column_title}' does not exist in the DataFrame.")
                    except IndexError:
                        st.error(f"Row number '{row_number}' is out of bounds for the DataFrame.")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                
                def search_files(content="", name=""):
                    item_search_results = office.get_drive_items_by_search(content,name)
                    file_list = []
                    for item in item_search_results:
                        item_dict = {
                            "name": item['name'],
                            "id": item['id'],
                            "size": item['size'],
                            "createdBy": item['createdBy']['user']['displayName'],
                            "createdDateTime": item['createdDateTime'],
                            "lastModifiedBy": item['lastModifiedBy']['user']['displayName'],
                            "lastModifiedDateTime": item['lastModifiedDateTime']
                            }
                        
                        file_list.append(item_dict)
                    return file_list
                    
                def set_possible_new_item_id():
                    # value = get_value_from_dataframe(st.session_state.df_view_grid, st.session_state.df_view_grid.selection.get('rows',[]), 'id')
                    selection = st.session_state.df_view_grid.selection
                    value = None
                    try:
                        selected_row = st.session_state.df_view_grid.selection.get('rows',None)
                        if selected_row:
                            if isinstance(selected_row, list):
                                row_num = selected_row[0]
                                value =  df.at[row_num, 'id']
                                st.session_state.possible_new_item_id = value
                                return value
                                
                    except Exception as e:
                        return None

                def_1, def_2, def_3, def_4, def_5 = select_excel_sheet_expander.columns([3,1,2,2,1])
                
                if st.session_state.possible_new_item_id != "":
                    new_item_id = def_1.text_input(label_visibility="collapsed", value=st.session_state.possible_new_item_id, placeholder=place_holder_text, label="New Item Id")
                else:
                    new_item_id = def_1.text_input(label_visibility="collapsed", placeholder=place_holder_text, label="New Item Id")
                set_default_excel_sheet_btn = def_2.button("Set Default", type='primary')
                
                
                search_content = def_3.text_input(label_visibility="collapsed", placeholder="Search file content ...", label="New Item Id")
                search_contentname = def_4.text_input(label_visibility="collapsed", placeholder="Search file name ...", label="New Item Id")
                search_files_btn = def_5.button("Search", type='primary')
                if search_files_btn:
                    file_list = search_files(search_content, search_contentname)
                else:
                    file_list = search_files()

                df = pd.DataFrame(file_list)
                df_viewer = select_excel_sheet_expander.dataframe(df, use_container_width=True, key="df_view_grid", on_select=set_possible_new_item_id, selection_mode="single-row", height=500)
                df_viewer.selection
                
                if set_default_excel_sheet_btn:
                    os.environ['AZURE_APP_ITEM_ID'] = new_item_id
                    st.session_state.current_item_id = new_item_id
                    st.write(f"Default Excel Sheet Set to: {new_item_id}")
        
            excel_file_expander = admin_col3.expander("Excel File Profile")
            if st.session_state.current_item_id != "":
                worksheets_list = office.get_worksheets()
                excel_file_expander.write(worksheets_list)
    
    def display_entity_detail_grid(df):
        gb = GridOptionsBuilder.from_dataframe(df)
        # Grid
        gb.configure_grid_options(groupDefaultExpanded=0,
                                    autoSizeStrategy="SizeColumnsToFitProvidedWidthStrategy",
                                    alwaysShowVerticalScroll=True, 
                                    groupSelectsChildren=False,
                                    enableRangeSelection=True, )
                                    # pagination=False, 
                                    # paginationPageSize=10000, domLayout='autoHeight')

        gb.configure_side_bar(columns_panel=False, filters_panel=False, )
        gb.configure_auto_height(autoHeight=True)
        gb.configure_selection(selection_mode="single", use_checkbox=False)
        
        # Columns
        gb.configure_default_column(groupable=False, value=True, enableRowGroup=False,  
                                    editable=False, suppressSizeToFit=False, suppressAutoSize=False, filter=True)
        gb.configure_column("EntityName", type_="dimension", header_name="Entity", enableRowGroup=False, rowGroup=False, hide=True)
        gb.configure_column("#", type_="dimension", header_name="#", enableRowGroup=True, rowGroup=False, hide=True)
        gb.configure_column("AttributeName", type_="dimension", header_name="Attribute", enableRowGroup=False, rowGroup=False, hide=False)
        gb.configure_column("FieldFormat", type_="dimension", header_name="Format", enableRowGroup=False, rowGroup=False, hide=False,width=100)
        gb.configure_column("FieldType", type_="dimension", header_name="Type", enableRowGroup=False, rowGroup=False, hide=True,)
        gb.configure_column("IsKey", type_="dimension", header_name="Key", enableRowGroup=False, rowGroup=False, hide=False,width=100)
        gb.configure_column("IsUnique", type_="dimension", header_name="Unique", enableRowGroup=False, rowGroup=False, hide=True,)
        gb.configure_column("RelatedEntity", type_="dimension", header_name="Related Entity", enableRowGroup=False, rowGroup=False, hide=False, width=100)
        gb.configure_column("DefaultValue", type_="dimension", header_name="Default", enableRowGroup=False, rowGroup=False, hide=True,)
        gb.configure_column("MaxLength", type_="dimension", header_name="Length", enableRowGroup=False, rowGroup=False, hide=False,width=90)
        gb.configure_column("AllowedValues", type_="dimension", header_name="Allowed Values", enableRowGroup=False, rowGroup=False, hide=True,)
        gb.configure_column("IsRequired", type_="dimension", header_name="Required", enableRowGroup=False, rowGroup=False, hide=True,)
        gb.configure_column("Definition", type_="dimension", header_name="Definition", enableRowGroup=False, rowGroup=False, hide=False,wrapText=True, autoHeight = True, width=300)
        
        
        
        gridOptions = gb.build()

        st.markdown(f'### :blue[{st.session_state.entity_detail} Entity: :green[Attribute Details]]')
        grid_response = AgGrid(
            df,
            gridOptions=gridOptions,
            enable_enterprise_modules=True,
            columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
            allow_unsafe_jscode=True,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            theme='balham', height=1000
        )
        return grid_response
    
    def export_df_to_json(df=None, key_column='AttributeName', entity_name='EntityName'):    
        if df is None:
            df = st.session_state.current_df
        
        # Specify the column to use as the key
            key_column = 'AttributeName'

            # Set the key_column as the index
            df.set_index(key_column, inplace=True)

            # Convert to JSON format
            result = df.to_dict(orient='index')

            # Convert the dictionary to a JSON string if needed
            import json
            json_result = json.dumps(result, indent=4)
            
            #get the directory path for the current user's Downloads folder
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")

            # Save to a JSON file
            with open(f"{downloads_path}/entity-{st.session_state.worksheet_dict[ws_name]}.json", 'w') as f:
                f.write(json_result)

            print(json_result)
                
    #?#############################################
    #?###      BUSINESS MODEL NAVIGATOR        ####
    #?#############################################
        
    office = _office_365_data()
    pg = _postgres()
    
    current_folder = os.path.dirname(__file__)  
    st.session_state.AdminMode = False
    
    if 'current_df' not in st.session_state:
        st.session_state['current_df'] = None
    
    format_sidebar()
    display_admin_tools(st.session_state.AdminMode)
    
    if not office.is_authenticated_to_o365():
        office.authenticate_to_o365()
        
    office.get_worksheet_dict()

    #?###########################################
    #?###          Main Page Body            ####
    #?###########################################
    
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

    button_auth = col5.button("Re-Authenticate to Office 365", use_container_width=True)
    if button_auth:
        office.authenticate_to_o365()
    
    ws_name = col1.selectbox ("Select Workbook", st.session_state.worksheet_dict.keys(), label_visibility="collapsed",)
    exp_json = col3.button("Export JSON", use_container_width=True, on_click=export_df_to_json)
    
    
    if col2.button("Select Worksheet", use_container_width=True):
        range = "A1:P500"
        temp_def = office.get_range_values(range, st.session_state.worksheet_dict[ws_name])
        columns = temp_def[0]
        temp_def = temp_def[1:]
        p_df = pd.DataFrame(temp_def, columns=columns)
        
        # Specify the column to use as the key
        key_column = 'AttributeName'

        # Set the key_column as the index
        p_df.set_index(key_column, inplace=True)
        
        # Replace empty strings and whitespace with NaN
        p_df = p_df.replace(r'^\s*$', np.nan, regex=True)
        
        # Explicitly call infer_objects to avoid future warnings
        p_df = p_df.infer_objects(copy=False)
        
        # Remove rows where all elements are NaN
        df_cleaned = p_df.dropna(how='all')
        
        # Check if the column exists
        if 'Pers55' not in df_cleaned.columns:
            # Add the column with default values (e.g., empty strings or a specific default value)
            df_cleaned['Pers55'] = ""
        st.session_state.current_df = df_cleaned
    
    dcol1, dcol2 = st.columns([8, 3])        
    if st.session_state.current_df is not None:
        def get_distinct_values(df, column_name):
            unique_values = set(df[column_name].unique().tolist())
            total_list = ["Asset Class","Asset Strategy","Asset Strategy Detail","Description","Ticker","CUSIP","Quantity","Base CCY","Local CCY","Price","PriceInd","Local Price","Today's Price Change","Price Change %","Pricing Date","Value","Today's Value Change","Value Change %","Local Value","Cost","Unit Cost","Local Unit Cost","Local Cost","Unrealized G/L Amt.","Orig. $ Gain/Loss (Base)","Local Unrealized G/L Amt.","Unrealized Gain/Loss (%)","Local Unrealized Gain/Loss (%)","Accrued/Income Earned","Local Accrued/Income Earned","Accrued Income","Est. Annual Income","Local Est. Annual Income"]
            new_list =[]
            for item in total_list:
                if item not in unique_values:
                    new_list.append(item)
            return  new_list
        dcol1.data_editor(height=1000, 
                       use_container_width=True, 
                       column_order=("AttributeName", "Pers55", "FieldType", "Definition"),
                       data=st.session_state.current_df, 
                       column_config={
                        "Pers55": st.column_config.SelectboxColumn(
                            options=get_distinct_values(st.session_state.current_df, "Pers55") 
                        )
                       },
                       key="current_df_editor")
        total_list = ["Asset Class","Asset Strategy","Asset Strategy Detail","Description","Ticker","CUSIP","Quantity","Base CCY","Local CCY","Price","PriceInd","Local Price","Today's Price Change","Price Change %","Pricing Date","Value","Today's Value Change","Value Change %","Local Value","Cost","Unit Cost","Local Unit Cost","Local Cost","Unrealized G/L Amt.","Orig. $ Gain/Loss (Base)","Local Unrealized G/L Amt.","Unrealized Gain/Loss (%)","Local Unrealized Gain/Loss (%)","Accrued/Income Earned","Local Accrued/Income Earned","Accrued Income","Est. Annual Income","Local Est. Annual Income"]
        dcol2.multiselect("Select Columns", total_list)
        
        


