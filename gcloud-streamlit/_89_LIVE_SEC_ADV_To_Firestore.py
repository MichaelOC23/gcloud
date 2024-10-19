import os
import pandas as pd
import chardet
import re
import asyncio

class RIAsToFirestore:
    def __init__(self):
        self.something = ''
        

    def type_df(self, file_path, encoding, max_rows=1000):
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
                clean_col_name = clean_str(col, "c")
                rename_dict[col] = clean_col_name.strip()
            df = df.rename(columns=rename_dict)
            return df
        
        def clean_str(str_text, prefix=None):
            if prefix is None:
                prefix = 'c'
            clean_col = re.sub(r'\W+', '', str_text.lower())
            clean_col = f"{prefix}{clean_col.replace('"', '')}"
            return clean_col

        # Reading the CSV file
        print(f"About to read csv {os.path.basename(file_path)} with encoding: {encoding}")
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
    
    def detect_encoding(self, file_path):
        with open(file_path, 'rb') as f:
            result = chardet.detect(f.read())
            return result['encoding']
    
    async def load_rias_to_firestore(self, csv_file_path, column_name_dict):
        
        # encoding =  self.detect_encoding(csv_file_path)
        df =  self.type_df(csv_file_path, 'ISO-8859-1')
        
        lc_name_dict = {}
        for key in column_name_dict.keys():
            lc_name_dict[key.lower()] = column_name_dict[key]
        
        df_renamed = df.rename(columns=lc_name_dict)
        
        list_of_ria_dicts = df_renamed.to_dict('records')
        
        from _class_firebase import FirestoreStorage
        db = FirestoreStorage()
        total = len(list_of_ria_dicts)
        count = 0
        for ria_dict in list_of_ria_dicts:
            count+=1
            await db.insert_dictionary('ria-firm',ria_dict, ria_dict.get('CRDNumber') )
            await db.insert_dictionary('ria-firm-filings',ria_dict, f"Filing-{ria_dict.get('FilingId')}")
            print(f'{count} of {total}')
            

