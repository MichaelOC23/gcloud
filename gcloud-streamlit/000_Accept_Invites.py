import streamlit as st
# from _class_streamlit import streamlit_mytech   
# stm = streamlit_mytech("Meeting Acceptance", auth=True)
    
if st.button('Accept'):
    from _class_o365_communify import MS_GraphAPI
    o365 = MS_GraphAPI()
    st.session_state['log'] = o365.process_meeting_invites()

if 'log' in st.session_state:
    for item in st.session_state['log']:
        st.markdown(f'- {item}' )
        