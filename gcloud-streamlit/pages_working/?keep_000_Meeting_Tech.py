# Imports
from openai import audio
import streamlit as st
import os
import asyncio
import uuid


from classes._class_streamlit_header import streamlit_header as stc

stc.set_up_page(page_title_text="Meeting Tools", jbi_or_cfy="jbi", light_or_dark="dark", 
    session_state_variables=[{"TransStatus": False}]) 

from classes._class_streamlit import (
    deepgram_audio_transcription as de,
    PsqlSimpleStorage as pg,
    text_extraction as te,
    # transcription_library_crud as tlc
    )
# Set up the header for the page


    
#?############################################
#?#######     FORMAT SIDEBAR     #############
#?############################################

def format_sidebar():   
    pass


if __name__ == '__main__':
    
###################################
########     HEADER     ###########
###################################

    storage = pg()
    dg = de()
    te = te()

    #Format the Sidebar
    format_sidebar()

   
#####################################
#######     STREAMLIT BODY     ######
#####################################

    combined_extract_name = "-all-extracts.json"
    
    current_folder = os.path.dirname(__file__)  
    output_folder = os.path.join(current_folder, 'textextracts')
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    def get_files_from_upload(uploaded_files=None, save_directory=output_folder):
        file_path_list = []
        for uploaded_file in uploaded_files:
            # Check if the directory exists, if not, create it
            if not os.path.exists(save_directory):
                os.makedirs(save_directory)

            # Combine the directory with the uploaded file name
            file_path = os.path.join(save_directory, uploaded_file.name)
            file_path_list.append(file_path)

            # Write the uploaded file to the file system
            with open(file_path, "wb") as file:
                file.write(uploaded_file.getbuffer())

        return file_path_list   
            
    def extract_text_from_file_list(file_list, output_folder_path, extensions):  

        split_key = str(uuid.uuid4())
        
        #open combined file for split_key and plan to put each document in it as an array item
        json_str_start = "{" + f'"{split_key}":['
        
        with open(os.path.join(output_folder, f'{split_key}{combined_extract_name}'), 'a') as f:
            f.write(json_str_start)

        # Iterate through the file names and perform some action on each one
        for file in file_list:    
            if file.split('.')[-1] in extensions: 
                te.extract_json_from_files(file, output_folder_path, mode="appendasnew")
    
    def get_transcription_status():
        if 'audioinfo' not in st.session_state:
            st.session_state.audioinfo = {}
        
        return "FIX ME"
    
####################################
######     STREAMLIT BODY     ######
####################################
    tool_col1, tool_col2, tool_col3, tool_col4, tool_col5, tool_col6 = st.columns([1,1,1,.5,.5,.5])
    
    #File Text Extraction
    with tool_col1:
        file_expander = st.expander("File Transcription")
        with file_expander:
            file_expander.markdown(f"""##### Extract Text from Files""")        
            files = file_expander.file_uploader("Upload one or more files", type=te.all_types, accept_multiple_files=True, key="Upload_Files", )
            submit_button = file_expander.button(label="Extract text From file(s)", type="primary")
            if submit_button:
                # Nothing was uploaded
                if files is None: st.write("Please enter a folder path to continue.")
                    
                # Something was uploaded                    
                else:
                    # Confirm that the uploaded files are of the allowed types
                    if not isinstance(files, list):
                        files = [files]
                    
                    #get the list of file paths that were uploaded
                    file_path_list = get_files_from_upload(files, output_folder)
                    for file in file_path_list:
                        text_dict = te.extract_json_from_files(file, output_folder)
                        asyncio.run(storage.add_update_or_delete_some_entities(storage.transcription_table,[text_dict]))
                    st.success(f"File extraction complete.")
    
    # Youtube Text Extraction
    with tool_col2:
        
        youtube_expander = st.expander("Youtube Transcription")
        with youtube_expander:
            youtube_expander.markdown(f"""##### Extract Text from Youtube""")        
            url_youtube = youtube_expander.text_input("Enter Youtube URL to Transcribe", key="url_youtube", value = "https://www.youtube.com/shorts/rIkDIqTcc3w")
            if st.button("Transcribe Youtube URL", type="primary"):
                yt_transcript = dg.transcribe_youtube(url_youtube)
                youtube_expander.write(yt_transcript)
                asyncio.run(storage.add_update_or_delete_some_entities(storage.transcription_table,[yt_transcript]))
    
    #Deepgram
    if True:
        with tool_col3:
            channel_exp = tool_col3.expander("Select Channel")
            audio_list = dg.get_audio_device_list()
            channel_exp.radio("Select Audio Device", audio_list, key="audio_device")
        with tool_col5:
            if st.button("Start", type="primary", key="startaudiorec", use_container_width=True):
                dg.fire_and_forget('startaudiorec')
        with tool_col6:
            if st.button("Stop", type="primary", key="stopaudiorec", use_container_width=True):
                dg.fire_and_forget('stopaudiorec')
        with st.sidebar:
            if st.button("Info", type="secondary", key="audioinfo", use_container_width=True):

                audioinfo_dict = dg.get_audioinfo()
                inputnum = audioinfo_dict.get('config', {}).get('defaultInputDevice', -1)
                outputnum = audioinfo_dict.get('config', {}).get('defaultOutputDevice', -1)
                input_str = audioinfo_dict.get('devices', {}).get(f"{inputnum}", "No Input Device")
                output_str = audioinfo_dict.get('devices', {}).get(f"{outputnum}", "No Output Device")
                status_cont = st.container(border=True)
                status_cont.markdown(f"""{audioinfo_dict.get('recstate', "None")}  \n{input_str}  \n{output_str}""")
                st.write(audioinfo_dict)

     