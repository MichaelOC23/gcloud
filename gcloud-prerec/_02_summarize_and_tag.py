import os
import sys
import asyncio
import random
import re
import uuid
# import aiofiles
# import aiohttp
# import fnmatch
# import httpx
import json
import google.generativeai as genai


# Import the custom Logger class
from _class_logger import Logger
logger = Logger()

COMBINED_SUMMARY_FILE_PREFIX = "summary_combined_"
RAW_TEXT_EXTRACTION_FILE_SUFFIX= "_raw_extract"
RAW_TEXT_EXTRACTION_FILE_TYPE= ".txt"
CLEAN_TEXT_EXTRACTION_FILE_SUFFIX= "_clean"
CLEAN_TEXT_EXTRACTION_FILE_TYPE= ".md"
JSON_SUMMARY_FILE_SUFFIX= "_summary"
JSON_SUMMARY_FILE_TYPE= ".json"
SUMMARY_FILE_SUFFIX= "_summary"
SUMMARY_FILE_TYPE= ".md"

test_summarize_legal = "/Users/michasmi/Library/Mobile Documents/iCloud~md~obsidian/Documents/Notes By Michael/Clients/14_RBC"

async def main():
    TEXT_TO_SUMMARIZE =''
    DATA_STRUCTURE = {}
    PROMPT = ""

    summary_type = 'legal'
    print ("sys.argv: ", f"{sys.argv}")
    
    # with open ("sys.argv[0].log", "w") as f:
    # f.write(str(sys.argv))
    PATH_PARAMETER = sys.argv[1] if len(sys.argv) == 2 else test_summarize_legal
    files_to_process = []
    
    if not os.path.exists(PATH_PARAMETER):
        logger.log(f"Error: Folder/File path not found: {sys.argv[1]}",color="RED")
        sys.exit(1)
    
    if os.path.isdir(PATH_PARAMETER):
        for root, dirs, files in os.walk(PATH_PARAMETER):
            for dir in dirs:
                if dir != ".attachments" and dir != ".archive":
                    dir_path = os.path.join(root, dir)
                    # Check if the directory contains a subdirectory named .attachments and is not itself named .attachments
                    if ".attachments" not in os.listdir(dir_path):
                        # Create a directory with the name .attachments
                        os.mkdir(os.path.join(dir_path, ".attachments"))
            
                # Iterate over the files in the current directory (root)
                for file in files:
                    file_path = os.path.join(root, file)
                    if file.endswith(".md"):
                        # Construct the expected _summary.json file path
                        base_filename = os.path.splitext(file)[0]
                        summary_file_path = os.path.join(root, ".attachments", f"{base_filename}_summary.json")
                        
                        # Check if the summary file does not exist
                        if not os.path.exists(summary_file_path):
                            # Add the *_clean.md file path to the files_to_process list
                            files_to_process.append(file_path)
    
    if os.path.isfile(PATH_PARAMETER):
        if PATH_PARAMETER.endswith(".pdf"):
            files_to_process.append(PATH_PARAMETER)
    
    if len(files_to_process) == 0:
        logger.log(f"No PDF files found to process given input: {sys.argv[1]}",color="YELLOW")
        sys.exit(0)     
    
    files_to_process = list(set(files_to_process))
    
    for file in files_to_process:
        clean_text_file = file.replace(".pdf", CLEAN_TEXT_EXTRACTION_FILE_SUFFIX + CLEAN_TEXT_EXTRACTION_FILE_TYPE)
        json_summary_extract_path = file.replace(".pdf", JSON_SUMMARY_FILE_SUFFIX + JSON_SUMMARY_FILE_TYPE)
        if not os.path.isfile(clean_text_file):
            logger.log(f"No cleaned file exists named '{clean_text_file}'. Skipping.",color="YELLOW")
            continue
    
        #Generate a random number between 1 and 250 and divide it by 1000 to get a random delay between .001 and .25 seconds
        delay = 1 + (random.randint(1, 250) / 1000)
        await asyncio.sleep(delay)
        
        # Open the clean extraction file and read the text to summarize
        with open(clean_text_file, 'r') as f:  
            TEXT_TO_SUMMARIZE = f.read()
        
        
        Summary_Type_Dict = { 
            "legal": 
                {
                 "data_structure": {
                    "Title": "Example Document Title",
                    "Summary": "A 3 paragraph summary of the document's content.",
                    "Document Type": "Client Contract",
                    "Execution Date": "2024-01-01",
                    "Effective Date": "2025-03-01",
                    "End or Renewal Date:": "2027-01-01",
                    "Automatic Renewal": True,
                    "Duration": "1 year",
                    "Amendments": ["Amendment 1", "Amendment 2"],
                    "Committed Fees": "$1,000,000",
                    "Parties Involved": ["Party A", "Party B"],
                    "Key Terms": ["Term 1", "Term 2", "Term 3"],
                    "Products or Services": "Hypo Tool, Managed Services, ESG",
                    "Is Addendum": False,
                    "References to Other Documents": ["Document 1", "Document 2"],
                    "Unusual Legal Terms": {
                        "Unlimited Liability": "Present or None",
                        "Broad Indemnification": "Present or None",
                        "Warranty of Performance": "Present or None",
                        "Source Code Escrow": "Present or None",
                        "Unilateral Amendment Rights": "Present or None",
                        "Mandatory Service Level Agreements (SLAs)": "Present or None",
                        "Service Credits": "Present or None",
                        "Most Favored Customer Clause (or Most Favored Nation)": "Present or None",
                        "Extensive Data Privacy Requirements": "Present or None",
                        "Intellectual Property Assignment": "Present or None",
                        "Performance Bonds": "Present or None",
                        "Joint IP Ownership": "Present or None",
                        "Termination at Will or for Convenience": "Present or None",
                        "Assignment Consent": "Present or None"
                    },
                    "Your Commentary": "Any additional commentary or notes you have on the document."}, 
                "term_dict":{ 
                    "Term1": {"Term":   "Termination for Cause", "TermKey": f"{uuid.uuid4()}"},
                    "Term2": {"Term":   "Dispute Resolution", "TermKey": f"{uuid.uuid4()}"},
                    "Term3": {"Term":   "Confidential Information", "TermKey": f"{uuid.uuid4()}"},
                    "Term4": {"Term":   "Intellectual Property", "TermKey": f"{uuid.uuid4()}"},
                    "Term5": {"Term":   "Payment Terms", "TermKey": f"{uuid.uuid4()}"},
                    "Term6": {"Term":   "Initial Term", "TermKey": f"{uuid.uuid4()}"},
                    "Term7a": {"Term":  "Fixed Price", "TermKey": f"{uuid.uuid4()}"},
                    "Term7b": {"Term":  "Favored Customer", "TermKey": f"{uuid.uuid4()}"},
                    "Term8": {"Term":   "Source Code", "TermKey": f"{uuid.uuid4()}"},
                    "Term9": {"Term":   "At Will", "TermKey": f"{uuid.uuid4()}"},
                    "Term10": {"Term":  "Force Majeure", "TermKey": f"{uuid.uuid4()}"},
                    "Term11": {"Term":  "Governing Law", "TermKey": f"{uuid.uuid4()}"},
                    "Term12": {"Term":  "Non-Compete", "TermKey": f"{uuid.uuid4()}"},
                    "Term13": {"Term":  "Non-Disclosure", "TermKey": f"{uuid.uuid4()}"},
                    "Term14": {"Term":  "Third-Party", "TermKey": f"{uuid.uuid4()}"},
                    "Term15": {"Term":  "Indemnification", "TermKey": f"{uuid.uuid4()}"},
                    "Term16": {"Term":  "Confidential", "TermKey": f"{uuid.uuid4()}"},
                    "Term17": {"Term":  "Termination", "TermKey": f"{uuid.uuid4()}"},
                    "Term18": {"Term":  "Performance", "TermKey": f"{uuid.uuid4()}"},
                    "Term19": {"Term":  "Severability", "TermKey": f"{uuid.uuid4()}"},
                    "Term20": {"Term":  "Arbitration", "TermKey": f"{uuid.uuid4()}"},
                    "Term21": {"Term":  "Unilateral", "TermKey": f"{uuid.uuid4()}"},
                    "Term22": {"Term":  "Unlimited", "TermKey": f"{uuid.uuid4()}"},
                    "Term23a": {"Term":  "Indemnify", "TermKey": f"{uuid.uuid4()}"},
                    "Term23b": {"Term":  "Dedicated Team", "TermKey": f"{uuid.uuid4()}"},
                    "Term23c": {"Term":  "Dedicated FTE", "TermKey": f"{uuid.uuid4()}"},
                    "Term23d": {"Term":  "Dedicated Resource", "TermKey": f"{uuid.uuid4()}"},
                    "Term23e": {"Term":  "Dedicated Full", "TermKey": f"{uuid.uuid4()}"},
                    "Term24": {"Term":  "Liability", "TermKey": f"{uuid.uuid4()}"},
                    "Term25": {"Term":  "Mandatory", "TermKey": f"{uuid.uuid4()}"},
                    "Term26": {"Term":  "Assignment", "TermKey": f"{uuid.uuid4()}"},
                    "Term27": {"Term":  "Subcontract", "TermKey": f"{uuid.uuid4()}"},
                    "Term28": {"Term":  "Warrants", "TermKey": f"{uuid.uuid4()}"},
                    "Term29": {"Term":  "Warranty", "TermKey": f"{uuid.uuid4()}"},
                    "Term30": {"Term":  "Favored", "TermKey": f"{uuid.uuid4()}"},
                    "Term31": {"Term":  "Exclusion", "TermKey": f"{uuid.uuid4()}"},
                    "Term32": {"Term":  "Disclaimers", "TermKey": f"{uuid.uuid4()}"},
                    "Term33": {"Term":  "Retention", "TermKey": f"{uuid.uuid4()}"},
                    "Term34": {"Term":  "Penalties", "TermKey": f"{uuid.uuid4()}"},
                    "Term35": {"Term":  "Automatic", "TermKey": f"{uuid.uuid4()}"},
                    "Term36": {"Term":  "Escrow", "TermKey": f"{uuid.uuid4()}"},
                    "Term37": {"Term":  "Cancel", "TermKey": f"{uuid.uuid4()}"},
                    "Term38": {"Term":  "Exceed", "TermKey": f"{uuid.uuid4()}"},
                    "Term39": {"Term":  "Change", "TermKey": f"{uuid.uuid4()}"},
                    "Term40": {"Term":  "Reduce", "TermKey": f"{uuid.uuid4()}"},
                    "Term41": {"Term":  "Nation", "TermKey": f"{uuid.uuid4()}"},
                    "Term42": {"Term":  "Match", "TermKey": f"{uuid.uuid4()}"},
                    "Term43": {"Term":  "Scope", "TermKey": f"{uuid.uuid4()}"},
                    "Term44": {"Term":  "Audit", "TermKey": f"{uuid.uuid4()}"},
                    "Term45": {"Term":  "Fees", "TermKey": f"{uuid.uuid4()}"},
                    "Term46": {"Term":  "Renew", "TermKey": f"{uuid.uuid4()}"},
                    "Term47": {"Term":  "Breach", "TermKey": f"{uuid.uuid4()}"},
                    "Term48": {"Term":  "Penalty", "TermKey": f"{uuid.uuid4()}"},
                    "Term49": {"Term":  "Uptime", "TermKey": f"{uuid.uuid4()}"},
                    "Term50": {"Term":  "Void", "TermKey": f"{uuid.uuid4()}"},
                    "Term51": {"Term":  "Limit", "TermKey": f"{uuid.uuid4()}"}
                    },
            
                    "prompt": f"""
                    Please summarize the following collection of business documents, ensuring that the output is formatted strictly as JSON 
                    without any additional commentary or text. The JSON should include the following fields:

                    1  Title: The title of the document (use the File name at the top if not in the document).
                    2  Summary: A concise summary of the document.
                    3  Document Type: The type of document (Choose one of the following and If the document type is an addendum/ammendment/renewal/extension of another document please state the name and type of the referenced agreement.
                            -- Master Services Agreement With a Client
                            -- Addendum to an Agreement With a Client
                            -- Amendment to an Agreement With a Client
                            -- Agreement Extension With a Client
                            -- Agreement: Data License Agreement With a Data Provider
                            -- Client Subscription Agreement With a Client
                            -- Service Level Agreement With a Client
                            -- Agreement: Vendor or Service Provider With a Vendor or Service Provider to Fincentric
                            -- SOW or Work Order Agreement for Services (with no additional product license or subscription
                            -- Channel Partner Agreemnent  
                            -- Other Document 
                    4  Execution Date: The execution, publish or other main date of the document.
                    5  Effective Date: The date when the document or agreement becomes effective.        
                    6  End or Renewal Date: The date when the document or agreement can be cancelled or renewed.
                    7  Automatic Renewal: If the document or agreement has an automatic renewal clause. (True or False)
                    8  Duration: The duration for which the document or agreement is valid.
                    9  Amendments: Any amendments or changes to previous agreements mentioned.
                    10 Committed Fees: Any fees committed in the document.
                    11 Parties Involved: The main parties involved in the document.
                    12 Key Terms: The key terms and conditions outlined in the document.
                    13 Products or Services: The products or services mentioned, defined, or affected by the document.  Likely product names are:  APIs, Guided Investing, Managed Services, Hypo Tool, Dynamic Video, Data, Conversational UI, ESG, Charting, SmartText, Calculators, Search, User Analytics, SmartShare, Personalization, Options Analysis, Screener, MIND.
                    14 Is Addendum: If the document is an addendum or amendment to another agreement. (True or False)
                    15 References to Other Documents: Any references to other documents or agreements.
                    16 Significant Legal Terms:  Any one-sided, unusual, non-standard, especially advantageous, especially disadvantageous legal terms mentioned. 
                            Please note each of these as "Present" or "None". 
                            16.1.  Unlimited Liability: Clients may seek unlimited liability clauses where the vendor is responsible for any damages, regardless of the amount, which can be financially devastating for the vendor.
                            16.2   Broad Indemnification: Clients often want vendors to indemnify them against a wide range of claims, including intellectual property infringement, data breaches, and other liabilities, which can be costly and risky.
                            16.3   Warranty of Performance: Clients may require extensive warranties regarding the performance, uptime, and functionality of the software, leading to potential legal and financial exposure if the software fails to meet these stringent standards.
                            16.4   Source Code Escrow: Clients may ask for a source code escrow agreement, where the source code is deposited with a third party and can be released to the client under certain conditions, potentially compromising the vendor's intellectual property.
                            16.5   Unilateral Amendment Rights: Clients might include terms that allow them to unilaterally amend the agreement, which could lead to unexpected and unfavorable changes for the vendor.
                            16.6   Mandatory Service Level Agreements (SLAs): Strict SLAs with severe penalties for non-compliance can be financially burdensome and operationally challenging for vendors to meet consistently.
                            16.7   Service Credits: Clients may demand service credits for downtime or service failures, reducing the vendor's revenue, certainty of revenue and profitability.
                            16.8   Most Favored Customer Clause (or Most Favored Nation): Clients may want assurances that they will receive the best terms and pricing compared to any other client, which can limit the vendor's pricing flexibility and profitability.
                            16.9   Extensive Data Privacy Requirements: Clients may impose strict data privacy and protection requirements that exceed standard regulations, increasing compliance costs and complexity for the vendor.
                            16.10  Intellectual Property Assignment: Clients might demand ownership or co-ownership of intellectual property developed under the agreement, which can hinder the vendor's ability to reuse and monetize their work.
                            16.11  Performance Bonds: Clients may require performance bonds or other financial guarantees to ensure the completion of the project, tying up the vendor's capital and adding financial risk.
                            16.11  Joint IP Ownership: Clients may seek joint ownership of intellectual property developed under the agreement, which can complicate licensing, commercialization, and future development efforts.
                            16.12  Termination at Will or for Convenience: Clients may include terms that allow them to terminate the agreement at any time or for any reason, which can leave the vendor vulnerable to sudden revenue loss and operational disruption.
                            16.13  Assignment Consent: Clients may require the vendor's consent for any assignment of the agreement, limiting the vendor's ability to transfer rights and obligations to other parties.
                    17 Your Commentary: Any additional commentary or notes you have on the document. Pretend you are Fincentric (also known as Market on Demand, MoD, Wall Street on Demand, WSOD, and S&P),
                                        would are the terms of a contract or document disadvantageous? Are there any terms that are particularly advantageous? If this text is not a contract, please comment on
                                        how the document could be improved or what the document is missing.
                    
                    Response structure should be a single JSON dictionary as follows (the values are examples and should be replaced with the actual data you generate):
                    {json.dumps(DATA_STRUCTURE, indent=4)}
            
                    If a field is not present in the document and cannot be inferred, please put "None" as the Value.
                    
                    ## Document Text ##
                    {TEXT_TO_SUMMARIZE}
                    ## End of Document Text ##
                    """
            }
        }
        
        print("Value of Summary Type: ", summary_type)
        DATA_STRUCTURE = Summary_Type_Dict[summary_type]['data_structure']
        PROMPT = Summary_Type_Dict[summary_type]['prompt']
        TERM_DICT = Summary_Type_Dict[summary_type]['term_dict']
        
        clean_dict = await get_gemini_summary(PROMPT, json_summary_extract_path, clean_text_file, TERM_DICT, summary_type)
        print(clean_dict)
    
