from re import search
import streamlit as st
import urllib
import requests #import the library that we use to make the http request

from _class_streamlit import streamlit_mytech
stm = streamlit_mytech(theme='cfdark')
stm.set_up_page(page_title_text="Library of Congress",
                session_state_variables=[], )


state_url=""
publisher_text = ""
subject_text = ""
state_text = ""
city_text = ""
date_text = ""
title_normal_text = ""
page_text = ""
protext_url =""


state_s = st.text_input("State",    "California", key="state_s",)
protext_s =st.text_input("Subject",    "", key="protext_s",)
start_year_s = st.text_input("Start Year",    1920, key="start_year_s",)
end_year_s = st.text_input("End Year",    1960, key="end_year_s",)

rows_s = 10
#make this string url safe using urllib.parse.quote
state_s = urllib.parse.quote(state_s)
protext_s = urllib.parse.quote(protext_s)


if state_s != "": state_url = f"state={state_s}"
if protext_s != "": protext_url = f"&protext={protext_s}"

search_url = f"http://chroniclingamerica.loc.gov/search/pages/results/?{state_url}{protext_url}&rows={rows_s}&sort=relevance&format=json"
print(search_url)
r = requests.get(search_url).json()
if st.button("Search"):
    st.write(f"Total Results: {r['itemsPerPage']}") #print out the number of items per page:

    for item in r['items']:
        if item.get('subject', []) != []:
            subject_text = f"Subject: {item['subject'][0].split('--')[0]}"
        if item.get('publisher', "") != "":
            publisher_text = f"Publisher: {item['publisher']}"
        if item.get('state', "") != "":
            state_text = f"State: {item['state'][0]}"
        if item.get('city', "") != "":
            city_text = f"City: {item['city'][0]}"
        if item.get('date', "") != "":
            date_text = f"Date: {item['date']}"
        if item.get('title_normal', "") != "":
            title_normal_text = f"{item['title_normal'].title()}"  
        if item.get('page', "") != "":
            page_text = f"Page: {item['page']}"
        
        st.markdown(f"### {title_normal_text}")
        st.markdown(f"#### {publisher_text} - {date_text} - {state_text} - {city_text} - {page_text}")
        st.write(item['url']) #print out the URL for each item
        text_col, image_col = st.columns([1, 1])
        orig_item = st.expander('Original Text', expanded = False)
        st.write(item.get('ocr_eng', ''))
        
        st.markdown(f"---")
    
    