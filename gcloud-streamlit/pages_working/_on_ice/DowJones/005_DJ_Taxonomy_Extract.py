from importlib.metadata import files

from re import search
from unittest import result
from httpx import get
from networkx import dijkstra_predecessor_and_distance
from numpy import extract
import streamlit as st
import pandas as pd
import requests
import urllib.parse

import json
import classes._class_dow_jones as dj

import classes._class_streamlit as cs
cs.set_up_page(page_title_text="Communify: Dow Jones Taxonomy Search", jbi_or_cfy="jbi", light_or_dark="dark", 
    session_state_variables=[],
                            connect_to_dj=True) 

def get_dj_fixed_taxonomy():

    dj_fixed_taxonomy={
    
    
        # "Author": {
        #     "search": {
        #     "method": "GET",
        #     "endpoint": "/taxonomy/factiva-authors/search",
        #     "definition": "Retrieves a user-filtered collection of authors.",
        #     "category": "factiva-authors"
        #     }
        # },
        "Company": {
            "search": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-companies/search",
            "definition": "Retrieves a user-filtered collection of companies.",
            "category": "factiva-companies"
            }
        },
        "Language": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-languages",
            "definition": "Retrieves the full taxonomy of languages.",
            "category": "factiva-languages"
        },
        "Industry": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-industries",
            "definition": "Retrieves the full taxonomy of industries.",
            "category": "factiva-industries",
            # "children": {
            # "method": "GET",
            # "endpoint": "/taxonomy/factiva-industries/{id}/children",
            # "definition": "Retrieves the child industries of an industry, using its Factiva code.",
            # "category": "factiva-industries"
            # },
            "list": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-industries/list",
            "definition": "Retrieves the plain list of industries.",
            "category": "factiva-industries"
            },
            "lookup": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-industries/lookup",
            "definition": "Retrieves details of an industry using its Factiva code.",
            "category": "factiva-industries"
            },
            "search": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-industries/search",
            "definition": "Retrieves a user-filtered collection of industries.",
            "category": "factiva-industries"
            }
        },
        "Subject": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-news-subjects",
            "definition": "Retrieves the full taxonomy of news subjects.",
            "category": "factiva-news-subjects",
            # "children": {
            # "method": "GET",
            # "endpoint": "/taxonomy/factiva-news-subjects/{id}/children",
            # "definition": "Retrieves the children news subjects of a news subject, using its Factiva code.",
            # "category": "factiva-news-subjects"
            # },
            "list": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-news-subjects/list",
            "definition": "Retrieves the plain list of news subjects.",
            "category": "factiva-news-subjects"
            },
            "lookup": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-news-subjects/lookup",
            "definition": "Retrieves details of a news subject using its Factiva code.",
            "category": "factiva-news-subjects"
            },
            "search": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-news-subjects/search",
            "definition": "Retrieves a user-filtered collection of news subjects.",
            "category": "factiva-news-subjects"
            }
        },
        "Region": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-regions",
            "definition": "Retrieves the full taxonomy of regions.",
            "category": "factiva-regions",
            # "children": {
            # "method": "GET",
            # "endpoint": "/taxonomy/factiva-regions/{id}/children",
            # "definition": "Retrieves the child regions of a region, using its Factiva code.",
            # "category": "factiva-regions"
            # },
            "list": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-regions/list",
            "definition": "Retrieves the plain list of regions.",
            "category": "factiva-regions"
            },
            "lookup": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-regions/lookup",
            "definition": "Retrieves details of a region, using its Factiva code.",
            "category": "factiva-regions"
            },
            "search": {
            "method": "GET",
            "endpoint": "/taxonomy/factiva-regions/search",
            "definition": "Retrieves a user-filtered collection of regions.",
            "category": "factiva-regions"
            }
        },
        # "Source": {
        #     "children": {
        #     "method": "GET",
        #     "endpoint": "/taxonomy/factiva-sources/{id}/children",
        #     "definition": "Retrieves the child sources of a source, using its Factiva code.",
        #     "category": "factiva-sources"
        #     },
        #     "list": {
        #     "method": "GET",
        #     "endpoint": "/taxonomy/factiva-sources/{type}/list",
        #     "definition": "Retrieves the plain list of sources of a specified type.",
        #     "category": "factiva-sources"
        #     },
        #     "search": {
        #     "method": "GET",
        #     "endpoint": "/taxonomy/factiva-sources/search",
        #     "definition": "Retrieves a user-filtered collection of sources.",
        #     "category": "factiva-sources"
        #     },
        #     "title-search": {
        #     "method": "GET",
        #     "endpoint": "/taxonomy/factiva-sources/title/search",
        #     "definition": "Retrieves a user-filtered collection of titles from sources.",
        #     "category": "factiva-sources"
        #     }
        # }
        }
    return dj_fixed_taxonomy