def json_to_markdown(json_dict, level=3):
    """
    Converts a JSON dictionary to a Markdown string with specific formatting.

    Parameters:
    json_dict (dict): The JSON dictionary to convert.
    level (int): The header level for the keys.

    Returns:
    str: The resulting Markdown string.
    """
    markdown_lines = []

    for key, value in json_dict.items():
        # Determine header level and color
        header_level = '#' * level
        header_color = "#00b0f0" if level == 3 else "#0073e6"  # Lighter blue for nested headers
        
        # Convert the key to a header
        header = f'{header_level} <font color="{header_color}">{key}</font>'
        markdown_lines.append(header)
        markdown_lines.append('---')
        
        # Handle different types of values
        if isinstance(value, dict):
            # Recursively handle nested dictionary
            nested_markdown = json_to_markdown(value, level + 1)
            markdown_lines.append(nested_markdown)
        elif isinstance(value, list):
            # Turn list into a bulleted list
            for item in value:
                if isinstance(item, (int, float)):
                    item = f'<span style="background:#b1ffff">**{item}**</span>'
                elif item == "Present":
                    item = f'<font color="#ff0000"><strong>{item}</strong></font>'
                markdown_lines.append(f'- {item}')
        elif isinstance(value, (int, float)):
            # Numeric value, make it bold and purple
            formatted_value = f'<span style="background:#b1ffff">**{value}**</span>'
            markdown_lines.append(formatted_value)
        elif value == "Present":
            # Value is "Present", make it bold and red
            formatted_value = f'<font color="#ff0000"><strong>{value}</strong></font>'
            markdown_lines.append(formatted_value)
        else:
            # Plain text value
            markdown_lines.append(value)
        
        # Add a blank line after each key-value pair for better readability
        markdown_lines.append('')

    # Join all lines into a single Markdown string
    markdown_content = '\n'.join(markdown_lines)
    return markdown_content

