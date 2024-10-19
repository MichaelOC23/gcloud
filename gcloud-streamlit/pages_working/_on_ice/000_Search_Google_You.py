

from googleapiclient.discovery import json
import streamlit as st
import time
from urllib.parse import urlparse
from openai import chat
from langchain.retrievers.you import YouRetriever
import asyncio
# from classes.MyTechBackground import scrape
import classes._class_search_web as sw
import classes._class_ollama as ol
import classes._class_streamlit as cs
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

cs.set_up_page(page_title_text="Web Search with RAG", jbi_or_cfy="jbi", light_or_dark="dark", 
    session_state_variables=[],
    connect_to_dj=False)



#!  #####   Streamlit App   #####
#*  #############################
#*  ######   PAGE HEADER   ######
#*  #############################    


cf_search = sw.Search()

if not "MODE" in st.session_state:
    st.session_state['MODE'] = "DEFINE_SEARCH"

if "SEARCH_QUERY" not in st.session_state:
    st.session_state["SEARCH_QUERY"] = []
    
if not "person_title" in st.session_state:
    st.session_state['person_title'] = ""
if not "company_name" in st.session_state:
    st.session_state['company_name'] = ""
if not "company_location" in st.session_state:
    st.session_state['company_location'] = ""
if not "SEARCH_RESULTS" in st.session_state:
    st.session_state['SEARCH_RESULTS'] = ""



message = st.empty()


def execute_google_search():
    st.session_state["person_title_value"] = st.session_state["title_field"]
    st.session_state["company_name_value"] = st.session_state["company_name_field"]
    st.session_state["company_location_value"] = st.session_state["company_location_field"]
    st.session_state["company_url_value"] = st.session_state["company_url_field"]

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
    # Create a form to get the search query
    new_person = st.form(border=True, clear_on_submit=True, key="new_person")
    
    #Create the columns for the fields
    tc, cc, lc, uc = new_person.columns([1,1,2,2])
    
    #Define the fields
    title = tc.text_input("Title", key="title_field").strip()
    company = cc.text_input("Company", key="company_name_field").strip()
    location = lc.text_input("Location", key="company_location_field").strip()
    url = uc.text_input("URL", key="company_url_field").strip()
    
    submit = new_person.form_submit_button("Submit")
    if submit:
        st.session_state["MODE"] = "EXECUTE_SEARCH"
    
    title="Founder"
    company="HUTNER CAPITAL MANAGEMENT INC."
    location="MANCHESTER, VT"
    url="HTTPS://WWW.HUTNERCAPITAL.COM"
     
Titles_List = [
    # "Founder",
    # "Managing Partner",
    # "Chairman",
    # "Chief Executive Officer (CEO)"
    "Wealth Management CEO",
    "Head of Wealth Management",
    # "Head of Private Banking",
    # "Head of Client Services",
    # "Head of Client Relations",
    # "Head of Client Experience",
    # "Head of Client Engagement",
    # "Head of Client Success",
    # "Chief Investment Officer (CIO)",
    # "Chief Financial Officer (CFO)",
    # "President",
    # "Managing Director",
    # "Partner",
    # "Executive Vice President (EVP)",
    # "Chief Strategy Officer (CSO)",
    # "Regional Managing Director",
    "Principal"
]
Test_Companies = [
    # {"Company":"", "Location":""},
    # {"Company":"", "Location":""},
    # {"Company":"", "Location":""},
    # {"Company":"", "Location":""},
    {"Company":"RBC Wealth Management", "Location":"Canada"},
    ]


