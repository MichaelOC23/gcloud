import streamlit as st
import asyncio
import random


from _class_streamlit import streamlit_mytech
# stm = streamlit_mytech(theme='cfdark')
# stm.set_up_page(page_title_text="Meetings",
#                 session_state_variables=[{"TransStatus": False}], )

material_icons=['Save', 'Surfing', 'Sprint', 'Savings', 'Spa', 'Nightlife', 'Raven', 'Pets', 'Pool', 'Tibia', 'Skull']

from _class_firebase import FirestoreStorage
fire = FirestoreStorage()

header_dict = {
  "name": "Name", #"duration": "Duration", "created": "Date",
    #   "transcription_raw": "transcription_raw", #  #   "document_id": "Id",
    #   "speaker_names": "Speakers", "topics": "Topics", "summary": "Summary",
    #   "public_url": "public_url", #   "modified": "Modified", "modifiedon": "modifiedon", #   "createdon": "createdon", 
    }
if not 'transcription_records' in st.session_state:
    st.session_state["transcription_records"] = fire.get_transcription_records_sync()

df_leftnav = st.session_state['transcription_records'][['name','duration','summary','topics','createdon']]
# [['name'],['duration'],['summary'],['topics'],['createdon']]


def on_nav_grid_select():
    if len(st.session_state["nav_grid"].selection.rows) >0:
        nav_grid_row = st.session_state["nav_grid"].selection.rows[0]
        st.session_state["selected_document_id"] = st.session_state['transcription_records'].index[nav_grid_row]
    else:
        st.session_state['selected_document_id'] = None

lc2, lc3, lc4, lc5 = st.columns([1,1.5,.5,.5],gap="small", vertical_alignment="bottom")
edit_radio = lc2.radio("Edit", ["Select Meeting", "Edit Meeting"], horizontal=True, label_visibility="hidden")
search_box = lc3.text_input("Search", value="", key="search", label_visibility="hidden")
lc4.button("Search", use_container_width=True, key="search_button")
lc5.button("Clear", use_container_width=True, key="clear_button")

mode="select"
if edit_radio == 'Edit Meeting':
    mode="edit"
    st.data_editor(df_leftnav, 
                #  on_select=on_nav_grid_select,
                use_container_width=True, 
                hide_index=True, 
                height=min((len(st.session_state['transcription_records'])+1)*30,300), 
                key='nav_grid',
                #  selection_mode="single-row",
                )
else:
    mode="select"
    st.dataframe(df_leftnav, 
                on_select=on_nav_grid_select,
                use_container_width=True, 
                hide_index=True, 
                height=min((len(st.session_state['transcription_records'])+1)*30,300), 
                key='nav_grid',
                selection_mode="single-row",
                )



st.divider()
if 'selected_document_id' in st.session_state and st.session_state['selected_document_id'] is not None:
    doc = asyncio.run(fire.get_full_transcription(st.session_state["selected_document_id"]))
    try:
        st.markdown(f"#### :blue[Overall Sentiment:] {doc[1]['results']['sentiments']['average']['sentiment'].title()}")
    except: pass
    
    
    convo, summary, topics, transcriptions = st.tabs(['Conversation', 'Summary', 'Topics', 'Transcription'])
    
    # Conversation Tab
    words = doc[1].get('results', {}).get('channels', [])[0].get('alternatives', [])[0].get('words', [])
    prior_speaker = -1
    statements = []
    statement = ''
    for word in words:
        if prior_speaker == -1:
            prior_speaker = word.get('speaker', '')
            statement = f"{word.get('punctuated_word', '')}"
            continue
        
        if word.get('speaker', '') == prior_speaker:
            statement += f" {word.get('punctuated_word', '')}"
            continue
        
        if word.get('speaker', '') != prior_speaker:
            statements.append([f"Speaker {prior_speaker}", statement.strip()])
            prior_speaker = word.get('speaker', '')
            statement = f"{word.get('punctuated_word', '')}"
            continue
    
    
    
    convo.markdown(f"##### :blue[Transcription of:] {doc[0]['name']}")
    trans_chat = convo.container(border=True)

    random.shuffle(material_icons)
    speaker_list = []
    for speaker in statements:
        if speaker[0] not in speaker_list:
            speaker_list.append(speaker[0])
        index_of_speaker = speaker_list.index(speaker[0])
        
        trans_chat.chat_message(speaker[0],avatar=f":material/{material_icons[index_of_speaker].lower()}:").write(speaker[1])

    # Summary Tab
    summary_text = doc[0].get('summary', '')
    summary.markdown(summary_text)
    
    # Topics
    topics_items = doc[0].get('topics', [])
    topics.markdown(topics_items)
    

    