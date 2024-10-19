import streamlit as st
import streamlit.components.v1 as components
import classes._class_streamlit as cs
import os
import ollama

cs.set_up_page(page_title_text="Local LLMs", jbi_or_cfy="jbi", light_or_dark="dark", 
    session_state_variables=[{"messages": [{"role": "assistant", "content": "Hi, I'm a chatbot who can search the web. How can I help you?"}]}],
    connect_to_dj=False)

b2_URL = "http://localhost:5011/"  # Replace with the URL of your Chainlit app
b7_URL = "http://localhost:5012/"  # Replace with the URL of your Chainlit app
mistral_URL = "http://localhost:5013/"  # Replace with the URL of your Chainlit app

# st.title("My Chainlit App in Streamlit")
if st.button('List all loaded Ollama Models'):
    for model in ollama.list().values():
        st.dataframe(model)

# Adjust the height as needed
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    st.subheader ("Gemma 2b")
    components.iframe(src=b2_URL, height=600) 

with col2:
    st.subheader ("Gemma 7b")
    components.iframe(src=b7_URL, height=600)

with col3:
    st.subheader ("Mistral 7b")
    components.iframe(src=mistral_URL, height=600)
    