def get_prompt(PersonTitle, Company):
    prompt = ''' {

            "Instructions": [
                "Below is an Example_JSON_Data_Record for a contact at a wealth management firm. Use the Example_JSON_Data_Record as a guide to populate the Empty_JSON_Data_Template with information about the person holding the RoleTitle specified in the Empty_JSON_Data_Template.",
                "Use only the information provided with this prompt. Do not use any external sources. If you are not able to populate a value, leave it as an empty string.",
                "Return only the Empty_JSON_Data_Template in your response. Do not return any other commentary or text. Your response is being systematically integrated and the assumption is that the Empty_JSON_Data_Template is the only output of your code.",
                "Your response must be in valid JSON format beginning with: {\"Contact_JSON_Data\": {<The template you populate>} }"
            ],
            "Example_and_Template": {
                "Example_JSON_Data_Record": {
                    "RoleTitle": "Chief Investment Officer (CIO)"
                    "PersonName": "John Doe",
                    "Company": "XYZ Wealth Management",
                    "Email": "John@xyzwealth.com",
                    "Phone": "555-555-5555",
                    "LinkedIn": "https://www.linkedin.com/in/johndoe",
                    "Background": "John Doe is the Chief Investment Officer at XYZ Wealth Management. He has over 20 years of experience in the financial services industry and specializes in investment management and portfolio construction. John holds a CFA designation and is a graduate of the University of ABC with a degree in Finance. He is passionate about helping clients achieve their financial goals and is committed to providing personalized investment solutions tailored to their needs.",
                    "PhotoURLs": ["https://www.xyzwealth.com/johndoe.jpg", "https://www.xyzwealth.com/johndoe2.jpg"],
                    "Location": "New York, NY",
                    "Interests": ["Cars", "Golf", "Travel"],
                    "OtherInfo": ["John is an avid golfer and enjoys spending time with his family and friends.", "He is also a car enthusiast and loves to travel to new destinations."]
                },
                
                "Empty_JSON_Data_Template": {
                    "RoleTitle": " ''' + PersonTitle + ''' ",
                    "PersonName": "",
                    "Company": " ''' + Company + ''' ",
                    "Email": "",
                    "Phone": "",
                    "LinkedIn": "",
                    "Background": "",
                    "PhotoURLs": ["", ""],
                    "Location": "",
                    "Interests": ["", "", ""],
                    "OtherInfo": ["", "", ""]
                }
            }
            }

            Critical reminder: "Your response must be in valid JSON format beginning with: 
            {
                \"Contact_JSON_Data\": {<The populated template>}
            }'''
        
    return prompt

async def process_company(Company, Location):
    
    company_results = []
    
    for title in Titles_List:
        
        search_query = f'person {title} at {Company} in {Location}?'
        google_results = await cf_search.async_search_google(search_query)
        
        add_you_results = await cf_search.async_search_you_rag_content(search_query)
        
        for rslt in add_you_results:
            google_results.append(rslt)
        
        with open(f"{title}search_results.json", "w") as f:
            f.write(json.dumps(google_results, indent=4))
        
        company_results.append(google_results)
    
    return company_results

