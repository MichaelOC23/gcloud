



import streamlit as st
import time
import asyncio
import classes._class_search_web as sw






#!  #####   Streamlit App   #####
#*  #############################
#*  ######   PAGE HEADER   ######
#*  #############################    


PAGE_TITLE = "Expand your community with Communify"
LOGO_URL = "https://devcommunifypublic.blob.core.windows.net/devcommunifynews/cfy-blk.png"

cf_search = sw.Search()

if not "MODE" in st.session_state:
    st.session_state['MODE'] = "DEFINE_SEARCH"

if "SEARCH_QUERY" not in st.session_state:
    st.session_state["SEARCH_QUERY"] = ""
    
if not "first_name_val" in st.session_state:
    st.session_state['first_name_val'] = ""
if not "last_name_val" in st.session_state:
    st.session_state['last_name_val'] = ""
if not "other_val" in st.session_state:
    st.session_state['other_val'] = ""



st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=":earth_americas:",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={
            'Get Help': 'mailto:michael@justbuildit.com',
            'Report a bug': 'mailto:michael@justbuildit.com',
            #'About': "# This is a header. This is an *extremely* cool app!"
            })

st.sidebar.title("Communify")


st.markdown(f"""
            <div style="display: flex; align-items: start; width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 5px; 
            height: 80px; background-color: lightblue; margin-bottom: 20px;"> 
            <img src="{LOGO_URL}" alt="{PAGE_TITLE}" style="width: 150px; height: auto; margin: 10px 15px 5px 0;">  
                                     <span style="flex: 1; font-size: 30px; margin: 0px 0px 10px 10px; 
                                     font-weight: 400; text-align: top; white-space: nowrap; 
  overflow: hidden; text-overflow: ellipsis;">{PAGE_TITLE}</span>  </div>
""", unsafe_allow_html=True)


message = st.empty()

    
def execute_google_search():
    st.session_state["first_name_val"] = st.session_state["first_name"]
    st.session_state["last_name_val"] = st.session_state["last_name"]
    st.session_state["other_val"] = st.session_state["other_details"]

def stream_text(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.02)

async def show_progress_bar(message="Processing", time_in_seconds=1):
    my_bar = st.progress(0, text=message)
    for percent_complete in range(100):
        await asyncio.sleep(0.01)
        my_bar.progress(percent_complete + 1, text=message)
    await asyncio.sleep(time_in_seconds)
    my_bar.empty()


def format_for_search():
    new_person = st.form(border=True, clear_on_submit=True, key="new_person")
    fn, ln, oth = new_person.columns([1,1,3])
    first_name = fn.text_input("First Name", key="first_name").strip()
    last_name = ln.text_input("Last Name", key="last_name").strip()
    other_details  = oth.text_input("Any other important details?", key="other_details").strip()
    step1_submit = fn.form_submit_button(label="Submit", type="primary", on_click=execute_google_search, use_container_width=True) 
    

    if step1_submit:
        if first_name == "" or last_name == "":
            s1_submit_text = f"""
            ###### :red[**Ummm . . .  not psychic . . . .  a name maybe?**]
            """
            message.write_stream(stream_text(s1_submit_text))
            time.sleep(1)

        else:
            st.session_state["MODE"] = 'EXECUTE_SEARCH'

def format_search_execution():
    def assemble_web_query(self, first_name, last_name, other_details=''):
        qry = f' ("{first_name} {last_name}" OR '
        qry+= f' ("{first_name}" AND "{last_name}")) '
        if other_details != "":
            qry+= f' AND ({other_details})'
        return qry
    
    s1_submit_text = f"""
        ###### Let's get started! We will have :blue[**{st.session_state["first_name_val"]} {st.session_state["last_name_val"]}**] added to your community in no time.
        """
    message.write_stream(stream_text(s1_submit_text))
    search_query = assemble_web_query(st.session_state["first_name_val"], st.session_state["last_name_val"], st.session_state["other_val"]).strip()
    st.session_state['SEARCH_QUERY'] = search_query.strip()

    #! Execute searches asynchrnously
    async def initial_search(): 
        s1_google_text = f"""Searching Communify for :blue[**{st.session_state["first_name_val"]} {st.session_state["last_name_val"]}**] . . . ."""
        search_tasks = []
        search_tasks.append(show_progress_bar(s1_google_text, 2))
        #! Below is the async google search
        search_tasks.append(cf_search.search_web_async(search_query))
        results = await asyncio.gather(*search_tasks)
        
        return results
    
    results = asyncio.run(initial_search())
    st.session_state['MODE'] = 'REVIEW_SEARCH_RESULTS'
        

def format_for_review():
    
    search_results = asyncio.run(cf_search.get_stored_search_results(st.session_state['SEARCH_QUERY']))
    st.subheader(f"Is this {st.session_state['first_name_val']}?", divider=True)
    
    for item in search_results:
        
        res_cont = st.container(border=True)
        site_img_and_title_col, img_col, btn_discard_col, = res_cont.columns([7,1.5,1])
        site_img_and_title_col.markdown(f"""
        <div style="display: flex; align-items: start; width: 100%; padding: 0px; height: auto; margin-bottom: 5px;"> 
        <img src="{item['primary_site_image']}" style="width: 20px; height: auto; align: center; margin: 10px 10px 10px 0px;">  
        <a href='{item.get('result_url', '')}' style='text-decoration: none; font-size: 20px; margin: 3px 0px 0px 0px; color: #06c; font-weight: 600; letter-spacing: inherit;'>{item.get('result_name', '')}</a>
        </span></div>""", unsafe_allow_html=True)
    
        btn_discard_col.button("Discard", key=item['Orig_RowKey'])

        site_img_and_title_col.markdown(item['page_snippet'], unsafe_allow_html=True)
        if item['primary_result_image'] != "":
            img_col.image(item['primary_result_image'], width=100)    



#?  ####################################
#?  #######    SCREEN MODES    #########
#?  ####################################


if st.session_state["MODE"] == "DEFINE_SEARCH":
    format_for_search()

if st.session_state["MODE"] == "EXECUTE_SEARCH":
    format_search_execution()

if st.session_state["MODE"] == "REVIEW_SEARCH_RESULTS":
    format_for_review()


 
            


# fire_and_forget("http://127.0.0.1:5000/search", params={"search_query": search_query})
#             requests.get(url, params=params)


    
    

