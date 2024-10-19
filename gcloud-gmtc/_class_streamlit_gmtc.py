
# Standard Python libraries
import streamlit as st
import os
from pathlib import Path
from _class_o365_gmtc import MS_GraphAPI
import requests
# from googleapiclient.discovery import build
# from _class_google_cloud_auth import Authenticate, CookieHandler
from msal import ConfidentialClientApplication
# import grpc
# import logging
# grpc_logger = logging.getLogger('grpc')
# grpc_logger.setLevel(logging.ERROR)

import os





####################################
####       STREAMLIT CLASS      ####
####################################
class streamlit_mytech():
    
    def __init__(self, page_title="New Page", session_state_variables = [], initial_sidebar_state="expanded", logo_url=None, auth=False):
        
        self.page_title = page_title
        print('st init')
        
        if not auth:
            # pg = self.create_menu()
            self.set_up_page(session_state_variables=[], initial_sidebar_state=initial_sidebar_state)
            # pg.run()
        else:
            print('st init auth')
            self.o365 = MS_GraphAPI()
            if st.session_state.get("authenticated", False):
                pg = self.create_menu()
                self.set_up_page(session_state_variables=[], initial_sidebar_state=initial_sidebar_state)
                pg.run()
            else: 
                self.set_up_page(session_state_variables=session_state_variables, initial_sidebar_state=initial_sidebar_state)
                self.login_ui()


    def create_google_secret(self, secret_id, secret_value, project_id='toolsexplorationfirebase'):
        
        # for key in os.environ.keys():
        #     if 'HOMEBREW' not in key:
        #         try:
        #             stm.create_google_secret(key, os.environ.get(key))
        #             print (f'Successfull added secret {key}')
        #         except:
        #             print (f'Failed to add secret {key}')
        #         time.sleep(1)
        

        
        from google.cloud import secretmanager

        # Create the Secret Manager client
        client = secretmanager.SecretManagerServiceClient()

        # Build the resource name of the parent project
        parent = f"projects/{project_id}"

        try:
            # Create the secret with automatic replication
            response = client.create_secret(request={"parent": parent, "secret_id": secret_id, "secret": {"replication": {"automatic": {}},},})
            print(f"Created secret: {response.name}")
            
            secret_name = f"projects/{project_id}/secrets/{secret_id}"
            payload = secret_value.encode("UTF-8")
            response = client.add_secret_version(request={"parent": secret_name,"payload": {"data": payload},})
            print(f"Added secret version: {response.name}")
            
        except Exception as e:
            print(f"Failed to create secret {secret_id} in project {project_id}. Error: {e}")

        return response.name
    
    def get_google_secret(self, secret_id, project_id='toolsexplorationfirebase',  version_id="latest"):
        from google.cloud import secretmanager
        secret_payload = ''
        try:
            # Create the Secret Manager client
            client = secretmanager.SecretManagerServiceClient()

            # Build the resource name of the secret version
            name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

            # Access the secret version
            response    = client.access_secret_version(request={"name": name})

            # Decode the secret payload and return it
            secret_payload = response.payload.data.decode("UTF-8")
            
        except:
            secret_payload = os.environ.get(secret_id, '')
        
        return secret_payload
        
    def set_up_page(self, session_state_variables=[], initial_sidebar_state="expanded"):

        def initialize_session_state_variable(variable_name, variable_value):
            if variable_name not in st.session_state:
                st.session_state[variable_name] = variable_value
        
            
        for variable in session_state_variables:
            if isinstance(variable, dict):
                for key in variable.keys():
                    initialize_session_state_variable(key, variable[key])
        
        
        
        
        st.set_page_config(
            page_title=self.page_title, page_icon=os.environ.get("STREAMLIT_PAGE_ICON", None), layout="wide", initial_sidebar_state=initial_sidebar_state,
            menu_items={'Get Help': 'mailto:michael@communify.com','Report a bug': 'mailto:michael@communify.com',})           
        
        # st.title(f":blue[{self.page_title}]")
        st.logo( os.environ.get("STREAMLIT_LOGO_URL", None),size= "large",icon_image=os.environ.get("STREAMLIT_ICON_URL", None))

    def get_redirect_uri(self):
        uri=os.environ.get('REDIRECT_URI', 'NO Redirect URI Found in env variables')
        if os.path.exists("/Users/michasmi"):
            uri = 'http://localhost:5010'
        if os.path.exists("/app/app.py"):
            uri = 'http://localhost:8080'
        return uri
            
    def initialize_app(self):
        authority_url = f"https://login.microsoftonline.com/{self.o365.AZURE_COMMUNIFY_TENANT_ID}"
        return ConfidentialClientApplication(self.o365.AZURE_COMMUNIFY_CLIENT_ID, authority=authority_url, client_credential=self.o365.AZURE_COMMUNIFY_CLIENT_SECRET)

    def acquire_access_token(self, app, code, scopes, redirect_uri):
        return app.acquire_token_by_authorization_code(code, scopes=scopes, redirect_uri=redirect_uri)

    def fetch_user_data(self, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}
        graph_api_endpoint = "https://graph.microsoft.com/v1.0/me"
        response = requests.get(graph_api_endpoint, headers=headers)
        return response.json()

    def authentication_process(self, app):
        scopes = ["User.Read"]
        redirect_uri = self.get_redirect_uri()
        auth_url = app.get_authorization_request_url(scopes, redirect_uri=redirect_uri)
        st.markdown(f"Please go to [this URL]({auth_url}) and authorize the app.")
        if st.query_params.get("code"):
            st.session_state["auth_code"] = st.query_params.get("code")
            token_result = self.acquire_access_token(app, st.session_state.auth_code, scopes, redirect_uri)
            if "access_token" in token_result:
                user_data = self.fetch_user_data(token_result["access_token"])
                return user_data
            else:
                st.error("Failed to acquire token. Please check your input and try again.")

    def login_ui(self):
        st.title("Microsoft Authentication")
        app = self.initialize_app()
        user_data = self.authentication_process(app)
        if user_data:
            print ('login check>authenticated')
            st.write("Welcome, ", user_data.get("displayName"))
            st.session_state["authenticated"] = True
            st.session_state["display_name"] = user_data.get("displayName")
            pg = self.create_menu()
            pg.run()
            return
        print ('login check> not aut')
        return
    
    # def create_menu(self):
        
    #     def create_page(menu_item):
    #         # print(menu_item)
    #         page = st.Page(page=f"gmtc_menu/{menu_item[0]}", title=menu_item[1].strip())
    #         return page
        
    #     menu_dict = {}
        
    #     for  heading in nav_menu.keys():
    #         for menu_item in nav_menu.get(heading):
    #             page = create_page(menu_item)
    #             if heading not in menu_dict:
    #                 menu_dict[heading] = []
    #             menu_dict[heading].append(page)
        
    #     pg = st.navigation(menu_dict)
    #     return pg