async def get_gemini_summary(PROMPT, summary_extract_path, clean_extract_path, term_dict, summary_type):
        
    def apply_tags_to_text(new_clean_md, term_dict, summary_type):
        def replace_case_insensitive(text, word, replacement):
                # Define a case-insensitive regular expression pattern for the word
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                # Replace occurrences in the text
                return pattern.sub(replacement, text)
        
        
        #! Remove any existing tags
        # Replace existing tags with their corresponding TermKeys
        for key in term_dict.keys():
                Term = term_dict[key]
                new_clean_md = replace_case_insensitive(new_clean_md, f"#{summary_type}/{Term['Term'].replace(' ', '_')}", Term['TermKey'])
        #! Remove any existing tags
        # Replace existing TermKeys with their corresponding terms (without tags)
        for key in term_dict.keys():
            Term = term_dict[key]
            new_clean_md = replace_case_insensitive(new_clean_md, Term['TermKey'],Term['Term'])
        
        
        #! Add new tags
        # Replace matching terms with their corresponding TermKey
        for key in term_dict.keys():
                Term = term_dict[key]
                new_clean_md = replace_case_insensitive(new_clean_md, Term['Term'], Term['TermKey'])
        #! Add new tags
        # Replace matching TermKeys with their corresponding Markdown tags
        for key in term_dict.keys():
            Term = term_dict[key]
            new_clean_md = replace_case_insensitive(new_clean_md, Term['TermKey'],f"#{summary_type}/{Term['Term'].replace(' ', '_')}")
        
        return new_clean_md
        
    def extract_json_dict_from_llm_response(content):
        
        
        def try_to_json(input_value):
            try:
                return json.loads(input_value)
            except:
                pass
            try:
                return json.loads(f"[{input_value}]")
            except:
                return input_value
        
        # Find the first '{' and the last '}'
        start_idx = content.find('{')
        end_idx = content.rfind('}')

        if start_idx == -1 or end_idx == -1:
            return None

        try:
            # Extract the JSON string
            json_string = content[start_idx:end_idx + 1]
            
            json_dict = try_to_json(json_string)
            if  isinstance(json_dict, dict) or isinstance(json_dict, list):
                return json_dict
            else:
                return None
        except Exception as e:
            return None
    
    
    if not os.path.exists(summary_extract_path):
        
        key = os.environ.get('GEMINI_API_KEY')
        genai.configure(api_key=key)

        model = genai.GenerativeModel('gemini-1.5-flash')

        response = model.generate_content(PROMPT,
            generation_config=genai.types.GenerationConfig(
                candidate_count=1,
                temperature=0.2))
        
        valid_dict = extract_json_dict_from_llm_response(response.text)
        
        if valid_dict:
            with open(summary_extract_path, 'w') as f:
                json.dump(valid_dict, f, indent=4)
            
            with open(clean_extract_path, 'r') as f:  
                clean_md = f.read()
                summary_md = json_to_markdown(valid_dict)
                
                new_clean_md = f"{summary_md}\n\n\n{clean_md}"
                new_clean_md = new_clean_md.replace(f"|##| |", f"## ")
                apply_tags_to_text(new_clean_md, term_dict, summary_type)
            
            with open(clean_extract_path, 'w') as f:
                f.write(new_clean_md)
                
            return valid_dict
        
        else:
            with open(summary_extract_path, 'w') as f:
                f.write(response.text)
            return response.text
    
    else :        
        with open(clean_extract_path, 'r') as f:  
                clean_md = f.read()
        
        # Reapply Tags
        clean_md = apply_tags_to_text(clean_md, term_dict, summary_type)
        
        with open(clean_extract_path, 'w') as f:
            f.write(clean_md)

            
    
    
    
if __name__ == '__main__':
    asyncio.run(main())