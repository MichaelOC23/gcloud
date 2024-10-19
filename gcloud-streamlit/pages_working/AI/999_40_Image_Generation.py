import sys
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

import streamlit as st
import numpy as np
import os
import functions_constants as con
import functions_images_stabledifusion as sd


st.header("Streamlit: Example User Interface Components", divider="blue")
#create a tab in the main page
SDXL_Tab1, DALLE_Tab2 = st.tabs(["Stable Difusion", "Dall e"])
with SDXL_Tab1:
        prompt_col1, col2, col3 = st.columns(3)

        with prompt_col1:
            st.header("Prompt")
            prompt_container = st.text_area('Prompt')
            prompt_image_count = st.number_input("Number of images to generate", value=1, placeholder="Type a number...")
            prompt_button = st.button('Submit Prompt')


        with col2:
            new_image_header = st.header("Generated Images")
            new_image_status = st.write("...")
            new_image_container = st.container(border=True)
            #image_path = os.path.join(current_directory, "placeholder_image.jpg")
            #new_image_container.image(image_path)
            
        with col3:
            st.header("Previous Images")
            prior_image_container = st.container(border=True)
            for file in os.listdir(con.IMAGE_PROCESSING_FOLDER_PATH):
                if file.lower().endswith(tuple(con.IMAGE_PATH_EXTENSIONS)): #if the file is an image with a valid extension
                    image_file_path = os.path.join(con.IMAGE_PROCESSING_FOLDER_PATH, file)
                    prior_image_container.image(image_file_path)
        
        
        if prompt_button:
            prompt = prompt_container
            new_image_status = ("Generating new image ...")
            images = sd.get_sdxl_image(prompt, prompt_image_count, con.UNIQUE_DATE_TIME_STRING())
            # for file in os.listdir("/images/"):
            #     st.image(file)  
            # new_image_status.write("New image generated.")