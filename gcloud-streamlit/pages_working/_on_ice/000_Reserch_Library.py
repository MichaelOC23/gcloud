

import streamlit as st
import os
import asyncio
import datetime

from torch import embedding

import _class_streamlit as cs
from _class_storage import _storage as embed_storage


cs.set_up_page(page_title_text="Research Library", jbi_or_cfy="jbi", light_or_dark="dark", 
    session_state_variables=[{"Library": {}}, {"CurrentStack": {}},], connect_to_dj=False) 

research_library_table_name = "ResearchLibrary"

rl = cs.research_libaray()
EmbStore = embed_storage()
with open('500words.txt', 'r') as file:
    text = file.read()
    description = text[:100]
    as_of_date = "2021-01-01"   
    
unique_time_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    
# embeddings = rl.create_embeddings(text, f"Harry Potter {unique_time_string}", f"{description[:100]}...", "General", as_of_date)
# # embeddings = rl.create_embeddings(text, f"Harry Potter {unique_time_string}", f"{description[:100]}...", "ChatGPT-3.5", as_of_date)
# embeddings_list = [embeddings]

embeddings_list = rl.get_embeddings_from_user_files()
if embeddings_list and len(embeddings_list) > 0:
    st.write(embeddings_list)
    asyncio.run(EmbStore.add_update_or_delete_some_entities(research_library_table_name, embeddings_list) )