if __name__ == '__main__':

    def main(column_name_dict):
        
        riatofs = RIAsToFirestore()
        asyncio.run(riatofs.load_rias_to_firestore('/Users/michasmi/Downloads/Goldmine/UsefulPart01/IA_ADV_Base_A_20240101_20240331.csv', column_name_dict))
    

    column_name_dict = {

        #c Firm
        "c1A": "Legal Name",
        "c1D": "CRDNumber",
        "cBusiness Name": "Business Name",
        "cPrimary Business": "Business Description",
        "cOther Products and Services": "Other Offerings",



        #cAUM Breakdown
        "c5F1": "Manage Portfolios",
        "c5F2a": "Discretionary AUM",
        "c5F2b": "Non-Discretionary AUM",
        "c5F2c": "Total AUM",
        "c5F3": "Foreign Part of AUM",

        #c Filing Contacts
        "cSignatory": "Exec1 Name - CCO",
        "cTitle": "Exec1 Title",
        "cReg Contact-Name": "Exec2 Name",
        "cReg Contact-Title": "Exec2 Title",
        "cReg Contact-Phone": "Exec2 Phone",
        "cReg Contact-Email": "Exec2 Email",
        "c1J2-Name": "CCO Name",
        "c1J-Email": "CCO Email",
        
        #c Executing Exec
        "Signatory": "Exec Name",
        "Title": "Exec Title",

        #c Main Office Location
        "c1F1-Street 1": "Address 1",
        "c1F1-Street 2": "Address 2",
        "c1F1-City": "City",
        "c1F1-State": "State",
        "c1F1-Country": "Country",
        "c1F1-Postal": "Postal Code",

            #c Client Segmentation
        "c5C1": "AdviceOnly Clients",
        "c5C2": "Foreign Client Percentage",
        "c5D1a": "NonHNW Clients",
        "c5D1b": "HNW Clients",
        "c5D1c": "Bank Clients",
        "c5D1d": "Invest. Co. Clients",
        "c5D1e": "Bus Dev Co",
        "c5D1f": "Pooled Vehicles",
        "c5D1g": "Pension Sponsor Clients",
        "c5D1h": "Charity Clients",
        "c5D1i": "Gov Clients",
        "c5D1j": "Other Inv. Advisor Clients",
        "c5D1k": "Insurance Co. Clients",
        "c5D1l": "Sovereign Wealth Clients",
        "c5D1m": "Corporate Clients",
        "c5D1n": "Other Clients",
        "c5D1n Other": "Other Description",
        "c5D2a": "Under 5 Non-HNW Clients",
        "c5D2b": "Under 5 HNW Clients",
        "c5D2c": "Under 5 Bank Clients",
        "c5D2g": "Under 5 Pension Sponsor Clients",
        "c5D2h": "Under 5 Charity Clients",
        "c5D2i": "Under 5 Gov. Clients",
        "c5D2j": "Under 5 Other Inv. Advisor Clients",
        "c5D2k": "Under 5 Insurance Co. Clients",
        "c5D2l": "Under 5 Sovereign Wealth Clients",
        "c5D2m": "Under 5 Corporate Clients",
        "c5D2n": "Under 5 Other Clients",
        "c5D3a": "Non-HNW AUM",
        "c5D3b": "HNW AUM",
        "c5D3c": "Bank AUM",
        "c5D3d": "Invest. Co. AUM",
        "c5D3e": "Bus. Dev. Co. AUM",
        "c5D3f": "Pooled Vehicle AUM",
        "c5D3g": "Pension Sponsor AUM",
        "c5D3h": "Charity AUM",
        "c5D3i": "Gov. AUM",
        "c5D3j": "Other Inv. Advisor AUM",
        "c5D3k": "Insurance Co. AUM",
        "c5D3l": "Sovereign Wealth AUM",
        "c5D3m": "Corporate AUM",
        "c5D3n": "Other AUM",
        "c5F1": "Manage Portfolios",
        "c5F2a": "Discretionary AUM",
        "c5F2b": "Non-Discretionary AUM",
        "c5F2c": "Total AUM",

        #c Firm Size
        "c5A": "Total Employees",
        "c5B1": "Advisory Employees",
        "c5B2": "Registerd Reps",
        "c5B3": "Registered Advisors",
        "c5B4": "Affiliated Advisors",
        "c5B5": "Insurance Advisors",
        "c5B6": "3rdParty Solicitors",
        "c1O": "Greater than 1B Ent. Val.",
        "c1M": "Intl Registered",
        "c1L": "Maintain Book of Record",
        "c1N": "Public Reporting Company",
        "c1F1-Private": "Is a Residential Address",

        #c Firm Structure
        "c6A1": "Broker Dealer",
        "c6A2": "Registered BD Rep",
        "c6A5": "Real Estate Brokerage",
        "c6A6": "Insurance Brokerage",
        "c6A7": "Bank",
        "c6A8": "Trust Company",
        "c6A9": "Municipal Advisor",
        "c9A1a": "Custody Client Cash",
        "c9A1b": "Custody Client Securities",
        "c9A2a": "Custody AUC",
        "c9A2b": "Custody Accounts",
        "c12A": "Greater than 5m AUM",
        "c12B1": "Ownership of Advisory Firm",
        "c12C1": "Control of Indiv. Advisor",
        "c12C1": "Share Oversigh Co.",
        "c12C2": "Share Oversight Person",
        "c2A1": "Large Advisory Firm",
        "c2A2": "Mid Advisory Firm",
        "c2A4": "US Based",
        "c2A5": "Subadvisor",
        "c2A6": "Advisor of BDC",
        "c2A7": "Pension Consultant",
        "c2A8": "Related Advisor",
        "c2A9": "Expect Reg. Elig.",
        "c2A10": "Multi-Staet Advisor",
        "c2A11": "Internet Advisor",
        "c2A13": "Uneligible for Reg.",

        #c Accounts
        "c5F2d": "Discretionary Accts",
        "c5F2e": "Non-Discretionary Accts",
        "c5F2f": "Total Accts",

        #c Revenue
        "c5E1": "Comp-AUM Fee",
        "c5E2": "Comp-Hourly Fee",
        "c5E3": "Comp-Subscription",
        "c5E4": "Comp-Fixed Fee",
        "c5E5": "Comp-Commission",
        "c5E6": "Comp-Performance Fee",
        "c5E7": "Other Fee",
        "c5E7-Other": "Other Fee Description",

        #c Services Offered
        "c5G1": "Financial Planning",
        "c5G2": "Portfolio Management for Indiv.",
        "c5G3": "Portfolio Management for Invest. Co.",
        "c5G4": "Portfolio Management for Pooled Vehic.",
        "c5G5": "Portfolio Management for Businesses",
        "c5G6": "Penson Consulting",
        "c5G7": "Adviser Selection",
        "c5G8": "Media Publication",
        "c5G9": "Ratings and Pricing",
        "c5G10": "Market Timing",
        "c5G11": "Education",
        "c5G12": "Other",
        "c5G12-Other": "Other Activity",
        "c5H": "Fin Plan Clients",
        "c5H-Other": "Fin Plan Clients Large",
        "c5I1": "Use SMA Program",
        "c5I2a": "SMA Program Sponsor AUM",
        "c5I2b": "SMA Product Mgt AUM",
        "c5I2c": "Sponsor to Other Manager",
        "c5J1": "Product Advice Limited",

        #c Identifiers
        "c1P": "Legal Entity Id",
        "cCIK Number": "CIK", 
        "cFilingID" :"FilingId", 
        "cReferenceID": "ReferenceID",
        }

        
    main(column_name_dict)
    
    
    

    
    
    
    