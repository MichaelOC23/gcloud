import streamlit as st
# from _class_streamlit import streamlit_mytech   
# stm = streamlit_mytech("CSV to Dictionary Converter/Loader", session_state_variables=[
#                     {"DF_OF_CSV": None},
#                     {"COLUMN_LIST": []},
#                     {"UNIQUE_COLUMN_LIST": []},
#                     {"SELECTED_KEY": ''},], auth=True)

import pandas as pd
import re
import chardet



def main():
    # File uploader
    uploaded_file = st.file_uploader("Upload a CSV file", type="csv")
    if uploaded_file is not None:
        analyze_csv(uploaded_file)
        
def analyze_csv(csv_path):
    progress_bar = st.progress(0)
    mc1, mc2, mc3, mc4, mc5, mc6 = st.columns([1,1,1,1,1,1])
    m1 = mc1.empty()
    m2 = mc2.empty()
    m3 = mc3.empty()
    m4 = mc4.empty()
    m5 = mc5.empty()
    m6 = mc6.empty()
    
    # Define pattern to detect special characters (excluding ., ,, /, $, @, &, -, :, ;, %, _)
    special_char_pattern = re.compile(r'[^a-zA-Z0-9_ /$@&-:;%,.]+')
    

    def check_special_characters(text):
        return special_char_pattern.findall(text)

    st.session_state['ENCODING'] = detect_encoding(csv_path)
    m1.metric("Encoding", st.session_state['ENCODING']) 
    df = create_typed_df(csv_path, st.session_state['ENCODING'], 50)
    st.session_state["DF_OF_CSV"] = df
    col_count = len(df.columns)
    row_count= df.shape[0]
    m2.metric("Rows/Columns", f"{row_count}/{col_count}")
    
    # Show dataframe and headers
    st.subheader("Data Preview:", divider=True)
    st.write(st.session_state["DF_OF_CSV"].head(10))
    st.divider()
    
    st.session_state["COLUMN_LIST"] = st.session_state["DF_OF_CSV"].columns.tolist()
    with st.expander("Column List"):
        st.table(st.session_state["COLUMN_LIST"])
    
    # Check for duplicate headers
    duplicates = set()
    if len(st.session_state["COLUMN_LIST"]) != len(set(st.session_state["COLUMN_LIST"])):
        st.write("Warning: Duplicate headers detected.")
        duplicates = set([header for header in st.session_state["COLUMN_LIST"] if st.session_state["COLUMN_LIST"].count(header) > 1])
        st.error(f"Duplicate headers: {duplicates}")
    else:
        st.info("No duplicate headers detected.")
    m3.metric("Duplicate Headers", len(duplicates))
    
    # Check for special characters in headers
    spec_char_count = 0
    progress_bar.progress(0)
    spec_exp = st.expander("Rows With Special Characters")
    for index, row in df.iterrows():
        progress_bar.progress((index + 1) / df.shape[0], 'Checking for special characters ...')
        for column in df.columns:
            value = row[column]
            if not isinstance(value, str):
                continue
            if 'http' in value or 'www.' in value or column.lower() in ["url", 'website', 'site']:
                continue
                
            check = check_special_characters(f"{value}")
            if check:
                spec_char_count += 1
                spec_exp.write(f"SPECIAL CHARACTERS: Row {index}, Column {column}: {value}")
    m4.metric("Special Characters", spec_char_count)
    
    # Process each row
    mismatched_rows = 0
    progress_bar.progress(0)
    mismatch_exp = st.expander('Rows With Mismatched Row Count')
    for row_number, row in df.iterrows():
        # Check if row length matches header length
        progress_bar.progress((row_number + 1) / df.shape[0], 'Checking for column count mismatches ...')
        if len(row) != len(st.session_state["COLUMN_LIST"]):
            mismatched_rows += 1
            mismatch_exp.write(f"Row {row_number + 1} has a mismatch in number of columns (expected {len(st.session_state["COLUMN_LIST"])}, got {len(row)}).")
    m5.metric("Mismatched Row Count", mismatched_rows)

    # Check for mixed data types in columns
    progress_bar.progress(0)
    count =0
    MixedDataTypes = st.expander('Mixed Data Types')
    for col in df.columns:
        count += 1
        progress_bar.progress((count) / len(df.columns), 'Checking for mixed data types ...')
        if df[col].apply(type).nunique() > 1:
            MixedDataTypes.write(f"Column '{col}' contains mixed data types.")
    m6.metric("Mixed Type Columns", count)
    
    # Check for trailing delimiters (extra empty columns)
    if len(df.columns) != len(st.session_state["COLUMN_LIST"]):
        st.warning("Warning: Detected trailing delimiters leading to extra columns.")
    

    print("CSV analysis complete.")


