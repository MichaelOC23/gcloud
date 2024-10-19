import sys
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

from sqlalchemy import column
import streamlit as st
from bs4 import BeautifulSoup
import sys

st.set_page_config(layout="wide")


# st.header("product-test", divider="red" )
# # Simulate input parameters
# parameter_1 = "Charlie's"
# parameter_2 = "Angels"

# if st.button("product-test", "product-test"):

# #?#############################################

#     result = ""

#     try: 
#         import os
        
#         def test_function(value_1, value_2):
        
#             current_directory = os.getcwd()
#             return (f"{value_1} {value_2} {current_directory}")

#         result = test_function(parameter_1, parameter_2)
#     except Exception as e:
#         result = f"Error Occurred [Error Message: {e}]"
#         print(result)

# #?#############################################
    
#     st.write(result)
    






st.header("RSS NextGen Plugin Function")
st.write("Click any row below to see the RSS.")
#Blue Divider
st.divider()
# Simulate input parameters

source_list = None

#if st.button("RSS-Plugin", "RSS-Plugin"):

#?#############################################
import json
from datetime import datetime
import re
import os
import feedparser
from bs4 import BeautifulSoup, NavigableString

result = ''
if source_list is None:
    source_list = [
    {
    "name":"Financial Times",
    "url":"https://www.ft.com/",
    "logo":"https://www.ft.com/__origami/service/image/v2/images/raw/ftlogo-v1%3Abrand-ft-logo-landscape-coloured-inverse?source=image-url-builder",
    "feed_url":"https://www.ft.com/myft/following/1f5bb351-6628-4cd7-b33f-54b4e0112edc.rss"
    }
    ,{
    "name":"Wall Street Journal",
    "url":"https://www.wsj.com/",
    "logo":"https://1000logos.net/wp-content/uploads/2019/11/The-Wall-Street-Journal-emblem.png",
    "feed_url":"https://feeds.a.dj.com/rss/RSSWSJD.xml"
    }
    ]
def get_image_urls_from_text(text, add_to_list = None, image_type_list = None):
    try: 
        if add_to_list is None:
            add_to_list = []
        
        if image_type_list is None:
            image_type_list = ['jpg', 'jpeg', 'png', 'gif']

        for image_type in image_type_list:
            # Regular expression pattern to match a URL ending in .jpg
            pattern = r'https?://[^\s]+\.' + image_type

            # Search for the pattern in the string
            match = re.search(pattern, text)
            for match in re.findall(pattern, text):
                add_to_list.append(match)
        
        return add_to_list
    except:
        return []


def extract_text_from_html(html):
        try:
            soup = BeautifulSoup(html, 'html.parser')
            img_tag = soup.find('img')
            desired_text = ""
            if img_tag and isinstance(img_tag.next_sibling, NavigableString):
                desired_text = img_tag.next_sibling.strip()
                return desired_text
        except:
            return ""
    
def transform_json(original_json, source):
    # Flatten the feed entries and append to the provided list (if provided)
    def get_dict_val(entry, field_l1, field_l2 = None):
        try:
            if field_l2 is None:
                field_value = entry[field_l1]
            else:
                field_value = entry[field_l1][field_l2]
            return field_value
        except:
            print(f"Could not get value for field(s): l1:{field_l1}: l2:{field_l2}")
            return ""
    
    transformed_data = {"entries": []}

    for entry in original_json["entries"]:
        
        #Title is the title field
        title =  get_dict_val(entry, 'title')
        
        # link to the article is the link field
        link =  get_dict_val(entry, 'link')
        
        #stripped the summary text of html tags
        summary_text =  extract_text_from_html(get_dict_val(entry, 'summary'))
        
        #id
        id = get_dict_val(entry, 'id')
        
        #published date is the published_parsed field
        try:
            published_date = datetime(*entry["published_parsed"][:6]).isoformat()
        except:
            published_date = datetime.now().isoformat()
            pass
        
        #tags are the terms in the tags field
        try: 
            tags = [tag.get("term") for tag in entry.get("tags", [])]
        except:
            tags = []
            pass
        
        # topic name is the first tag
        if len(tags) > 0:
            topic_name = tags[0]
        else:
            topic_name = ""

        # Get the image urls from the summary text
        # the images may be separately useful ... pulling them out into their own field
        img_list = []
        img_list = get_image_urls_from_text(entry["summary"])
        if len(img_list) > 0:
            image = img_list[0]
        else:
            image = source['logo']


        # Building the transformed entry
        transformed_entry = {
            "title": title,
            "summary": summary_text,
            "topic": {
                "name": topic_name,
                "url": link
            },
            "image": image,
            "link": link,
            "id": id,
            "tags": tags,
            "published": published_date,
            "source": source
        }

        transformed_data["entries"].append(transformed_entry)
        #transformed_data["source"] = { "name": "Financial Times", "url": "https://www.ft.com/", "logo":"https://www.ft.com/__origami/service/image/v2/images/raw/ftlogo-v1%3Abrand-ft-logo-landscape-coloured-inverse?source=image-url-builder"}

    return transformed_data

def fetch_and_transform_feed(source):
    f_url = source['feed_url']
    feed = feedparser.parse(source['feed_url'])
    feed_json = transform_json(feed, source)
    return feed_json

feed_items = None

for source in source_list:
    try:
        source_result = fetch_and_transform_feed(source)
    except Exception as e:
        print(f"Error fetching feed for source: {source['name']}")
        print(f"Error Message: {e}")
        pass

    if feed_items is None or len(feed_items) == 0:
        feed_items = source_result['entries']
    else:
        feed_items.extend(source_result['entries'])


#?#############################################
    
def on_row_selected_RSS(event):
    st.write(event)    

# Get the directory of the current script
current_script_directory = os.path.dirname(os.path.abspath(__file__))

# Get the parent directory
parent_directory = os.path.dirname(current_script_directory)

# Add the parent directory to sys.path
sys.path.append(parent_directory)

import pandas as pd
import functions_aggrid as aggrid
#? Page Level Code
st.header('AG Grid RSS Feed', divider="blue")

# Turn them into a dataframe / grid
feed_dataframe = pd.DataFrame(feed_items)
grid_return = aggrid.get_grid(dataframe=feed_dataframe, row_selection=True, on_row_selected=on_row_selected_RSS)


# if clicked
if 'selected_rows' in grid_return and len(grid_return['selected_rows']) > 0:
    st.write(grid_return['selected_rows'])
    # import streamlit.components.v1 as components
    # components.html(grid_return['selected_rows'][0]['summary'], height=700, scrolling=True)





