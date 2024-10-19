from email import message
from re import S
import ollama
from sqlalchemy import values
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.header('Ollama Playzone', divider="red")

st.subheader('List of all functions in ollama', divider="red")
if st.button('List all Ollama Models'):
    for model in ollama.list().values():
        st.dataframe(model)

st.subheader('Models', divider="blue")


from ollama import chat

# question = st.text_input('Enter your question here')
# ask = st.button('Submit Simple')
prompt = st.chat_input("Say something")

if prompt:
    
    with st.chat_message("user"):
        st.write(f"{prompt}")

    if st.session_state.get('messages') is None:
        messages = [
            {
                'role': 'user',
                'content': prompt,
            },
            ]
    else:
        messages = st.session_state.get('messages')

        messages.append({
            'role': 'user',
            'content': prompt,
        })


    response = chat('llama2', messages=messages)
    with st.chat_message("ollama"):
        st.write(response['message']['content'])
    messages.append({
        'role': 'assistant',
        'content': response['message']['content'],
    })
    st.session_state.messages = messages
    # st.chat_input(messages=messages, placeholder='Type a message')
    # st.write(response['message']['content'])

    # if st.button('Submit Streaminng'):
