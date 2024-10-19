# Standard Python Libraries
import os
import shutil
import yaml

import sys
import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend

import uuid

import json
import math
from collections import Counter
import random

#Date / Time
from datetime import datetime
import time


# PDF and Image Processing
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from markdown import markdown
from bs4 import BeautifulSoup
from pptx2md import convert

# Data Processing
import pandas as pd

# Async and Multiprocessing
from multiprocessing import Pool, cpu_count
import asyncio
import httpx
from tqdm.asyncio import tqdm_asyncio

from _class_logger import Logger

class TextExtractor:
    def __init__(self, model="gemini-1.5-flash", test_folder_path=None, force_rerun=False, skip_gemini=True):
        print(f"SysArg: {sys.argv}")
        if len(sys.argv) < 2 and test_folder_path is None:
            print("Error: No folder path provided.")
            sys.exit(1)
        
        self.path_to_extract = sys.argv[1] if len(sys.argv) >= 2 else test_folder_path
            
        self.logger = Logger()
        

        API_KEY = os.environ.get("GOOGLE_API_KEY")
        MODEL = model
        self.URL = f'https://generativelanguage.googleapis.com/v1/models/{MODEL}:generateContent?key={API_KEY}'
        self.HEADERS = {'Content-Type': 'application/json'}
        self.RUNNING_TOKEN_COUNT =0
        
        self.entropy_threshold = 4.8 # Entropy is a measure of the randomness in a string of text (used to ignore serial numbers, etc.)

        self.test_folder_path = test_folder_path
        self.gemini_rate_limit = 5
        self.skip_gemini = skip_gemini

        self.COMBINED_SUMMARY_FILE_PREFIX = "summary_combined_"
        self.CLEAN_TEXT_EXTRACTION_FILE_SUFFIX= "_clean"
        self.CLEAN_TEXT_EXTRACTION_FILE_TYPE= ".md"
        self.JSON_SUMMARY_FILE_SUFFIX= "_summary"
        self.JSON_SUMMARY_FILE_TYPE= ".json"
        self.SUMMARY_FILE_SUFFIX= "_summary"
        self.SUMMARY_FILE_TYPE= ".md"

        self.OVERWRITE_EXISTING_FILES = False
        self.pdf_types = ['.pdf']
        self.image_types = ['.jpg', '.jpeg', '.png', '.bmp', '.eps', '.tiff', 
                            '.webp', '.svg', '.ppm', '.sgi', '.iptc', '.pixar', '.psd', '.wmf']
        
        self.office_document_types = ['.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls']
        self.all_types = self.pdf_types + self.image_types + self.office_document_types
        self.pytesseract_executable_path = '/opt/homebrew/bin/tesseract'
        self.force_rerun = force_rerun
              
    async def get_log_file_working_dir(self, path_str):
        
        if not os.path.exists(path_str):
            return None
        
        if os.path.isfile(path_str):
            path = Path(path_str)
            # Extract the directory name
            directory_name = path.parent
            # Get the absolute path of the parent directory
            path_str = directory_name.resolve()
        
        # Extract the directory name
        path = Path(path_str)
        
        # Extract the directory name
        directory_name = path.name

        # Check if the directory name is not or "_attachments"
        if directory_name  in ["_attachments", "_attachments/"]:
            # Go back one directory
            parent_directory = path.parent
        else :
                parent_directory = path

        # Get the absolute path of the parent directory
        parent_directory_absolute_path = f"{parent_directory.resolve()}"
        
        return parent_directory_absolute_path

    async def get_processing_paths(self, file, additional_tags_list=[]):
        # self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
        file_name = os.path.basename(file)
        file_type = os.path.splitext(file)[1] 
        file_title = file_name.replace(file_type, "")
        base_folder_path = os.path.dirname(file)
        if base_folder_path.endswith("_attachments/") or base_folder_path.endswith("_attachments"):
            base_folder_path = os.path.dirname(base_folder_path)
        attachments_folder_path = f"{base_folder_path}/_attachments"
        working_folder_path = f"{base_folder_path}/_attachments"
        clean_file_path = os.path.join(base_folder_path, file_name.replace(file_type, "_clean.md"))
        post_processing_file_path = os.path.join(attachments_folder_path, file_name)
        
        if not os.path.exists(attachments_folder_path): os.makedirs(attachments_folder_path)
        if not os.path.exists(working_folder_path): os.makedirs(working_folder_path)
        
        # Get rid of he numbers
        file_title = file_name
        pattern = re.compile(r'^\d{1,3}(\.\d{1,3}){1,3} ')
        if pattern.match(file_title):
            # Remove the sequence from the filename
            file_title = pattern.sub('', file_title)

        type_tag = file_type.replace(".", "")
        type_tag = type_tag.upper()
        clean_tags = [f"{type_tag}"] + additional_tags_list
        for tag in clean_tags:
            tag = tag.replace("#", "")
            tag = tag.replace(".", "")
        clean_tags = list(set(clean_tags))
        yaml_header_dict = {
                    "Title": file_title,
                    "File": file_name,
                    "Pages": 0,
                    "Format": file_type.upper(),
                    "CreatedOn": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Tags": clean_tags
        }
        
        return file_name, file_title, file_type, base_folder_path, attachments_folder_path, working_folder_path, clean_file_path, post_processing_file_path, yaml_header_dict

    async def sanitize_for_url(self, input_string):
        # Use a regular expression to remove any characters that are not alphanumeric, hyphen, underscore, or period
        sanitized_string = re.sub(r'[^a-zA-Z0-9\-_.]', '', input_string)
        return sanitized_string
    
    async def init_extractor(self):
        
        working_dir = await self.get_log_file_working_dir(self.path_to_extract)
        self.logger = Logger(output_folder="_attachments", only_print_errors=True, working_dir=working_dir)
        # self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
        PATH_PARAMETER = self.path_to_extract
        if len(sys.argv) >= 3 and sys.argv[2] == "force_rerun":
            self.force_rerun = True 
            
        pdf_files_to_process, image_files_to_process, officedocs_to_process = await self.get_files_to_process(PATH_PARAMETER)
    
        if len(pdf_files_to_process) == 0 and len(image_files_to_process) == 0 and len(officedocs_to_process) == 0:
            self.logger.log(f"No PDF, Image, or Office Doc files found to process given input: sysargv: {PATH_PARAMETER}",color="YELLOW")
            sys.exit(0)   
        
        await self.execute_file_processing_tasks(pdf_files_to_process=pdf_files_to_process, 
                                                 image_files_to_process=image_files_to_process, 
                                                 officedocs_to_process=officedocs_to_process
                                                 )
    
    async def get_files_to_process(self, PATH_PARAMETER):
        pdf_files_to_process = []
        image_files_to_process = []
        officedocs_to_process = []
        print(f"PATH_PARAMETER = {PATH_PARAMETER}")
        if not os.path.exists(PATH_PARAMETER):
            self.logger.log(f"Error: Folder/File path not found: {sys.argv}",color="RED")
            sys.exit(1)
        
        if os.path.isdir(PATH_PARAMETER):
            for root, dirs, files in os.walk(PATH_PARAMETER):
                if "_attachments/images_" in root  or "_attachments/page_images" in root:
                    continue
                for file in files:
                    if file.startswith("~"):
                        continue
                    if file.endswith(".pdf"):
                        pdf_files_to_process.append(os.path.join(root, file))
                    if file.endswith(tuple(self.image_types)):
                        image_files_to_process.append(os.path.join (root, file))
                    if file.endswith(tuple(self.office_document_types)):
                        officedocs_to_process.append(os.path.join(root, file))
        

        if os.path.isfile(PATH_PARAMETER) and not PATH_PARAMETER.startswith("~"):
            root = os.path.dirname(PATH_PARAMETER)
            if PATH_PARAMETER.endswith(".pdf"):
                pdf_files_to_process.append(os.path.join(root, PATH_PARAMETER))
            if PATH_PARAMETER.endswith(tuple(self.image_types)):
                image_files_to_process.append(os.path.join (root, PATH_PARAMETER))
            if PATH_PARAMETER.endswith(tuple(self.office_document_types)):
                officedocs_to_process.append(os.path.join(root, PATH_PARAMETER))
        
        self.logger.log(f"PDF Files to Process: {pdf_files_to_process}",color="YELLOW")
        self.logger.log(f"Image Files to Process: {image_files_to_process}",color="YELLOW")
        self.logger.log(f"Office Document Files to Process: {officedocs_to_process}",color="YELLOW")
        
        return pdf_files_to_process, image_files_to_process, officedocs_to_process
    
    async def execute_file_processing_tasks(self, pdf_files_to_process, image_files_to_process, officedocs_to_process):
        
        file_processing_tasks = []
        for file in image_files_to_process:
            file_processing_tasks.append(self.image_to_text(file))
        for file in pdf_files_to_process:
            file_processing_tasks.append(self.process_pdf_file(file))
        for file in officedocs_to_process:
            file_processing_tasks.append(self.office_doc_to_text(file))
        
        random.shuffle(file_processing_tasks)
        self.logger.log(f"Beginning processing of {len(file_processing_tasks)} files.",color="CYAN")
        await tqdm_asyncio.gather(*file_processing_tasks)
            
        self.logger.log("All documents processed.",color="GREEN", force_print=True)
        
    async def process_pdf_file(self, file):
                            
        self.logger.log(f"Beginning assessment of PDF: {file}",color="NC")
        file_name, file_title, file_type, base_folder_path, attachments_folder_path, working_folder_path, clean_file_path, post_processing_file_path, yaml_header_dict = await self.get_processing_paths(file, ["PDF", "OCR"])
        
        #get the hours and minutes and seoonds in and hhmmss format
        image_folder_relative_path = await self.sanitize_for_url(f"images_{file_title}_{datetime.now().strftime("%H%M%S")}")
        image_folder_relative_path = f"_attachments/{image_folder_relative_path}"
        page_images_absolute_path = f"{base_folder_path}/{image_folder_relative_path}"
        if not os.path.exists(f"{page_images_absolute_path}"): os.makedirs(f"{page_images_absolute_path}")
        
        if file_type not in self.pdf_types:
            self.logger.log(f"PDF Error: File type {file_type} not supported for file {file}",color="RED")
            return True
        
        if os.path.isfile(clean_file_path) and not self.force_rerun:
            self.logger.log(f"Cleaned PDF file '{clean_file_path}' already exists. Skipping.",color="YELLOW")
            return True
        
        try: 
            # Begin the real processing
            self.logger.log(f"Begin extracting text from '{os.path.basename(file)}'.")
            raw_text, possible_title, page_count = await self.pdf_to_text(file, image_folder_relative_path, page_images_absolute_path)
            
            # Do some easy maintenance on the extracted text (before sending to Gemini)
            standard_text = await self.standardize_extracted_text(raw_text)
                
            if self.skip_gemini:
                clean_text = standard_text
            else:
                clean_text = await self.clean_extracted_text(standard_text)
            self.logger.log(f"Successfully extracted, standardized and cleaned text from '{file}'.",color="GREEN")
        except Exception as e:
            msg = f"""Error extracting PDF text. Error is likely in:
            pdf_to_text, standardized_extracted, or clean_extracted_text
            File: {file}
            Error: {e}"""
            
            self.logger.log(msg,color="RED")
            return False
        
        if possible_title != "No title found":
                yaml_header_dict['Title'] = possible_title
        
        if page_count != 0:
                yaml_header_dict['Pages'] = page_count
        
        # Dump the dictionary as a YAML string
        yaml_header = yaml.dump(yaml_header_dict, default_flow_style=False)

        # Create the complete header with delimiters
        md_header = f"---\n{yaml_header}---\n\n"
        
        if file != post_processing_file_path:
            #Move the image file to the attachments folder
            shutil.move(file, post_processing_file_path)
        
        final_text = f"{md_header}##### {possible_title}]\n\n{clean_text}\n\n![[_attachments/{file_name}]"
        
        with open(clean_file_path, 'w') as f:
            f.write(final_text)
                    
        self.logger.log(f"PDF Successful cleaned and saved text to:\n\033[1;36m'{clean_file_path}'.",color="GREEN")
        
        return True
               
    def process_image_pool(self, image_param):
        text = pytesseract.image_to_string(image_param[0])
        image_param.append(text)
        return image_param
    
    async def pdf_to_text(self, file_path, page_images_relative_path, page_images_absolute_path):
        # self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
        
        # Convert PDF to a list of images
        self.logger.log(f"Beginning cong of PDF to images: '{file_path}'")
        images = convert_from_path(file_path)
        
        images_param = []
        for i, image in enumerate(images):
            image_path = f"{page_images_absolute_path}/page_{i+1}.png"
            image.save(image_path, 'PNG')
            images_param.append([image, image_path])
        
        # Determine the number of processes to use (you can adjust this)
        # Create a Pool of worker processes
        self.logger.log(f" PDF Converted, Beginning  image multiprocessing for '{file_path}'")
        num_processes = min((cpu_count()-4), len(images))
        
        # Map each image to a process (each image is a page in the PDF)
        with Pool(processes=num_processes) as pool:
            results = pool.map(self.process_image_pool, images_param)
        
        self.logger.log(f"Completed  image multiprocessing for '{file_path}'")
        
        if not results or len(results) == 0:
            self.logger.log(f"Error: No text extracted from '{file_path}'.",color="RED")
            return ""
        
        #Get the first part of teh text (or all of it if it is short)
        if len(results) == 1: starting_text =  results[0][2]
        elif len(results) > 1: starting_text = f"{results[0][2]}\n{results[1][2]}"   
        
        # Submit the first part of the text to Gemini to get the title of the document
        possible_title = await self.try_and_get_document_title(starting_text)
        
        # Combine all extracted text with page numbers
        all_text = ''
        page_count =0
        for result in results:
            page_count += 1
            image_path = f"{page_images_relative_path}/page_{page_count}.png"
            image_text = result[2]
            all_text = f"""{all_text}\n""" + \
                "````col\n" + \
                "```col-md\n" + \
                "flexGrow=.5\n" + \
                "===\n" + \
                f"> [!info] [Page {page_count}]({image_path})\n" + \
                f"> ![]({image_path})\n" + \
                "```\n\n" + \
                "```col-md\n" + \
                f"{image_text}\n" + \
                "```\n" + \
                "````\n" + \
                "Notes:  \n"
            
        # for i, page in enumerate(results):
        #     all_text = f'''{all_text}\n___ \n<span style="color:#6986B0; font-size:20px; font-weight:bold;">Page {i + 1}</span> \n\n{sentence}\n'''

        return all_text, possible_title, page_count

    def calculate_entropy(self, text):
        # Count the frequency of each character in the string
        frequencies = Counter(text)
        total_chars = len(text)

        # Calculate probabilities and entropy
        entropy = 0
        for freq in frequencies.values():
            prob = freq / total_chars
            if prob != 0:  # Handle the case where the probability is zero
                entropy -= prob * math.log2(prob)

        return entropy
    
    async def ocr_image(self, file_path ):
        # self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
        
        # Get the file extension
        file_extension = os.path.splitext(file_path)[1] 
        
        # Check if the file extension is supported
        if file_extension not in self.image_types:
            msg = f"File type {file_extension} not supported for file {file_path}"
            self.logger.log(msg, color="RED")
            return file_path, False, msg
        
        # Configure the path to the tesseract executable
        pytesseract.pytesseract.tesseract_cmd = self.pytesseract_executable_path

        try:
            # Load the image
            image = Image.open(file_path)
            
            # Use Tesseract to do OCR on the image
            text = pytesseract.image_to_string(image)
            
            return text
            
        except Exception as e:
            msg = f"Error extracting text from the image: {e}"
            self.logger.log(msg, color="RED")
            return msg
    
    async def standardize_extracted_text(self, ocr_text):
        # self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
        
        # Identify extraction-created unnecessary line breaks (for preservation and later standardization)
        # Note: the below will remove the line breaks that are not part of any title
        # lines however we will restore those carefully 
        mutiple_line_breaks = f"{uuid.uuid4()}"
        ocr_text = ocr_text.replace("\n\n\n\n\n", mutiple_line_breaks)
        ocr_text = ocr_text.replace("\n\n\n\n", mutiple_line_breaks)
        ocr_text = ocr_text.replace("\n\n\n", mutiple_line_breaks)
        ocr_text = ocr_text.replace("\n\n", mutiple_line_breaks)
        # ocr_text = ocr_text.replace(". \n", mutiple_line_breaks)
        # ocr_text = ocr_text.replace(".  \n", mutiple_line_breaks)
        
        #Eliminate line brakes from mid-word wraps
        ocr_text = ocr_text.replace("- \n", "")
        ocr_text = ocr_text.replace("-\n", "")
        
        # Clean up double periods
        ocr_text = ocr_text.replace("..", ".  \n")  
        
        # Remove dangling periods (likely scanned image blips)
        ocr_text = ocr_text.replace("\n. ", "")
        ocr_text = ocr_text.replace("\n.", "")
        ocr_text = ocr_text.replace("# ", "")
        
        # Restore places that previously had multiple line breaks to have 1 line break
        standardized_text = ocr_text.replace(mutiple_line_breaks, "  \n")
        return standardized_text
    
    def markdown_to_plain_text(self, markdown_text):
        # Convert Markdown to HTML
        html = markdown(markdown_text)
        # Use BeautifulSoup to convert HTML to plain text
        soup = BeautifulSoup(html, "html.parser")
        plain_text = soup.get_text()
        return plain_text    
    
    def standardize_markdown_headers(self, markdown_text):
        # Scanned text has line break on every wrap of body text.  If a line break doe not conform to the
        # above patterns, the line break should likely be removed (unless it is a tile line)
        # Each text line has no \n (because of the split), but we will add them before and after titles
        page_number_html = f"{uuid.uuid4()}"
        multiple_line_breaks = f"{uuid.uuid4()}"
        #Retain multiple line breaks wherever they are ...
        
        page_number_style ='<span style="color:#6986B0; font-size:20px; font-weight:bold;">'
        markdown_text = markdown_text.replace("\n\n", multiple_line_breaks)
        markdown_text = markdown_text.replace("\n\n\n", multiple_line_breaks)
        markdown_text = markdown_text.replace(page_number_style, page_number_html)
        
        text_lines = markdown_text.split("\n")
        title_indicators = ["######", "#####", "####", "###" "##", "#"]
            
        standardized_lines = []
        for line in text_lines:
            if not line or line.strip() == "":
                continue
            
            line = line.replace(".. ", ".  ")
            line = line.replace("# #", "####")

            for title_indicator in title_indicators:
                if title_indicator in line and not "6986B0" in line:
                    line = line.replace(title_indicator, f"\n####")
                    line = f"{line}\n"
                    line = line.replace(multiple_line_breaks, "\n")
                    line = line.replace(page_number_html, page_number_style)
                    line = line.replace("___", "\n___")
                line = line.replace("</span>", "</span>\n")
                line = line.replace("<span style", "\n<span style")    
                standardized_lines.append(line)
                continue        
        
        # Reassemble the sentence using spaces instead of \n
        # The  majority of paragraphs that had wrap-created line breaks mid sentence 
        # should be corrected now. 
        markdown_text = " ".join(line for line in standardized_lines if line and line.strip() != "" and line.replace("#", "").strip() != "")  
        return markdown_text

    async def fetch_gemini_response(self, prompt=None, data=None, timeout=15, return_data_on_error=False):
        # self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
        
        return_value_on_error = None
        
        if return_data_on_error:
            return_value_on_error = data
        
        if not prompt:
            return return_value_on_error
        
        if data:
            prompt = f"{prompt}\n{data}"
        
        limits = httpx.Limits(max_keepalive_connections=None, max_connections=None)
        timeout = httpx.Timeout(timeout, read=timeout)
        KeepTrying = True
        TryCount = 0
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "safetySettings": [
            {"category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE"},
            ]
            }
        
        response = None
        
        async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
            while KeepTrying and TryCount <= 3:
                TryCount += 1
                try:
                    time.sleep(.2)
                    response = await client.post(self.URL, headers=self.HEADERS, json=payload)
                    response.raise_for_status()
                except Exception as e:
                    tqdm_asyncio.write(f"TQDM Error in get_gemini response: {e}")
                    self.logger.log(f"Gemini Error (Try 1): {e}\n Prompt {prompt}\n" , color="RED", force_print=True)
                    time.sleep(1)
                    if TryCount > 2:
                        KeepTrying = False
                        tqdm_asyncio.write(f"Error: Failed to get response after {TryCount} tries.")
                        self.logger.log(f"Giving up on this Gemini Request): {e}\n Prompt {prompt}\n" , color="RED", force_print=True)
                        time.sleep(1)
                        return return_value_on_error
                    
                    else:
                        tqdm_asyncio.write(f"Warning: Retrying request {TryCount}...")
                        self.logger.log(f"Gemini Error (Try {TryCount}): {e}\n Prompt {prompt}\n" , color="RED", force_print=True)
                        time.sleep(1)
                        await asyncio.sleep(1*TryCount)
                        continue
            
            
        try:
            result = response.json()
            self.RUNNING_TOKEN_COUNT += int(result.get('usageMetadata', {}).get('totalTokenCount', 0))
        
            if result['candidates'][0]['finishReason'] == 'RECITATION':
                tqdm_asyncio.write("Warning: Possible copyrighted or sensitive content detected. Returning original text.")
                return return_value_on_error  # Return original text if flagged
            else:    
                value_to_return = result['candidates'][0]['content']['parts'][0]['text']
                return value_to_return

        except Exception as e:
            tqdm_asyncio.write("Could not process the response.json() from Gemini.")
            if response:
                tqdm_asyncio.write(f"Value of result: \n${response} \n\n Error: {e}")
            return return_value_on_error
                
    async def try_to_json(self, input_value):
        # self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
        try:
            return json.loads(input_value)
        except:
            pass
        try:
            return json.loads(f"[{input_value}]")
        except json.JSONDecodeError:
            return input_value
    
    async def extract_json_dict_from_llm_response(self, llm_response):
        # self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")

        
        # Find the first '{' and the last '}'
        start_idx = llm_response.find('{')
        end_idx = llm_response.rfind('}')

        if start_idx == -1 or end_idx == -1:
            return None

        try:
            # Extract the JSON string
            json_string = llm_response[start_idx:end_idx + 1]
            
            json_dict = await self.try_to_json(json_string)
            if  isinstance(json_dict, dict) or isinstance(json_dict, list):
                return json_dict
            else:
                return None
        except Exception as e:
            return None
    
    async def create_prompt_to_clean_ocr_text(self):
        # self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
            
        json_response_format = {"transformedtext": "the transformed text you create", "commentary": "Commentary you feel is necessary about how you did or did not clean the text."}

        instructions = f"""Transform the following OCR-extracted text into clean, readable MARKDOWN. 
        Return the MARKDOWN in the specified JSON format. The text is part of a longer document that was split on ". "
        please look for sentences with preceeding title text and apply reasonable line breaks and MARKDOWN "#" header formatting.

        1. Accuracy: Correct OCR errors, ensuring the text is accurate.
        2. Readability: Make the text clear and easy to understand.
        3. Structure: Preserve the original structure (e.g., lists, headings).
        4. Legal Context: If the document is a legal document, maintain the integrity of ALL legal language.
        5. Organization: Keep the names of these organizations as they are: Fincentric, Markit On Demand, Markit, S&P, Wall Street On Demand, JBI, Communify.
        6. Uncertain Words: If a word is unclear, mark it with a question mark in brackets [?].
        7. Make sure to maintain existing valid MARKDOWN and HTML formatting (if it is around the page numbers)
        
        Your response is being systematically integrated. Only return the MARKDOWN in the specified JSON in the format below:
        {json.dumps(json_response_format, indent=4)}
        

        OCR Text:"""

        return instructions

    async def extract_cleaned_text_from_gemini_response(self, prompt, data):
        # self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
        self.logger.log(f"Gemini-cleaning sesntence: {data}",color="GREEN")
        llm_response = await self.fetch_gemini_response(prompt, data, return_data_on_error=True)
        
        start_idx = llm_response.find('{')
        end_idx = llm_response.rfind('}')

        if start_idx == -1 or end_idx == -1:
            return None

        try:
            json_string = llm_response[start_idx:end_idx + 1]
            json_dict = await self.try_to_json(json_string)
            if isinstance(json_dict, dict):
                clean_text = json_dict.get('transformedtext', "No title found")
                return clean_text
            else:
                return None
        except Exception as e:
            print(f"Exception in extract_cleaned_text_from_gemini_response: {e}")
            return None

    async def schedule_task(self, semaphore, task):
        async with semaphore:
            return await task
    
    async def clean_extracted_text(self, raw_text):
        # self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
        sentences = raw_text.split(". ")
        
        self.logger.log("Split text into {len(sentences)} sentences | Beginning to clean text with Gemini...", color="GREEN")

        prompt = await self.create_prompt_to_clean_ocr_text()
        
        semaphore = asyncio.Semaphore(self.gemini_rate_limit)
        # Create a list of tasks, applying the semaphore to rate limit them
        cleaning_tasks = [self.schedule_task(semaphore, self.extract_cleaned_text_from_gemini_response(prompt, sentence))
                        for sentence in sentences if sentence.strip()]
        
        # cleaning_tasks = [self.extract_cleaned_text_from_gemini_response(prompt, sentence) for sentence in sentences if sentence.strip()]

        start_time = datetime.now()
        tqdm_asyncio.write(f"Cleaning {len(sentences)} sentences with Gemini...")
        cleaned_sentences = await tqdm_asyncio.gather(*cleaning_tasks,)

        time_delta_int = int((datetime.now() - start_time).total_seconds())
        avg_tokens_per_sentence = self.RUNNING_TOKEN_COUNT/len(cleaned_sentences) if len(cleaned_sentences) > 0 else 0
        avg_tokens_per_second = self.RUNNING_TOKEN_COUNT/time_delta_int if time_delta_int > 0 else 0
        self.logger.log(f"Time taken: {time_delta_int} | {len(cleaned_sentences)} sentences. \n {self.RUNNING_TOKEN_COUNT} tokens used. {avg_tokens_per_sentence} average tokens per sentence. {avg_tokens_per_second} average tokens per second.")
        
        text_only_sentence = [self.standardize_markdown_headers(sentence) for sentence in cleaned_sentences if sentence and sentence.strip() != ""]
        
        all_sentences = []
        
        for sentence in text_only_sentence:
            if sentence.strip().endswith("."):
                sentence = sentence[:-1]
            all_sentences.append(sentence)
                
        clean_text = ".  ".join(all_sentences)
        
        # Further clean up the text as a whole
        clean_text = clean_text.replace("####\n", "\n")
        clean_text = clean_text.replace("\n\n\n", "\n\n")
        clean_text = clean_text.replace("\n\n", "\n")
        clean_text = clean_text.replace("___", "")
        clean_text = clean_text.replace("\n####P", "\n#### P")
        clean_text = clean_text.replace("\n#### <font color=", "___\n#### <font color=")
        
        return clean_text

    async def try_and_get_document_title(self, some_text):
        # self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
        
        
        json_response_format = {"title": "[Formal Title of Document]"}

        prompt = f"""Given the text below, which is the first part of a document or set of images, please attempt to obtain the formal title of the document or create one based on the content and return it in the specified JSON format.:
        
        ### Start of Text ###
        {some_text}
        ### End of Text ###
        
        Your response is being systematically integrated. Only return the title in the specified JSON format below:
        {json.dumps(json_response_format, indent=4)}"""
        try: 
        
            # Ask Gemini to get the title of the document
            response = await self.fetch_gemini_response(prompt)
            
            dict_response = await self.extract_json_dict_from_llm_response(response)
            if isinstance(dict_response, dict):
                return_text = dict_response.get('title', "No title found")
                return return_text
            else:
                return "No title found"
            result = response.json()
        
            
        except:
            self.logger.log("Warning: JSON format not detected. No title found", color="ORANGE")
            return "No title found"
   
    async def office_doc_to_text(self, file_path):
        # self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
        
        supported_doc_types = ['.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls']
        self.logger.log(f"Processing Office Document: {file_path}",color="YELLOW") 
        
        file_name, file_title, file_type, base_folder_path, attachments_folder_path, working_folder_path, clean_file_path, post_processing_file_path, yaml_header_dict= await self.get_processing_paths(file_path, ["OfficeDoc"])
        
        #Generate a 5-digit random number to use as a unique identifier
        unique_id = str(random.randint(10000, 99999))
        
        images_folder_name = os.path.join(attachments_folder_path, f"images_{unique_id}")
        
        if file_type not in supported_doc_types:
            self.logger.log(f"Office Doc Error: File type {file_type} not supported for file {file_path}",color="RED")
            return  ''
        
        # Get the approaciate document loader based on the file extension
        if file_type in ['.docx', '.doc']:
            pass# doc_loader = UnstructuredWordDocumentLoader(file_path=file_path, mode="elements")
        
        if file_type in ['.pptx', '.ppt']:
            # Convert the pptx file to markdown (convert is a 3rd party function)
            convert(file_path, output=clean_file_path, title=file_title, image_dir=images_folder_name) 

        if file_type in ['.xlsx', '.xls']:
            markdown_text = await self.excel_to_text(file_path)
            with open (clean_file_path, 'w') as f:
                f.write(markdown_text)
        
        if not "_attachments" in file_path:
            #Move the file to the attachments folder
            shutil.move(file_path, post_processing_file_path)
        return True
     
    async def excel_to_text(self, excel_file_path):
        # self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")

        # Load the Excel file
        excel_data = pd.ExcelFile(excel_file_path)
        
        md_file_text = []
        for sheet_name in excel_data.sheet_names:
            # Write the sheet name
            md_file_text.append(f"\n___\n### {sheet_name}\n\n")
            
            # Load the sheet into a DataFrame
            df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
            
            # Format the header
            header = '| ' + ' | '.join([f'**{col}**' for col in df.columns]) + ' |'
            separator = '| ' + ' | '.join(['---' for _ in df.columns]) + ' |'
            
            md_file_text.append(header)
            md_file_text.append(separator)
            
            # Write the data rows
            for index, row in df.iterrows():
                row_values = []
                for value in row:
                    if isinstance(value, (int, float)):
                        row_values.append(f"{value}")
                    elif isinstance(value, datetime):
                        try:
                            row_values.append(f"{value.strftime('%Y-%m-%d')}")
                        except:
                            row_values.append(f"{value.max}")
                    else:  
                        row_values.append(f"{value}")
                row_str = '| ' + ' | '.join(row_values) + ' |'
                md_file_text.append(row_str)
            
            # Add space between sheets
            md_file_text.append('\n\n')
            
        final_text = "\n".join(md_file_text)
        def remove_strings(text, substrings):
            for substring in substrings:
                text = text.replace(substring, "")
            return text
        substrings_to_remove = ["NaT", "nan", "9999-12-31 23:59:59.999999", "00:00:00"]
        final_text = remove_strings(final_text, substrings_to_remove)
        
        return final_text
    
    async def semi_improve_image_ocr(self, clean):
        # self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
        # Best efforts to clean up the text from OCR
        clean_text_lines = clean.split("\n")
        valid_lines = []
        invalid_lines = []
        for line in clean_text_lines:
            if "___" in line or "6986B0" in line:
                valid_lines.append(line)
                continue
            if not line or line.strip() == "" or line.replace("#", "").strip() == "" or "6986B0" in line:
                continue
            if len(line.strip()) <= 1:
                continue
            plain_text = self.markdown_to_plain_text(line)
            line_text_entropy = self.calculate_entropy(plain_text)
            if line_text_entropy > self.entropy_threshold:
                # this means it gibberish
                invalid_lines.append(line.strip())
            else:
                valid_lines.append(line)
        self.logger.log(f"Removed this text via Entropy Check: {invalid_lines}",color="NC")  
        semi_improved_text = "\n".join(valid_lines)
        return semi_improved_text
        
    async def image_to_text(self, file):
        # self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
                    
        self.logger.log(f"Beginning assessment of image: {file}",color="NC")
        
        file_name, file_title, file_type, base_folder_path, attachments_folder_path, working_folder_path, clean_file_path, post_processing_file_path, yaml_header_dict = await self.get_processing_paths(file, ["Image"])
        
        if file_type not in self.image_types:
            self.logger.log(f"Image Error: File type {file_type} not supported for file {file}",color="RED")
            return True
        
                
        if os.path.isfile(clean_file_path) and not self.force_rerun:
            self.logger.log(f"Cleaned Image file '{clean_file_path}' already exists. Skipping.",color="YELLOW")
            return True
                
        self.logger.log(f"Proceeding with porcessing of: {file}",color="NC") 
        
        try:
            image_raw_text = await self.ocr_image(file)
            clean_text = await self.clean_extracted_text(image_raw_text)
            clean_text = await self.semi_improve_image_ocr(clean_text)
            possible_title = await self.try_and_get_document_title(clean_text)
            if possible_title != "No title found":
                yaml_header_dict['Title'] = possible_title
        except Exception as e:
            self.logger.log(f"Error during OCR, cleaning or while obtaining title: {file}\n Error is: {e}",color="RED")
            return False
        
        # Dump the dictionary as a YAML string
        yaml_header = yaml.dump(yaml_header_dict, default_flow_style=False)

        # Create the complete header with delimiters
        md_header = f"---\n{yaml_header}---\n\n"
        
        if file != post_processing_file_path:
            #Move the image file to the attachments folder
            shutil.move(file, post_processing_file_path)
        
        final_text = f"{md_header}##### {possible_title}\n\n![[_attachments/{file_name}]]\n\n{clean_text}"
        
        with open(clean_file_path, 'w') as f:
            f.write(final_text)
        
        self.logger.log(f"Successfully cleaned and saved text to:\n\033[1;36m'{clean_file_path}'.",color="GREEN")
        
        return True

        
    
        
if __name__ == "__main__":
    pass
    test_folder = "/Users/michasmi/Downloads/goldmine2/_attachments/79_340898_9_20231208.pdf"
    # test_folder = "/Users/michasmi/Downloads/goldmine2/_attachments"
    extractor = TextExtractor(test_folder_path=test_folder, force_rerun=True,)
    asyncio.run(extractor.init_extractor())
         