def clean_str(str_text):
    clean_col = re.sub(r'\W+', '', str_text.lower())
    clean_col = f"{clean_col.replace('"', '')}"
    return clean_col

def create_typed_df(file_path, encoding, max_rows=1000):
    
    def check_convertible_to_datetime(column):
        def is_convertible(value):
            if pd.isnull(value) or value == '':
                return True
            try:
                pd.to_datetime(value)
                return True
            except (ValueError, TypeError):
                return False
        return column.apply(is_convertible).all()

    def is_numeric_or_empty(s):
        s_float = pd.to_numeric(s, errors='coerce')
        return s_float.notna() | s.isna()
    
    def sanitize_col_names(df):
        # Create a dictionary to safely rename the fields
        rename_dict = {}
        df.columns = df.columns.str.strip()
        for col in df.columns:
            clean_col_name = clean_str(col)
            rename_dict[col] = clean_col_name.strip()
        df = df.rename(columns=rename_dict)
        return df

    # Reading the CSV file
    file_path.seek(0)
    df = pd.read_csv(file_path, on_bad_lines='warn', encoding=encoding)
    
    # Process each column
    for col in df.columns:
        sample = df[col].iloc[:max_rows]
        
        if is_numeric_or_empty(sample).all():
            # Set its type to number
            df[col] = df[col].replace(r'^\s*$', '0', regex=True).fillna('0')
            try:
                df[col] = df[col].astype(float).fillna(0)
            except ValueError:
                continue
            
        elif check_convertible_to_datetime(sample):
            try:
                # Set its type to datetime
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except ValueError:
                continue
        else:
            df[col] = df[col].astype(str).replace({pd.NA: None, 'nan': None, 'NaT': None, None: None, '<NA>': None})

        
        # Set all string and date columns to None (to be more consistent in replacement)
        df[col] = df[col].replace({pd.NA: None, 'nan': None, 'NaT': None, None: None, '<NA>': None})

    # Sanitize column names
    df = sanitize_col_names(df)
    
    # Clean Up Tasks
    # 1. Remove empty rows and columns
    df = df.replace('', pd.NA).dropna(how='all')  # Replace empty strings with pd.NA and drop completely empty rows
    
    # 2. Ensure no whitespace in column names
    df.columns = df.columns.str.strip()
    
    # 3. Remove newline characters from all fields in the DataFrame
    def sanitize_cell(x):
        if isinstance(x, str):
            return x.replace('\n', ' ').replace('\r', ' ')
        else:
            return x

    # Apply the sanitize_cell function to each element in the DataFrame
    df = df.apply(lambda column: column.map(sanitize_cell))

    
    # 4. Drop rows where all elements are NaN (if it's not redundant with step 1)
    df = df.dropna(how='all')
    
    # 5. Handle NaNs for specific types
    for col in df.columns:
        if pd.api.types.is_integer_dtype(df[col]):
            df[col] = df[col].fillna(0).astype(pd.Int64Dtype())  # Handle integer columns with NaNs
        elif pd.api.types.is_float_dtype(df[col]):
            df[col] = df[col].fillna(0.0)  # Handle float columns with NaNs
        elif pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].fillna('')  # Handle string columns with NaNs
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].fillna(pd.Timestamp('1970-01-01'))  # Handle datetime columns with NaNs
    
    # 6. Reset the index after dropping rows
    df = df.reset_index(drop=True)
    
    return df

# Function to detect encoding
def detect_encoding(uploaded_file):
    result = chardet.detect(uploaded_file.read())
    if result['encoding'] == 'ascii':
        return 'utf-8'
    return result['encoding']

main()
if __name__ == "__main__":
    pass
    
    
    
        # Dropdown to select the header
        # selected_header = st.selectbox("Select key header", df.columns, key='header_selection' ,placeholder='Choose ...')
        
        # if selected_header:
        #     # Create a dictionary
        #     result_dict = df.set_index(selected_header).to_dict(orient="index")
            
        #     # Display dictionary
        #     st.write("Generated Dictionary:")
        #     st.json(result_dict)

        #     # Option to download the dictionary as JSON
        #     st.download_button("Download Dictionary as JSON", 
        #                        data=pd.json.dumps(result_dict), 
        #                        file_name="output.json", 
        #                        mime="application/json")