def get_search_methods(taxonomy):
    tax = get_dj_fixed_taxonomy()
    cat_dict = {}
    got_string = False
    for sub_key in tax[taxonomy].keys():
        if isinstance(tax[taxonomy][sub_key], str) and not got_string:
            cat_dict['GET'] =  tax[taxonomy]['definition']
            got_string = True
        if isinstance(tax[taxonomy][sub_key], dict):
            cat_dict[sub_key] = tax[taxonomy][sub_key]['definition']
    return cat_dict

def get_suffix(search_term="", search_method="", language="en"):
    
    encoded_search_term = urllib.parse.quote_plus(search_term)

    suffix_dict = {
        "GET": f"?language={language}",
        "list": f"/list?language={language}&parts=All",
        "children": f"/{encoded_search_term}/children?language={language}&parts=All",
        "lookup": f"/lookup?filter.id={encoded_search_term}&language={language}&parts=All",
        "search": f"/search?filter.search_string={encoded_search_term}&language={language}",
        "title-search": "/title/search"
    }
    

    return suffix_dict[search_method]

def search_taxonomy(category=None, endpoint=None, child_endpoint_suffix="", API_Category="taxonomy", attempt=0):
    
    # https://api.dowjones.com/taxonomy/factiva-authors/search?filter.search_string=smith&language=en
    
    url = f"https://api.dowjones.com{API_Category}/{endpoint}{child_endpoint_suffix}"
    # result.write(f"E:https://api.dowjones.com/taxonomy/factiva-industries/list?language=en&parts=All")
    result.info(f"U:{url}")
    
    token = st.session_state.djtoken
    # Headers
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'}

    response = requests.get(url, headers=headers)

    if response.ok:
        return response.json()
    
    else:
        st.session_state.djtoken_status_message = f"Error: {response.status_code} - {response.text}"
        st.sidebar.write(st.session_state.djtoken_status_message)
        st.session_state.djtoken == {}
        if attempt < 2:
            return search_taxonomy(category, endpoint, child_endpoint_suffix, API_Category, attempt+1)
        else:
            st.stop()
        

