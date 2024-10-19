
import requests
import json
import os
import streamlit as st
from enum import Enum
from sympy import comp, content
from datetime import datetime
import functions_constants as constants
import dow_jones as dj
import streamlit as st
from enum import Enum
from sympy import comp, content
from datetime import datetime
import functions_constants as constants
import dow_jones as dj

# The following code is from the Dow Jones API documentation:
# Dow Jones Newswires Real-Time API Documentation. https://developer.dowjones.com/site/docs/newswires_apis/dow_jones_newswires_real_time_api/index.gsp
# Newswires API Certification Documentation.https://developer.dowjones.com/site/docs/newswires_apis/certification_process/index.gsp
# Authentication and Authorization details. https://developer.dowjones.com/site/docs/quick_start/authenticating_into_dowjones/index.gsp

# if connect_to_dj:
#             initialize_session_state_variable("djsession", None)
#             initialize_session_state_variable("djtoken", {})
#             initialize_session_state_variable("djtoken_status_message", "") 
#             initialize_session_state_variable("search_result_cache", "") 
#             initialize_session_state_variable("viewed_article_cache", "") 
#             initialize_session_state_variable("show_results", False)
#             initialize_session_state_variable("show_article", False) 
#             initialize_session_state_variable("chat_has_started", False)
#             initialize_session_state_variable("show_search_results", False)
#             initialize_session_state_variable("current_search_summary", "")

#!Setup
def UNIQUE_DATE_TIME_STRING(): 
	return datetime.now().strftime("%Y%m%d.%H%M%S") #note this is unique to the second i.e. per run
unique_id = constants.UNIQUE_DATE_TIME_STRING()

# Use the full screen width
st.set_page_config(layout="wide")

# Set the title of the page
st.header('Dow Jones Real-Time Article Search', divider='gray')

# if an error message was reported in the session state, display it (from a prior page load)
if 'error_message' in st.session_state:
	st.error(st.session_state.error_message)
	st.session_state.error_message = None

#!Search
#Create a form to search for articles
with st.form(key='Search'):
	search_string = st.text_input('Search String', 'djn=p/pmdm')
	search_date_range = st.selectbox('Search Date Range', options=['Last30Days', 'Last6Months', 'Last12Months', 'Last24Months', 'Last36Months'], index=0, key=None)
	#clicking submit will run the search_content function 
	submit_button = st.form_submit_button(label='Search', on_click=dj.search_content)

#! Process the search results
# the dj.search_content function will store the search results in the session state
if 'search_result' not in st.session_state:
	exit()
# Get the search results (stored as text) from the session state
# Convert the search results to a dictionary
search_result = st.session_state.search_result
search_dict = json.loads(search_result)

# Save the search results to a file (for reference only, not used by the app)
with open('temp/dj_search_result.json', 'w') as f:
	json.dump(search_dict, f, indent=4)

def iterate_and_concatenate(data, target_keys, result=None):
	if result is None:
		result = []

	if isinstance(data, dict):
		for key, value in data.items():
			if key in target_keys:
				if isinstance(value, list):
					result.extend({key: value})
				else:
					result.append({key: value})
			iterate_and_concatenate(value, target_keys, result)
	elif isinstance(data, list):
		for item in data:
			iterate_and_concatenate(item, target_keys, result)

	return result

if not search_dict['data']:
	st.write('No results found')
else:
	search_items = search_dict['data']
	item_count = len(search_items)

#! Iterate through the search results
	for item in search_items:
		item_count -= 1
		#! Get the full article content
		content_item = dj.get_content_item(item['id'])
		content_dict = json.loads(content_item)
		with open(f'temp/dj_content_result_{unique_id}_{item_count}.json', 'w') as f:
			json.dump(content_dict, f, indent=4)


		# Usage
		value_keys = ['id', 'column_name', 'hosted_url', 
					'live_date', 'live_time','section_type', 'product', 
					'page','video_count', 'word_count', 'image_count', 'audio_count']

		# list_keys = ['authors', ['byline']['content'], ['copyright']['text']]

		complex_keys = ['key5', 'key6']

		complete_content = iterate_and_concatenate(content_dict, value_keys)
		if complete_content is None:
			st.error('No content found in article ... See content below')
		with st.expander('Article Content'):
			st.write(complete_content)


# article_dict['data']['attributes']['body'] #! LIST The body of the article. Main content will have to write case based assebly logic.

#? article_dict['data']['id'] #STRING The article ID
# article_dict['data']['attributes'] #LIST The attributes of the article (title, body, etc.) 
#? article_dict['data']['attributes']['authors'] #?LIST The authors of the article (iterate through items and create tags
#? article_dict['data']['attributes']['byline']['content'] #?LIST Location and names of the authors (iterate through items and append text values)
#? article_dict['data']['attributes']['column_name'] #STRING The column name of the article
#? article_dict['data']['attributes']['copyright']['text'] #STRING obligated to show this copyright
# article_dict['data']['attributes']['headline']['main']['text'] #STRING The headline of the article
# article_dict['data']['attributes']['headline']['deck']['content'] #STRING The sub-headline of the article (iterate through items and append text values)
#? article_dict['data']['attributes']['hosted_url'] #Link to the article

