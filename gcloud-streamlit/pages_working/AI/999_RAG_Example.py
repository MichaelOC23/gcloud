
from openai import chat
import streamlit as st
from langchain.retrievers.you import YouRetriever
import asyncio
import classes._class_search_web as sw
import classes._class_ollama as ol
import classes._class_streamlit as cs

cs.set_up_page(page_title_text="RAG for Google Searches", jbi_or_cfy="jbi", light_or_dark="dark", 
    session_state_variables=[],
    connect_to_dj=False)



llm = ol.Ollama_LLM()
yr = YouRetriever()
cf_search = sw.Search()


search, chat_app = st.columns(2)

if prompt := chat_app.chat_input("What would you like me to search for?"):
    chat_app.chat_message("user").write(prompt)
    asyncio.run(cf_search.search_web_async(prompt))
    docs = yr.get_relevant_documents(prompt)
    search.write(docs)
    llm.embed_documents(docs)
    response = llm.generate_response(prompt)
    
    chat_app.chat_message("assistant").write(response)

