# Standard Python Libraries
import os
import streamlit as st
# from _class_streamlit import streamlit_mytech
from _class_firebase import FirestoreStorage

import uuid

import json
import math
from collections import Counter

#Date / Time
from datetime import datetime
import time


# PDF and Image Processing
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image

# Async and Multiprocessing
from multiprocessing import Pool, cpu_count
import asyncio
import httpx
from tqdm.asyncio import tqdm_asyncio

class TextExtractor:
    def __init__(self, model="gemini-1.5-flash"):
        
        

        API_KEY = os.environ.get("GOOGLE_API_KEY")
        MODEL = model
        self.URL = f'https://generativelanguage.googleapis.com/v1/models/{MODEL}:generateContent?key={API_KEY}'
        self.HEADERS = {'Content-Type': 'application/json'}
        self.RUNNING_TOKEN_COUNT =0
        
        self.entropy_threshold = 4.8 # Entropy is a measure of the randomness in a string of text (used to ignore serial numbers, etc.)

        self.gemini_rate_limit = 5
        
        self.OVERWRITE_EXISTING_FILES = False
        self.pdf_types = ['.pdf']
        self.image_types = ['.jpg', '.jpeg', '.png', '.bmp', '.eps', '.tiff', 
                            '.webp', '.svg', '.ppm', '.sgi', '.iptc', '.pixar', '.psd', '.wmf']
        self.office_document_types = ['.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls']
        self.all_types = self.pdf_types + self.image_types + self.office_document_types
        self.pytesseract_executable_path = '/opt/homebrew/bin/tesseract'
        self.db = FirestoreStorage(default_collection='documents')
        
        self.progress_total = 0
        self.progress_current  = 0

    async def process_pdf_files(self, files, progress_bar):
        for file in tqdm_asyncio(files):
            
            await self.process_pdf_file(file)
            self.progress_current +=1
            progress_bar.progress((self.progress_current/self.progress_total))

    async def process_pdf_file(self, file):
        
        # try:     
            possible_title, results = await self.pdf_to_text(file)
            
            doc_guid = f'{uuid.uuid4()}'
            
            doc_dict = {
                'title': possible_title, 
                'file': file.name,
                'size': file.size,
                'type': file.type,
                'guid': doc_guid, 
               'pages': len(results),
                'created': datetime.now().isoformat(),
                'updated': datetime.now().isoformat()
                
                }
            await self.db.insert_dictionary('documents', doc_dict, doc_guid)
            page_number = 0
            
            for page in results:
                page_number+=1
                
                page_guid = f'Page-{page_number}-of-{len(results)}-{doc_guid}'
                image_url = await self.db.upload_image_from_object(page[0], f'{page_guid}.png')
                
                # clean_text = self.standardize_extracted_text(page[1])
                clean_text = page[1]
                
                page_dict = {
                'name': possible_title, 
                'url': image_url,
                'doc_guid': doc_guid,
                'page_guid': page_guid, 
                'page_number': page_number,
                'page_text': clean_text,
                'pages': len(results),
                    'created': datetime.now().isoformat(),
                    'updated': datetime.now().isoformat()
                     }
                
                await self.db.insert_dictionary('document-pages', page_dict, page_guid)

            
            
        
        # except Exception as e:
        #     msg = f"""Error extracting PDF text. Error is likely in:
        #     pdf_to_text, standardized_extracted, or clean_extracted_text
        #     File: {file}
        #     Error: {e}"""
            
        #     ## self.logger.log(msg,color="RED")
        #     return False
        # return True
               
    def process_image_pool(self, image):
        text = pytesseract.image_to_string(image)
        image_and_text = [image, text]
        return image_and_text
    
    async def pdf_to_text(self, file):
        
        images = convert_from_bytes(file.read())
        
        results = []
        for image in images:
            results.append(self.process_image_pool(image))
        
        
        if not results or len(results) == 0:
            #self.logger.log(f"Error: No text extracted from '{file_path}'.",color="RED")
            return []
        
        #Get the first part of teh text (or all of it if it is short)
        starting_text =  results[0][1]
        if len(results) > 1:
            starting_text += results[1][1]
        
        # Submit the first part of the text to Gemini to get the title of the document
        possible_title = await self.try_and_get_document_title(starting_text)
        
        return possible_title, results
    
    async def fetch_gemini_response(self, prompt=None, data=None, timeout=15, return_data_on_error=False):
        ## self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
        
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
                    #self.logger.log(f"Gemini Error (Try 1): {e}\n Prompt {prompt}\n" , color="RED", force_print=True)
                    time.sleep(1)
                    if TryCount > 2:
                        KeepTrying = False
                        tqdm_asyncio.write(f"Error: Failed to get response after {TryCount} tries.")
                        #self.logger.log(f"Giving up on this Gemini Request): {e}\n Prompt {prompt}\n" , color="RED", force_print=True)
                        time.sleep(1)
                        return return_value_on_error
                    
                    else:
                        tqdm_asyncio.write(f"Warning: Retrying request {TryCount}...")
                        #self.logger.log(f"Gemini Error (Try {TryCount}): {e}\n Prompt {prompt}\n" , color="RED", force_print=True)
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
        ## self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
        try:
            return json.loads(input_value)
        except:
            pass
        try:
            return json.loads(f"[{input_value}]")
        except json.JSONDecodeError:
            return input_value
    
    async def extract_json_dict_from_llm_response(self, llm_response):
        ## self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")

        
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
        ## self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
            
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
        ## self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
        #self.logger.log(f"Gemini-cleaning sesntence: {data}",color="GREEN")
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

    async def try_and_get_document_title(self, some_text):
        ## self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
        
        
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
            ## self.logger.log("Warning: JSON format not detected. No title found", color="ORANGE")
            return "No title found"
   
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

    async def semi_improve_image_ocr(self, clean):
        ## self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
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
        ## self.logger.log(f"Removed this text via Entropy Check: {invalid_lines}",color="NC")  
        semi_improved_text = "\n".join(valid_lines)
        return semi_improved_text
        
    async def image_to_text(self, file):
        
        try:
            
            image_raw_text = await self.ocr_image(file)
            clean_text = await self.clean_extracted_text(image_raw_text)
            clean_text = await self.semi_improve_image_ocr(clean_text)
            possible_title = await self.try_and_get_document_title(clean_text)
            
        except Exception as e:
            print(f"Error during OCR, cleaning or while obtaining title: {file}\n Error is: {e}",color="RED")
            return False, False, False
        
        
        return image_raw_text, possible_title, clean_text

    async def ocr_image(self, file_path ):
        ## self.logger.log(f"CurFunct11: {inspect.currentframe().f_code.co_name}", force_print=True, color="CYAN")
        
        # Get the file extension
        file_extension = os.path.splitext(file_path)[1] 
        
        # Check if the file extension is supported
        if file_extension not in self.image_types:
            msg = f"File type {file_extension} not supported for file {file_path}"
            ## self.logger.log(msg, color="RED")
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
            ## self.logger.log(msg, color="RED")
            return msg
    
        
async def main():

    # stm = streamlit_mytech(theme='cfdark')
    ext = TextExtractor()
    # stm.set_up_page(page_title_text="PDF Uploader",
    #                 session_state_variables=[], )

    # File uploader
    if 'processed' not in st.session_state:
        st.session_state['processed'] = []
    
    uploaded_file_list = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
    if uploaded_file_list is not None:
        uploaded_file_list = [f for f in uploaded_file_list if f not in st.session_state["processed"]]
        if len(uploaded_file_list)>0:
            upl_prog = st.progress(0, 'Uploading Files')
            ext.progress_total = len(uploaded_file_list)
            ext.progress_current = 0
            await ext.process_pdf_files(uploaded_file_list, upl_prog)
            for file in uploaded_file_list:
                st.session_state['processed'].append(f'{file.name}')
        uploaded_file_list.clear()  
    for file in st.session_state["processed"]:
        st.markdown(f'File: **{file}** was processed.')
                
 

asyncio.run(main())
if __name__ == "__main__":
    pass
   