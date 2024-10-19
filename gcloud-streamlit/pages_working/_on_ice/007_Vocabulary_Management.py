from enum import unique
from itertools import count
from pipes import Template
import re

from numpy import full
import streamlit as st
import openpyxl
import pandas as pd
import os
import json

from sympy import div

st.set_page_config(layout="wide")
base_path = '/Volumes/code/vscode/cool-tools/'
vocab_path = os.path.join(base_path, "vocab/vocab-finance.txt")

full_vocab_list = []
def get_vocab():
    with open(vocab_path, 'r') as f:
        content = f.read().upper()
        content = content.replace('{', '').replace('}', '').replace("'", '').replace('\n', '').replace(' ', '') #Remove unnecessary characters
        content_list = content.split(',')
        # Convert the list into a set
        full_vocab_list = list(set(content_list))
        full_vocab_set = set(full_vocab_list)
        return full_vocab_list, full_vocab_set


st.header('Vocabulary Management', divider='gray')

add_col, remove_col = st.columns(2)


with add_col:
    st.subheader('Add Words to Vocabulary List', divider="green")
    add_word = st.text_input ('Add additional words, spearated by spaces, below',key='add_word', help='Enter words separated by spaces.')

    #strip out all punctionation and specaial characters except single quotes and spaces
    add_word = re.sub(r'[^\w\s\']', '', add_word)

    possible_words = add_word.split(' ')
    if st.button("Add Words"):
        full_vocab_list, full_vocab_set = get_vocab()
        for word in possible_words:
            if word.upper() in full_vocab_set:
                st.warning(f"The word '{word}' is already in the vocabulary list. No changes have been made.")
            else:
            
                if word.upper() not in full_vocab_set:
                    full_vocab_list.append(word.upper())
                    full_vocab_list = list(set(full_vocab_list))
                    full_vocab_list.sort()
                    with open(vocab_path, 'w') as f:
                        f.write(str(full_vocab_list))
                    st.write(f"Successfully added '{word}' to the vocabulary list")



with remove_col:
    st.subheader('Remove Words from Vocabulary List', divider="red")
    full_vocab_list, full_vocab_set = get_vocab()
    remove_word = st.text_input ('Enter words below, spearated by spaces, you would like removed.',key='remove_word', help='Enter words separated by spaces.')

    #strip out all punctionation and specaial characters except single quotes and spaces
    remove_word = re.sub(r'[^\w\s\']', '', remove_word)

    possible_words = remove_word.split(' ')
    if st.button("Remove Words"):
        for word in possible_words:
            if word.upper() not in full_vocab_set:
                st.warning(f"The word '{word}' is not in the Vocabulary List. There is nothing to remove.")
            else:
                item_index = full_vocab_list.index(word.upper())
                full_vocab_list.pop(item_index)
                with open(vocab_path, 'w') as f:
                    f.write(str(full_vocab_list))
                st.write(f"Successfully removed '{add_word}' from the vocabulary list" )
st.divider()

st.subheader('View Current Vocabulary List', divider="blue")
if st.button("View Vocabulary List"):
    st.caption(full_vocab_list)