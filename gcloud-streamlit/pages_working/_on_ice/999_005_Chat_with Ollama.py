

from hmac import new
import random
import time
import streamlit as st
from ollama import chat


st.title("Simple chat")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    
    # Add user message to chat history
    new_message = {"role": "user", "content": prompt}
    st.session_state.messages.append(new_message)
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        assistant_response = chat('llama2', messages=st.session_state.messages)
        
        full_response = ""
        # Simulate stream of response with milliseconds delay
        for part in chat('llama2', messages=messages, stream=True):
            print(part['message']['content'], end='', flush=True)
        for chunk in assistant_response.split():
            full_response += chunk + " "
            # time.sleep(0.05)
            # Add a blinking cursor to simulate typing
            message_placeholder.markdown(full_response + "▌")
        
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})