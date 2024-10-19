import requests
import os
import streamlit as st
from openai import OpenAI
import json
import requests
# from googlesearch import search
# from _class_search_google import search as image_search
from _class_search_google import GoogleSearch

from langchain.retrievers.you import YouRetriever

import streamlit as st
import classes._class_streamlit as st_setup

menu_dict = st_setup.setup_page("Search")




yr = YouRetriever()
from IPython.display import display

# from googlesearch import search
# search("Google")


def show_json(obj):
    display(json.loads(obj.model_dump_json()))

def get_assistants_list():
        
    # Make sure you have your OpenAI API key stored in an environment variable named OPENAI_API_KEY.
    # Alternatively, you can directly assign your API key as a string to the variable api_key (not recommended for production).
    api_key = os.getenv('OPENAI_API_KEY')

    # API endpoint
    url = "https://api.openai.com/v1/assistants?order=desc&limit=20"

    # Headers including the API key and content type
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "OpenAI-Beta": "assistants=v1"
    }

    # Making the GET request
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Convert the response to JSON and print it
        data = response.json()
        print("Success:", data)
    else:
        # Print error message
        print("Failed to retrieve data. Status code:", response.status_code, "Reason:", response.reason)
    return data.get('data')

assistant_id = "asst_jUdu8qQJ9rZqbJTmnI7WKU01"

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# assistant = client.beta.assistants.create(
#     name="Math Tutor",
#     instructions="You are a personal math tutor. Answer questions briefly, in a sentence or less.",
#     model="gpt-4-1106-preview",
# )


def submit_message(assistant_id, thread, user_message):
    client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=user_message
    )
    return client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
    )


def get_response(thread):
    return client.beta.threads.messages.list(thread_id=thread.id, order="asc")

# show_json(assistant)

# st.dataframe(get_assistants_list())



def get_ai_snippets_for_query(query):
    headers = {"X-API-Key": "0ed789ae-9296-404f-ab4b-e13bdb8e1fe1<__>1OQbcUETU8N2v5f4N6cpKDUg"}
    params = {"query": query}
    return requests.get(
        f"https://api.ydc-index.io/news?q={query}",
        params=params,
        headers=headers,
    ).json()


def google_search_web():

    ydc_col, google_col = st.columns(2)
    search_string = "Tim Gokey Broadridge"
    with ydc_col:
        ydc_list = []
        for doc in yr.get_relevant_documents(search_string):
            ydc_list.append(doc.page_content)
        st.dataframe(ydc_list)
        
        
    # st.dataframe(yr.get_relevant_documents(search_string))

    # with google_col:
    #     google_list = []
    #     search_result = image_search(search_string, advanced=True)
    #     for result in search_result:
    #         google_list.append([result.title, result.description, result.url])
    #     st.dataframe(google_list)
    #     # google_list = []
    #     # search_result = search(search_string, advanced=True)
        # for result in search_result:
        #     google_list.append([result.title, result.description, result.url])
        # st.dataframe(google_list)


search_results = GoogleSearch("Tim Gokey Broadridge")
sr = search_results.search()
print(sr)

# results = get_ai_snippets_for_query("Tim Gokey Broadridge")
# st.write(results)




exit()

def create_thread_and_run(user_input):
    thread = client.beta.threads.create()
    run = submit_message(assistant_id, thread, user_input)
    return thread, run


# Emulating concurrent user requests
thread1, run1 = create_thread_and_run(
    "I need to solve the equation `3x + 11 = 14`. Can you help me?"
)
thread2, run2 = create_thread_and_run("Could you explain linear algebra to me?")
thread3, run3 = create_thread_and_run("I don't like math. What can I do?")



import time

# Pretty printing helper
def pretty_print(messages):
    print("# Messages")
    for m in messages:
        print(f"{m.role}: {m.content[0].text.value}")
    print()


# Waiting in a loop
def wait_on_run(run, thread):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run


# Wait for Run 1
run1 = wait_on_run(run1, thread1)
st.write(get_response(thread1))

# Wait for Run 2
run2 = wait_on_run(run2, thread2)
st.write(get_response(thread2))

# Wait for Run 3
run3 = wait_on_run(run3, thread3)
st.write(get_response(thread3))

# Thank our assistant on Thread 3 :)
run4 = submit_message(assistant_id, thread3, "Thank you!")
run4 = wait_on_run(run4, thread3)
st.write(get_response(thread3))