search_end_col, result  = st.columns([.5, 1])
result.subheader("Taxonomy Search Results", divider=True)
with search_end_col:
    st.subheader("Extracts", divider=True)
    extract_all = st.button("Extract All", key="extract_all", type="primary", use_container_width=True)
    extract_progress = st.empty()
    
    
    st.subheader("Define Search", divider=True)
    
    full_tax = get_dj_fixed_taxonomy()
    tax_val = st.radio("Taxonomy", full_tax.keys(), key="taxonomy_radio", horizontal=True, index=0)
    search_methods = get_search_methods(tax_val)
    search_val = st.radio("Search Method", list(search_methods.keys()), key="search_radio113", horizontal=True, index=0)
    
    search_term = ""
    search_button = None
    if search_val in ['children', 'lookup', 'search']:
        search_term = st.text_input(f"Enter a value for {search_val}", value="", key="search_term", )
        search_button = st.button("Search", key="search_taxonomy", type="primary", use_container_width=True)
    
    if search_val in ['list']:
        search_button = st.button("Search", key="list_taxonomy", type="primary", use_container_width=True)
    
    if search_val in ['GET']:
        search_button = st.button("Search", key="nested_taxonomy", type="primary", use_container_width=True)

    suffix = get_suffix(search_method=search_val,search_term=search_term, language="en")
    
    if search_val not in ['GET']:
        endpoint = full_tax[tax_val][search_val]['category']
    else:
        endpoint = full_tax[tax_val]['category']
    
    tax =  get_dj_fixed_taxonomy()
    with st.expander("All Available Taxonomies", expanded=False):
        st.subheader("All Available Taxonomies", divider=True)
        for key in tax.keys():
            st.write(f"#### :blue[{key}]")
            cat_dict = get_search_methods(key)
            df = pd.DataFrame(list(cat_dict.values()), index=cat_dict.keys(), columns=['Values'])
            st.dataframe(df)

    
    if search_button:
        result.write(f"Searching for {search_term} ...")
        search_results = search_taxonomy(category = search_val,
                                         API_Category="/taxonomy", 
                                         endpoint= endpoint,
                                         child_endpoint_suffix=suffix)
        
        
        rexp = result.expander("Search Results (JSON)", expanded=False)
        rexp.write(search_results)
        
        
        #Format the results
        if search_val in ['GET'] and tax_val in ['Language', 'Industry', 'Region', 'Subject']:
            if tax_val == 'Language':
                result.dataframe(pd.DataFrame(search_results.get('data', {}).get('attributes', {}).get('languages', [])), 
                                     use_container_width=True, height=700)
        
        if search_val in ['search'] and tax_val in ['Company', 'Industry', 'Region', 'Subject']:
            if tax_val in ['Company']:
                result_dict={}
                for co in search_results.get('data', []):
                    result_dict[co.get('id', {})] = co.get('attributes', {})
                    result_dict[co.get('id', {})]['type'] = co.get('type', {})
                result.dataframe(pd.DataFrame(result_dict).T, use_container_width=True, height=700)
                    
        if search_val in ['list'] and tax_val in ['Industry', 'Region', 'Subject']:
            if tax_val in ['Industry']:
                result_dict={}
                for co in search_results.get('data', {}).get('attributes', {}).get('industries', []):
                    if result_dict.get(co.get('code', {}), {}) == {}:
                        # result_dict[co.get('code', {})] = co
                        result_dict[co.get('code', {})] = {}
                        result_dict[co.get('code', {})]['descriptor'] =  co.get('descriptor', '')
                        result_dict[co.get('code', {})]['description'] = co.get('description', '')
                        result_dict[co.get('code', {})]['is_active'] = co.get('code', {}).get('code_status', {}).get('is_active', False)
                        result_dict[co.get('code', {})]['is_visible'] = co.get('code', {}).get('code_status', {}).get('is_visible', False)
                        
                        
                        # result_dict[co.get('code', {})]['parent'] = json.dumps(co.get('parent', {}))
                        # result_dict[co.get('code', {})] = co
        
            
            if tax_val in ['Subject']:
                result_dict={}
                for co in search_results.get('data', {}).get('attributes', {}).get('news_subjects', []):
                    result_dict[co.get('code', {})] = co
                    result_dict[co.get('code', {})]['code-status'] = json.dumps(co.get('code_status', {}))
                    result_dict[co.get('code', {})]['parent'] = json.dumps(co.get('parent', {}))
            
            rexp_c = result.expander("Search Results (Custom JSON)", expanded=False)
            rexp_c.write(result_dict)
            result.dataframe(pd.DataFrame(result_dict).T, use_container_width=True, height=700)

            
            
            
                # result.dataframe(pd.DataFrame(search_results.get('data', {}).get('attributes', {}).get('languages', [])), 
                #                      use_container_width=True, height=700)

    if extract_all:
        full_tax = get_dj_fixed_taxonomy()
        i=0
        for tax_value in full_tax.keys():
            i+=1
            progress = (len(full_tax.keys())-i)/len(full_tax.keys())*100
            extract_progress.progress(0, f"Extracting ...{tax_value}")

            search_methods = get_search_methods(tax_value)
            for search_value in search_methods.keys():
                suffix = get_suffix(search_method=search_value,search_term=search_term, language="en")
                endpoint = ''
                if search_value in ['GET']:
                    endpoint = full_tax[tax_value][search_value]['category']
                if search_value in ['list']:
                    endpoint = full_tax[tax_value]['category']
                if endpoint != '':
                    extract_results = search_taxonomy(category = search_value,
                                            API_Category="/taxonomy", 
                                            endpoint= endpoint,
                                            child_endpoint_suffix=suffix)
                    with open(f"taxonomy_{tax_value}_{search_value}.json", "w") as outfile:
                        json.dump(extract_results, outfile)
                    
                
       
       
       
       
       
       
       
       
       
       
       

