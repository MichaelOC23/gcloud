from hmac import new
import os
import json
from pathlib import Path
import PIL.Image
import pytesseract
# import functions_constants as con
import re
from pdfminer.high_level import extract_text
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
import uuid
from _class_extract_text import Extract_Text_From_PDF as extract_pdf_new
import streamlit as st

ext_pdf = extract_pdf_new()
new_texts = []
combined_extract_name = "-all-extracts.json"
# folder = os.path.join(con.TEST_FOLDER_PATH, 'test-text-extraction')
current_folder = os.path.dirname(__file__)  
output_folder = os.path.join(current_folder, 'assets', 'textextracts')

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

#! Example of JSON text extraction from PDF
def extract_text_from_pdf_as_JSON(pdf_file):

    #Create an empty dictionary
    data = {}

    with open(pdf_file, 'rb') as f:
        filename = Path(pdf_file).stem # remove extension
        filename = re.sub(r'[^a-zA-Z0-9_\s-]', '', filename) # clean invalid chars
        
        
        data[filename] = {}
        
        for page_num, page_layout in enumerate(extract_pages(f)):
            page_key = f"{filename}.page.{page_num:04d}" 
            data[filename][page_key] = []
            
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text = element.get_text()
                    data[filename][page_key].append(text)
    
    return data

#! Example of simple text extraction from many file types
def process_extraction_from_file(filename, output_folder, split_key = None, json_str_start = None):
    # Extract text 

    if split_key is None:
        split_key = str(uuid.uuid4())

    text = ''

    # get file extension from filename
    file = Path(filename)


    if file.suffix in ['.png', '.jpg', '.jpeg']:
        print(f"IMAGE: Attempting to extract text from {filename} with suffix {file.suffix} as IMAGE ...")
        text = pytesseract.image_to_string(PIL.Image.open(filename))
        #prep the text to be part of a string in JSON format
        text= json.dumps(text)
        filename_escaped = json.dumps(filename)
        # Add the filename as a parent node
        text = "{" + f'{filename_escaped}: {text}' + "}"
        #turn it into a dictionary
        text_dict = json.loads(text)
    
    elif file.suffix == '.pdf':
        print(f"PDF: Attempting to extract text from {filename} with suffix {file.suffix} as PDF ...")
        filename_escaped = json.dumps(filename)
        #This function returns a dictionary
        text_dict = extract_text_from_pdf_as_JSON(filename)
    
    else:
        print(f"OTHER/TXT: Attempting to extract text from {filename} with suffix {file.suffix} as TEXT ...")
        with open(filename, 'r') as f:
            text = f.read()
        #prep the text to be part of a string in JSON format
        text = json.dumps(text)
        filename_escaped = json.dumps(filename)
        # Add the filename as a parent node
        text = "{" + f'{filename_escaped}: {text}' + "}"
        text_dict = json.loads(text)
    
    json_as_text = json.dumps(text_dict)

    if json_as_text == None or text_dict == '':
        with open(os.path.join(output_folder, 'failed.txt'), 'a') as f:
            f.write(f"{filename}\n")
        return text
    else:
        # Write text to file
        with open(os.path.join(output_folder, f'{split_key}-{file.stem}.json'), 'w') as f:
            f.write(f"{json_as_text}\n")
        
        # Write text to combined file for split_key
        # with open(os.path.join(output_folder, f'{split_key}{combined_extract_name}'), 'r') as fr:
        #     body = fr.read()
        #     fr.close()
        #     if body == json_str_start: # if first entry, don't add comma
        #         with open(os.path.join(output_folder, f'{split_key}{combined_extract_name}'), 'a') as f:
        #             f.write(f"{json_as_text}\n") #no leading comma
        #     else:
        #         with open(os.path.join(output_folder, f'{split_key}{combined_extract_name}'), 'a') as f:
        #             f.write(f",{json_as_text}\n") # add comma to separate entries (after first entry)
    
    return json_as_text
        
def extract_text_from_file_list(file_list, output_folder_path, extensions):  
    
    split_key = str(uuid.uuid4())
    
    #open combined file for split_key and plan to put each document in it as an array item
    json_str_start = "{" + f'"{split_key}":['
    
    with open(os.path.join(output_folder, f'{split_key}{combined_extract_name}'), 'a') as f:
        f.write(json_str_start)

    # Iterate through the file names and perform some action on each one
    for file in file_list:    
        if file.split('.')[-1] in extensions: 
            json_as_text = process_extraction_from_file(file, output_folder_path, split_key, json_str_start)
            st.write(json.loads(json_as_text))
            
    # with open(os.path.join(output_folder, f'{split_key}{combined_extract_name}'), 'a') as f:
    #         f.write("]}")
        
import classes._class_streamlit as cs
cs.set_up_page(page_title_text="PDF Text Extraction (JSON Format)", jbi_or_cfy="jbi", light_or_dark="dark", 
    session_state_variables=[], connect_to_dj=False) 

old_process = ''
new_process = ''
with st.form(key="my_form"):
    files = st.file_uploader("Upload a file", type=["png", "jpg", "jpeg", "txt", "pdf"], accept_multiple_files=True, key="upload_files")
    submit_button = st.form_submit_button(label="Submit")
    if submit_button:
        if files is None:
            st.write("Please enter a folder path to continue.")
        
        else:
            extensions = ["png", "jpg", "jpeg", "txt", "pdf"]
            if not isinstance(files, list):
                files = [files]
            file_path_list = get_files_from_upload(files, output_folder)
            for file in file_path_list:
            
                old_process = json.loads(process_extraction_from_file(file, output_folder))
                
                new_process = ext_pdf.extract_json_from_pdf(pdf_path=file, output_folder=output_folder)
                useful_text_list = new_process.get('useful', [])
                new_texts = [d['text'] for d in useful_text_list if 'text' in d]

                # def extract_json_from_pdf(self, pdf_path, extract_path=None, entropy_threshold=4.8, output_folder=None):
                
                
old_col, new_col = st.columns(2)
old_col.header("Old Process")
old_col.write(old_process)
new_col.header("New Process")
new_col.write(new_texts)


            

            


# if __name__ == "__main__":
#     extensions = ["png", "jpg", "jpeg", "txt", "pdf"]
#     extract_text_from_files_in_folder(folder, output_folder, extensions)