# article_dict['data']['attributes']['content_resources'] #!LIST The content resources of the article (iterate through items and create tags)

# article_dict['data']['meta']['language']['code'] #STRING The language of the article
# article_dict['data']['attributes']['live_date'] #STRING The date the article was published
# article_dict['data']['attributes']['live_time']

#? article_dict['data']['attributes']['section_type'] #World News
#? article_dict['data']['attributes']['product'] # WSJ.com
#? article_dict['data']['attributes']['page'] # World

# article_dict['data']['attributes']['publisher']['name']
# article_dict['data']['attributes']['section_name']['text']

# article_dict['data']['attributes']['summary']['headline']['main']['content'] #?LIST The summary of the article (iterate through items and append text values)  
# article_dict['data']['attributes']['summary']['body'] #?LIST The summary of the article (iterate through items and append text values)

# article_dict['data']['meta']['source']['name'] #STRING The source of the article

# article_dict['data']['meta']['keywords'] #?LIST The keywords of the article (iterate through items and create tags)
# article_dict['data']['meta']['code_sets'][0]['codes'] #?LIST The codes of the article (iterate through items and create tags)

# article_dict['data']['meta']['metrics']['video_count']
# article_dict['data']['meta']['metrics']['word_count']
# article_dict['data']['meta']['metrics']['image_count']
# article_dict['data']['meta']['metrics']['audio_count']
		





# def assemble_article(content_item):
# #! Get the article content
#	 article_dict = json.loads(content_item)
# if 'data' not in article_dict:
# 		return None

# #! The following are the key paths in the JSON Article file
# flat_article_dict = {
# 		'id': article_dict.get('data').get('id', ''),
# 		'body': article_dict.get('data', {}).get('attributes', {}).get('body', ''),
# 		#'authors': article_dict.get('data', {}).get('attributes', {}).get('authors', ''),
# 		#'byline_content': article_dict.get('data', {}).get('attributes', {}).get('byline', {}).get('content', ''),
# 		'column_name': article_dict.get('data', {}).get('attributes', {}).get('column_name', ''),
# 		'copyright': article_dict.get('data', {}).get('attributes', {}).get('copyright', {}).get('text', ''),
# 		'headline': article_dict.get('data', {}).get('attributes', {}).get('headline', {}).get('main', {}).get('text', ''),
# 		'sub_headline': article_dict.get('data', {}).get('attributes', {}).get('headline', {}).get('deck', {}).get('content', ''),
# 		'hosted_url': article_dict.get('data', {}).get('attributes', {}).get('hosted_url', ''),
# 		#'content_resources': article_dict.get('data', {}).get('attributes', {}).get('content_resources', []),
# 		'language_code': article_dict.get('data', {}).get('meta', {}).get('language', {}).get('code', ''),
# 		'live_date': article_dict.get('data', {}).get('attributes', {}).get('live_date', ''),
# 		'live_time': article_dict.get('data', {}).get('attributes', {}).get('live_time', ''),
# 		'section_type': article_dict.get('data', {}).get('attributes', {}).get('section_type', ''),
# 		'product': article_dict.get('data', {}).get('attributes', {}).get('product', ''),
# 		'page': article_dict.get('data', {}).get('attributes', {}).get('page', ''),
# 		'publisher_name': article_dict.get('data', {}).get('attributes', {}).get('publisher', {}).get('name', ''),
# 		'section_name': article_dict.get('data', {}).get('attributes', {}).get('section_name', {}).get('text', ''),
# 		#'summary_headline': article_dict.get('data', {}).get('attributes', {}).get('summary', {}).get('headline', {}).get('main', {}).get('content', ''),
# 		#'summary_body': article_dict.get('data', {}).get('attributes', {}).get('summary', {}).get('body', ''),
# 		'source_name': article_dict.get('data', {}).get('meta', {}).get('source', {}).get('name', ''),
# 		#'keywords': article_dict.get('data', {}).get('meta', {}).get('keywords', []),
# 		#'codes': article_dict.get('data', {}).get('meta', {}).get('code_sets', [{}])[0].get('codes', []),
# 		'video_count': article_dict.get('data', {}).get('meta', {}).get('metrics', {}).get('video_count', ''),
# 		'word_count': article_dict.get('data', {}).get('meta', {}).get('metrics', {}).get('word_count', ''),
# 		#'image_count': article_dict.get('data', {}).get('meta', {}).get('metrics', {}).get('image_count', ''),
# 		#'audio_count': article_dict.get('data', {}).get('meta', {}).get('metrics', {}).get('audio_count', '')
# }
# return flat_article_dict