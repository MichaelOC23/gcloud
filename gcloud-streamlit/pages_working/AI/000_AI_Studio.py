

import streamlit as st
import os
import asyncio
import datetime
import pandas as pd
import requests
import json


import _class_streamlit as cs
from _class_storage import _storage as embed_storage


cs.set_up_page(page_title_text="AI Studio", jbi_or_cfy="jbi", light_or_dark="dark", 
    session_state_variables=[{"Library": {}}, {"CurrentStack": {}},], connect_to_dj=False) 

research_library_table_name = "ResearchLibrary"
    
unique_time_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")



    
AISTUIDO_API_KEY = os.environ.get('AISTUDIO_API_KEY')
BASE_URL = "https://getcody.ai/api/v1/"
devmode = True

def get_chat_response_from_aistudio_api(content, conversation_id):
    headers = {
        "Authorization": f"Bearer {AISTUIDO_API_KEY}",  # Replace $ACCESS_TOKEN with your actual token
        "Content-Type": "application/json"}
    
    url = f"{BASE_URL}{"messages"}"
    
    data = {"content": content, "conversation_id": conversation_id}
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        data = response.json()  # Convert JSON response to a dictionary
        return data.get('data', [])
    
    else:
        st.error(f"Request failed with status code: {response.status_code}")
        st.write(response.text)  # Display any error message from the API
        return { "error": "Request failed with status code: 400"}






def get_response_from_aistudio_api(endpoint, bot_id="", document_content="", url=""):
    
    AIS_DICT = {
        # Get API Endpoints
        "get_bots": {
            "endpoint": "bots",
            "method": "GET",
            "bot_id": bot_id,
            "description": "Get all bots"
        },
        "get_documents": {
            "endpoint": "documents",
            "method": "GET",
            "bot_id": bot_id,
            "description": "Get all documents"
        },
        "get_conversations": {
            "endpoint": "conversations",
            "method": "GET",
            "bot_id": bot_id,
            "description": "Get all conversations"
        },
        "get_conversations_by_id": {
            "endpoint": "conversations",
            "method": "GET",
            "bot_id": bot_id,
            "description": "Get one conversation"
        },

        # Create API Endpoints
        "create_bot": {
            "endpoint": "bots",
            "method": "POST",
            "bot_id": bot_id,
            "description": "Create new bot"
        },
        "create_document": {
            "endpoint": "documents",
            "method": "POST",
            "bot_id": bot_id,
            "description": "Create new document"
        },
        "create_conversation": {
            "endpoint": "conversations",
            "method": "POST",
            "bot_id": bot_id,
            "description": "Create new conversation"
        },
        "create_document_file": {
            "endpoint": "documents/file",
            "method": "POST",
            "bot_id": bot_id,
            "description": "Create a document by uploading a file"
        },

        # Update API Endpoints
        "update_conversation": {
            "endpoint": "conversations",
            "method": "POST",
            "bot_id": bot_id,
            "description": "Update a conversation"
        },

        # Delete API Endpoints
        "delete_conversation": {
            "endpoint": "conversations",
            "method": "DELETE",
            "bot_id": bot_id,
            "description": "Delete a conversation"
        },
    }
    
    API_Values = AIS_DICT[endpoint]

    headers = {"Authorization": f"Bearer {AISTUIDO_API_KEY}"}
    url = f"{BASE_URL}{API_Values['endpoint']}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()  # Convert JSON response to a dictionary
        return data.get('data', [])
    
    else:
        st.error(f"Request failed with status code: {response.status_code}")
        st.write(response.text)  # Display any error message from the API
        return { "error": "Request failed with status code: 400"}


st.title("AI Studio")
test_question = "Who is the CEO of STP Investent Services?"
st.write(f"Questions{test_question}")
response = get_chat_response_from_aistudio_api(test_question, "joQeZQ3ZgdpZ")
st.write(response)

st.subheader("All Bots")
st.dataframe(pd.DataFrame(get_response_from_aistudio_api("get_bots")), use_container_width=True)

st.subheader("All Conversations")
st.dataframe(pd.DataFrame(get_response_from_aistudio_api("get_conversations")), use_container_width=True)

st.subheader("All Documents")
st.dataframe(pd.DataFrame(get_response_from_aistudio_api("get_documents")), use_container_width=True)
  
#!##########################
#!#####    GET ALL   #######
#!##########################

#? Get all documents:
# curl \
#  -X GET https://getcody.ai/api/v1/documents \
#  -H "Authorization: Bearer $ACCESS_TOKEN"
# Create new document:


#? Get all bots:
# curl \
#  -X GET https://getcody.ai/api/v1/bots \
#  -H "Authorization: Bearer $ACCESS_TOKEN"


#? Get all conversations:
# curl \
#  -X GET https://getcody.ai/api/v1/conversations \
#  -H "Authorization: Bearer $ACCESS_TOKEN"

#? Get all documents:
# curl \
#  -X GET https://getcody.ai/api/v1/documents \
#  -H "Authorization: Bearer $ACCESS_TOKEN"

#!##########################
#!#####    GET ONE    ######
#!##########################


#? Fetch a conversation by its id:
# curl \
#  -X GET https://getcody.ai/api/v1/conversations/{id} \
#  -H "Authorization: Bearer $ACCESS_TOKEN"



#!#########################
#!#####    CREATE    ######
#!#########################

#? Create new document:
# curl \
#  -X POST https://getcody.ai/api/v1/documents \
#  -H "Authorization: Bearer $ACCESS_TOKEN" \
#  -H "Content-Type: application/json" \
#  -d '{"name":"string","folder_id":"string","content":"string"}'

#? Create new conversation:
# curl \
#  -X POST https://getcody.ai/api/v1/conversations \
#  -H "Authorization: Bearer $ACCESS_TOKEN" \
#  -H "Content-Type: application/json" \
#  -d '{"name":"string","bot_id":"string","document_ids":["string"]}'

#? Create a document by uploading a file:
# curl \
#  -X POST https://getcody.ai/api/v1/documents/file \
#  -H "Authorization: Bearer $ACCESS_TOKEN" \
#  -H "Content-Type: application/json" \
#  -d '{"folder_id":"string","key":"string"}'

#? Create a document with a webpage URL:
# curl \
#  -X POST https://getcody.ai/api/v1/documents/webpage \
#  -H "Authorization: Bearer $ACCESS_TOKEN" \
#  -H "Content-Type: application/json" \
#  -d '{"folder_id":"string","url":"https://example.com"}'


#!#########################
#!#####    UPDATE    ######
#!#########################

# curl \
#  -X POST https://getcody.ai/api/v1/conversations/{id} \
#  -H "Authorization: Bearer $ACCESS_TOKEN" \
#  -H "Content-Type: application/json" \
#  -d '{"name":"string","bot_id":"string","document_ids":["string"]}'



#!#########################
#!#####    DELETE    ######
#!#########################


#? Delete a conversation by its id:
# curl \
#  -X DELETE https://getcody.ai/api/v1/conversations/{id} \
#  -H "Authorization: Bearer $ACCESS_TOKEN"






