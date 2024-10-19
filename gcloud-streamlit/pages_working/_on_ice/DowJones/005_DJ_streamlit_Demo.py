import streamlit as st
from streamlit_option_menu import option_menu
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import time

import classes._class_dow_jones as dowjones
import classes._class_streamlit as st_setup
import classes._class_storage as _storeage

store = _storeage._storage()
if "subpage" not in st.session_state:
    st.session_state.subpage = "Overview"


       
def apply_html_style(text_to_style, style_name="body-text-html", URL_Link="", color="black"):
    
    style_dict = {

        "article-page-title-html": f"<div style='font-size: 48px; line-height: 1.08349; font-weight: 700; letter-spacing: -.003em; font-family: 'SF Pro Display', 'SF Pro Icons', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;'>{text_to_style}</div>",
        "article-search-result-title-html": f"<div style='font-size: 19px; line-height: 1.21053; font-weight: 100; letter-spacing: .012em; font-family: 'SF Pro Display', 'SF Pro Icons', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;'>{text_to_style}</div>",
        "subsubheader": f"<div style='font-size: 22px;color: #06c; line-height: 1.21053; font-weight: 100; letter-spacing: .012em; font-family: 'SF Pro Display', 'SF Pro Icons', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;'>{text_to_style}</div><br>",
        "article-type-html": f"<div style='margin-bottom: 8px; font-size: 14px; line-height: 1.33337; font-weight: 700; font-family: 'SF Pro Text', 'SF Pro Icons', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;'>{text_to_style}</div>",
        "search-result-title-html": f"<div style='font-size: 19px; line-height: 1.21053; font-weight: 700; letter-spacing: .012em; font-family: 'SF Pro Display', 'SF Pro Icons', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif; overflow: hidden;'>{text_to_style}</div>",
        "article-date-html": f"<div style='margin-top: 8px; font-size: 16px; line-height: 1.28577; color: #09C7FD; font-weight: 300; letter-spacing: -.016em; font-family: 'SF Pro Text', 'SF Pro Icons', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif; display: flex; justify-content: flex-start; align-items: center;'>{text_to_style}</div>",
        "subheader-html": f"<div style='font-size: 19px; line-height: 1.21053; font-weight: 700; letter-spacing: .012em; font-family: 'SF Pro Display', 'SF Pro Icons', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;'>{text_to_style}</div>",
        "snippet-text-html": f"<div style='font-size: 16px; line-height: 1.4211; font-weight: 400; letter-spacing: .012em; font-family: 'SF Pro Display', 'SF Pro Icons', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;'>{text_to_style}</div>",
        "body-text-html": f"<div style='font-size: 19px; line-height: 1.4211; font-weight: 400; letter-spacing: .012em; font-family: 'SF Pro Display', 'SF Pro Icons', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;'>{text_to_style}</div>",
        "image-caption-html": f"<div style='position: relative; display: flex; align-items: flex-start; justify-content: space-between; margin: 16px 16px 0; font-size: 12px; line-height: 1.33337; font-weight: 600; letter-spacing: -.01em; font-family: 'SF Pro Text', 'SF Pro Icons', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;'>{text_to_style}</div>",
        "caption-header-html": f"<div style='font-size: 14px; line-height: 1.42859; font-weight: 400; letter-spacing: -.016em; font-family: 'SF Pro Text', 'SF Pro Icons', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;'>{text_to_style}</div>",
        "link_html": f"<a href='{URL_Link}' style='text-decoration: none; color: #06c; letter-spacing: inherit;'>{text_to_style}</a>",
        # "icon_html": f"<span style='font-family: 'social-media-font';'>{text_to_style}</span>",
        "chip_html": f"<span style='display: inline-block; margin: -4px; height: auto;'><div style='background-color: #7D55C7; color: #fff; width: auto; margin: -4px; font-size: 12px; line-height: 1.33337; font-weight: 700; letter-spacing: -.01em; font-family: &quot;SF Pro Text&quot;, &quot;SF Pro Icons&quot;, &quot;Helvetica Neue&quot;, &quot;Helvetica&quot;, &quot;Arial&quot;, sans-serif; padding: 5px 10px; border-radius: 15px; display: inline-block;'>{text_to_style}</div></span>"


    }
    return style_dict[style_name]
    

menu_dict = st_setup.setup_page("Dow Jones News and Content Demonstration")

def on_sub_menu_change(key):
    print(f"{st.session_state[key]} is the menu selection")
    
        

