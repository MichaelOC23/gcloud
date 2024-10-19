import json
import os
import pandas as pd
import streamlit as st
import classes._class_streamlit as cs


cs.set_up_page(page_title_text="Code Analysis", jbi_or_cfy="jbi", light_or_dark="dark", 
    session_state_variables=[],connect_to_dj=False)


folder_or_file_path = 'articles'


#Get the list of files to process
all_code_sets = []
all_codes_dict = {
    'DJN': {},
    'DJID': {},
    }
djn_set = set()
if os.path.isdir(folder_or_file_path):
    file_list = os.listdir(folder_or_file_path)
    for file in file_list:
        #Check if the file is a json file
        if file.endswith('.json'):
            file_path = os.path.join(folder_or_file_path, file)
            with open(file_path, 'r') as f:
                try:
                    text = f.read()
                    text_dict = json.loads(text)
                    codes = text_dict.get('code_sets', {})
                    for key in codes.keys():
                        all_code_sets.append(codes[key])
                except:
                    print (f"Error reading file {file_path}")
    for code_block in all_code_sets:
        for code_record in code_block:
            scheme = code_record.get('code_scheme', {})
            
            
            if scheme == 'DJN':
                all_codes_dict['DJN'][code_record.get('code')]={}
                all_codes_dict['DJN'][code_record.get('code')].update(code_record)
                djn_set.add(code_record.get('code'))
            
            if scheme == 'DJID':
                all_codes_dict['DJID'][code_record.get('code')]={}
                all_codes_dict['DJID'][code_record.get('code')].update(code_record)

    
    with open('all_codes.json', 'wb') as f:
        f.write(json.dumps(all_code_sets).encode('utf-8'))
    with open('all_codes_dict.json', 'wb') as f:
        f.write(json.dumps(all_codes_dict).encode('utf-8'))
    with open('all_codes_dict.csv', 'wb') as f:
        f.write(pd.json_normalize(all_codes_dict).to_csv().encode('utf-8'))
        
    with open('djn_codes.csv', 'wb') as f:
        f.write(pd.DataFrame(djn_set).to_csv().encode('utf-8'))
    
    # normalized = pd.json_normalize(all_codes_dict)
    st.dataframe(djn_set)
    
    # st.dataframe(pd.DataFrame(all_codes_dict), use_container_width=True)
    
#     codes_df =[]
#     for key_scheme in all_codes_dict.keys():
#         for key in key_scheme.keys():
#             codes_df.append(key_scheme[key])
    
# st.dataframe(codes_df)
        
        