
import streamlit as st
import classes._class_dow_jones as djclass
import classes._class_streamlit as cs

dj = djclass.DJSearch()
dj.connect()


cs.set_up_page(page_title_text="Article Formatting Test", jbi_or_cfy="jbi", light_or_dark="dark",session_state_variables=[], connect_to_dj=False)

articles = dj.get_test_rich_articles()
for article in articles:
    st.divider()
    html_dict = article.get('html', []) #dict is sequeced for article display
    for key in html_dict.keys():
        html_list = html_dict.get(key)
        for html in html_list:          #value of each node is a list of html strings
            if 'html_list' in key:
                continue
            if 'image' in key:
                html_out = html.get('html', '')    
                st.markdown(html_out, unsafe_allow_html=True)
            else:
                st.markdown(html, unsafe_allow_html=True)


 