def scrape_single_url(search_result):
    def extract_text_from_html(html_body):
        soup = BeautifulSoup(html_body, 'html.parser')
        return soup.get_text(separator=' ', strip=True)

    def is_a_valid_url(may_be_a_url):
        try:
            result = urlparse(may_be_a_url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    url = search_result.get('Link', '')
    
    if url == "" or not is_a_valid_url(url):
        search_result['Page_Content'] = "Invalid or missing URL"
        return search_result
    
    else:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(url)
                page.wait_for_selector('body')
                body = page.content()
                body_text = extract_text_from_html(body)
                search_result['Page_Content'] = body_text
                
                return search_result
            
            except Exception as e:
                error_message = f"Error getting full webpage for {url}: {str(e)}"
                search_result['Page_Content'] = error_message
                return search_result
            
            finally:
                browser.close()

async def async_scrape_single_url_old(search_result):
    from pyppeteer import launch
    
    def extract_text_from_html(html_body):    
        soup = BeautifulSoup(html_body, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    
    def is_a_valid_url(may_be_a_url):
        try:
            result = urlparse(may_be_a_url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False  
    
    url = search_result.get('Link', '')
    
    if url == "" or not is_a_valid_url(url):
        search_result['Page_Content'] = "Invalid or missing URL"
        return search_result
    
    else:
        browser = None
        
        try:
            browser = await launch(headless=True)
            page = await browser.newPage()
            await page.goto(url)
            await page.waitForSelector('body')
            body = await page.content()
            body_text = extract_text_from_html(body)
            search_result['Page_Content'] = body_text
            
            return search_result
        
        except Exception as e:
            
            error_message = f"Error getting full webpage for {url}: {str(e)}"
            search_result['Page_Content'] = error_message
            return search_result
        
        finally:
            if browser:
                await browser.close()   
    
        
    
    step1_submit = tc.form_submit_button(label="Submit", type="primary", on_click=create_search_query, use_container_width=True) 

    if step1_submit:
        st.session_state["MODE"] = 'EXECUTE_SEARCH'

def format_search_execution():    
    
    #! Execute searches asynchrnously
    async def initial_search(): 
        search_tasks = []
        #add task for you.com rag search
        search_tasks.append(cf_search.async_search_you_rag_content(st.session_state['SEARCH_QUERY']))

        #add task for google search
        search_tasks.append(cf_search.search_google_async(st.session_state['SEARCH_QUERY']))
        
        #execute all tasks
        st.session_state["SEARCH_RESULTS"] = await asyncio.gather(*search_tasks)
        

    
    message.info(f"Search Query: {st.session_state['SEARCH_QUERY']}")
    
    #! Execute search
    asyncio.run(initial_search())
    
    st.session_state['MODE'] = 'REVIEW_SEARCH_RESULTS'
        
def format_for_review():
    pass
    st.write(st.session_state["SEARCH_RESULTS"])
    # search_results = asyncio.run(cf_search.get_stored_search_results(st.session_state['SEARCH_QUERY']))
    # st.subheader(f"Is this {st.session_state['person_title']}?", divider=True)
    
    # for item in search_results:
        
    #     res_cont = st.container(border=True)
    #     site_img_and_title_col, img_col, btn_discard_col, = res_cont.columns([7,1.5,1])
    #     site_img_and_title_col.markdown(f"""
    #     <div style="display: flex; align-items: start; width: 100%; padding: 0px; height: auto; margin-bottom: 5px;"> 
    #     <img src="{item['primary_site_image']}" style="width: 20px; height: auto; align: center; margin: 10px 10px 10px 0px;">  
    #     <a href='{item.get('result_url', '')}' style='text-decoration: none; font-size: 20px; margin: 3px 0px 0px 0px; color: #06c; font-weight: 600; letter-spacing: inherit;'>{item.get('result_name', '')}</a>
    #     </span></div>""", unsafe_allow_html=True)
    
    #     btn_discard_col.button("Discard", key=item['Orig_RowKey'])

    #     site_img_and_title_col.markdown(item['page_snippet'], unsafe_allow_html=True)
    #     if item['primary_result_image'] != "":
    #         img_col.image(item['primary_result_image'], width=100)    



#?  ####################################
#?  #######    SCREEN MODES    #########
#?  ####################################
if __name__ == '__main__':
    
    def main(company_results):
    
        llm_context_list = []
    
        for title in company_results:
            for result in title:            
                if isinstance(result, dict):
                    type = result.get('Type', '')   
                    if type == 'google':
                        llm_context_list.append(scrape_single_url(result))
                    else:
                        llm_context_list.append(result)
        return llm_context_list
                    
        
        
    if st.session_state["MODE"] == "DEFINE_SEARCH":
        format_for_search()
        
    

    if st.session_state["MODE"] == "EXECUTE_SEARCH":
        
        # format_search_execution()
        
        def test_function():
            for item in Test_Companies:
                company_results = asyncio.run(process_company(item["Company"], item["Location"]))
                llm_context_list = main(company_results)
                with open(f"{item['Company']}_results.json", "w") as f:
                    f.write(json.dumps(llm_context_list, indent=4))
        test_function()

    if st.session_state["MODE"] == "REVIEW_SEARCH_RESULTS":
        format_for_review()

        
        
        # Run the asyncio event loop in the main thread


                