selected2 = option_menu(None, ["Overview", 
                                "Content Dashboard", 
                                "Search", 
                                "Search Conifgurations", 
                                'Other Features'], 
                        # icons=['house', 'cloud-upload', "list-task", 'gear'], 
                        on_change=on_sub_menu_change, 
                        key='sub_menu', 
                        orientation="horizontal",
                        default_index=0
                        # menu_icon="cast", 
                        # styles={
                        # "container": {"padding": "0!important", "background-color": "#fafafa"},
                        # "icon": {"color": "orange", "font-size": "25px"}, 
                        # "nav-link": {"font-size": "25px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
                        # "nav-link-selected": {"background-color": "green"},
                        # #See below for more options
                        # }
                        )



               
        
        
        # resp = asyncio.run(store.create_parameter("test_parameter", "test_value"))
        # st.write(f"Parameter created: {resp}")
        
        # resp = asyncio.run(store.get_one_parameter("test_parameter"))
        # st.write(f"Parameter retrieved: {resp}")
        
        
        # st.write(f"Deleting parameter")
        # resp = asyncio.run(store.delete_parameter("test_parameter"))
        # st.write(f"Parameter deleted: {resp}")
        
        
        
        # st.write(f"Uploading log")
        # resp = asyncio.run(store.upload_log("test_log", b"Hello, World!"))
        # st.write(f"Log uploaded: {resp}")
        # st.write(f"Getting recent logs")
        # log_list = asyncio.run(store.get_recent_logs())
        # log_df = pd.DataFrame(log_list)
        # st.write(log_df)
        # st.write(":green[All tests completed]")
        
       
         

        
        
        
        

        # apply_html_style("Parameters", "subsubheader")
        
        # st.markdown(":green[All Entities]")
        # all_df = pd.DataFrame(all_entities)
        # st.dataframe(all_df)

        # st.markdown(":red[Correct List of 4 Entities not found]")
        # st.markdown(f"##### :violet[Attempting to update the entities just created.{test_table}]")
        
        # st.markdown(f"Attempting to process the batch update : {test_table}")
        # result = await store.load_test_entity_update_batch(test_table, list_of_entities)
        # st.markdown("Entities batch has processed .... let's confirm and get all entities")
        # all_entities = await store.get_all_entities(test_table)
        # st.markdown(":green[All Entities]")
        # all_df = pd.DataFrame(all_entities)
        # st.dataframe(all_df)
        
        # st.markdown("##### :green[All tests completed]")

if st.session_state.get("subpage","") == "Overview" or st.session_state.get("subpage","") == "":
    content_list = [] #asyncio.run(store.get_all_entities(store.search_results_table_name))
    content_df = pd.DataFrame(content_list)
    st.dataframe(content_df, use_container_width=True, #hide_index=True,
                       column_config={
                            "PartitionKey": None,
                            "RowKey": None,
                            # "RowKey": st.column_config.Column(
                            #         "Name",
                            #         width='small',
                            #         required=True),
                            "parameter_value": st.column_config.Column(
                                    "Value",
                                    width="large",
                                    required=True,
            )})
    
    
   
    
if st.session_state.get("subpage","") == "Other Features":

    
    access_token_log, blob_log  = st.columns([1.5, 2])
    dj = dowjones.DJSearch()
    
    with access_token_log:
        st.markdown(apply_html_style("Access Token", "subsubheader"), unsafe_allow_html=True)

        token_str = dj.get_nearest_valid_authz_token()
        
        if token_str is not None:
            at_expand = st.expander(":green[Vaild]", expanded=False)
            at_expand.write(token_str)
        else:
            st.error(":red[Token is invalid].")
            st.write ('Stopping ...')
            st.stop()
        parameter_list = asyncio.run(store.get_all_entities(store.access_token_table_name_and_keys))
        param_df = pd.DataFrame(parameter_list)
        st.dataframe(param_df, use_container_width=True, hide_index=True,
                       column_config={
                            "PartitionKey": None,
                            "RowKey": None,
                            # "RowKey": st.column_config.Column(
                            #         "Name",
                            #         width='small',
                            #         required=True),
                            "parameter_value": st.column_config.Column(
                                    "Value",
                                    width="large",
                                    required=True,
            )})
        
        
        st.markdown("---")
        st.markdown(apply_html_style("Database Connection", "subsubheader"), unsafe_allow_html=True)

        IsValid = asyncio.run(store.validate_connection_string())
        if IsValid:
            st.markdown(f"Table Connection string is :green[Valid].", unsafe_allow_html=True)
        else:
            st.markdown(f"Connection string is :red[Invalid].", unsafe_allow_html=True)
            st.write ('Stopping ...')
            st.stop()
        
        st.markdown(apply_html_style("Accessible Tables", "subsubheader"), unsafe_allow_html=True)
        # Table Read Access
        table_names = asyncio.run(store.get_tables_names_as_markdown())
        st.markdown(table_names)
        
        # asyncio.run(store.get_all_entities("accesstoken"))
        

        # await store.process_entity(table_name=store.parameter_table_name, entity=entity, instruction_type="UPSERT_MERGE")
        st.markdown(apply_html_style("Configuration Variables", "subsubheader"), unsafe_allow_html=True)

        def upsert_parameter(param_df):
            print("Uncomment the below for parameter management")
            # updated_dict = st.session_state.get("param_df", {}) 
            # if updated_dict != {} and updated_dict.get("edited_rows", {}) != {}:  
            #     for key in updated_dict.get("edited_rows", {}).keys():
            #         old_param_name = param_df[key][1]
            #         new_param_name= updated_dict.get("edited_rows", {}).get(key).get("RowKey")
            #         row = updated_dict.get("edited_rows", {}).get(key)
            #         # asyncio.run(store.create_parameter(row["RowKey"], row["parameter_value"]))
            #         return
            #     asyncio.run(store.create_parameter(row["RowKey"], row["parameter_value"]))
            #     return
            # # if updated_dict == {}:
            # # # param_df.values = updated_dict
            # # st.write("Updated Data:", f"{updated_dict}")

            for index, row in param_df.iterrows():
                st.success(f"Parameter {row['RowKey']} updated.")

        parameter_list = asyncio.run(store.get_all_parameters())
        param_df = pd.DataFrame(parameter_list)
        st.data_editor(param_df, use_container_width=True, hide_index=True, key="param_df", on_change=upsert_parameter(param_df),
                       column_config={
                            "PartitionKey": None,
                            "RowKey": st.column_config.Column(
                                    "Name",
                                    width='small',
                                    required=True),
                            "parameter_value": st.column_config.Column(
                                    "Value",
                                    width="large",
                                    required=True,
            )})
        
    with blob_log:    
        log_blob_list = asyncio.run(store.get_blob_list(store.log_container_name, 20))
        st.dataframe(log_blob_list)
        