import streamlit as st
import concurrent.futures

from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
import uuid
import time
import os
import sys
import pandas as pd
import numpy as np

import csv

sys.path.append(os.path.abspath("/Users/michasmi/code/mytech/classes"))
from _class_streamlit import streamlit_mytech 

stm = streamlit_mytech()
stm.set_up_page(page_title_text="Policy and Tactical Asset Allocation", 
                session_state_variables=[{"TransStatus": False}]) 




class gmtc_data():
    def __init__(self):
        self.account_holdings = None
        self.account_positions = None
        self.account_securities = None
        self.account_transactions = None
        self.account_performance = None
        self.account_models = None
        self.account_groups = None
        self.account_employees = None
        self.employee_account_coverage = None
        self.account_portfolios = None
        
        self.load_all_data()
     
    def load_all_data(self):
        start_time = time.time()
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # Submit tasks to the ProcessPoolExecutor
            futures = {
                'account_holdings': executor.submit(self.get_data, 'account_holdings.csv'),
                'account_transactions': executor.submit(self.get_data, 'account_transactions.csv'),
                'account_performance': executor.submit(self.get_data, 'account_performance.csv'),
                'account_models': executor.submit(self.get_data, 'account_models.csv'),
                'account_groups': executor.submit(self.get_data, 'account_groups.csv'),
                'employees': executor.submit(self.get_data, 'account_employees.csv'),
                'employee_account_coverage': executor.submit(self.get_data, 'employee_account_coverage.csv'),
                'account_portfolios': executor.submit(self.get_data, 'account_portfolios.csv')
            }

            # Collect the results as they complete
            for key, future in futures.items():
                setattr(self, key, future.result())

        # Create the security master
        smf_start_time = time.time()
        self.account_securities = self.account_holdings[['marketprice', 'issuename1', 'maturitydate', 'moodyrating',
                                                         'assetclass', 'assetsubclass', 'amortization', 'assetsector',
                                                         'expirationdate', 'cusip', 'ticker', 'eps', 'minsecclass',
                                                         'vchshortname', 'priceaspercent', 'gpemplid', 'sma',
                                                         'calldate', 'issuename2']]
        self.account_securities = self.account_securities.drop_duplicates()
        print(f"\033[1;96mTime to get Security Master: {time.time() - smf_start_time}\033[0m")
        print(f"\033[1;96mTime to get ALL FILES: {time.time() - start_time}\033[0m")
    
    def get_data(self, filename):
        with open(f'gmtc/{filename}') as f:
            
            start_time = time.time()
            
            # Read the first line (header)
            header = f.readline().strip().split(',')
            
            # Clean the header: lowercase and remove spaces
            clean_header = [col.strip().replace(' ', '_').lower() for col in header]

            # Load the rest of the file into a DataFrame using the cleaned header
            df = pd.read_csv(f, names=clean_header, dtype=str)
            
            # Drop rows where all elements are NaN
            df = df.dropna(how='all')
            
            # Remove \n from all fields in the DataFrame
            df = df.apply(lambda col: col.apply(lambda x: x.replace('\n', ' ').replace('\r', ' ') if isinstance(x, str) else x))
            
            
            
            # Reset the index after dropping rows
            df = df.reset_index(drop=True)
            
            cast_log = []
            df = self.inspect_and_cast(df, cast_log, filename)
            
            with open(f'gmtc/{filename}.log', 'w') as f:
                f.write('\n'.join(cast_log))
            
            #! Custom Logic for gmtc files
            if 'portnum' in df.columns:
                df['accountnum'] = df['portnum'].str.replace(r'\.\d+$', '', regex=True)
            
            if 'holdings' in filename:
                # Step 1: Create the 'secid' column with the value of 'ticker'
                df['secid'] = df['ticker']

                # Step 2: Where 'ticker' is empty/blank/null, set 'secid' to 'cusip'
                df['secid'] = np.where(df['secid'].isnull() | df['secid'].str.strip().eq(''), df['cusip'], df['secid'])

                # Step 3: Set any remaining blanks in 'secid' to 'USD'
                df['secid'] = df['secid'].replace('', 'USD')
                df['secid'] = df['secid'].fillna('USD')
            
            print(f"\033[1;96mTime to get {filename}: {time.time() - start_time}\033[0m")
            return df 
       
    def inspect_and_cast(self, df, cast_log = [], ref_name=''):
        
        def is_numeric_or_empty(s):
            # Check if a column is entirely numeric or empty/NaN
            try:
                s_float = pd.to_numeric(s, errors='coerce')
                return s_float.notna() | s.isna()
            except ValueError:
                return False

        def optimize_dataframe(df, max_rows=50):
            for col in df.columns:
                # Limit the number of rows checked to max_rows
                sample = df[col].iloc[:max_rows]

                if 'targetmin' in col:
                    pass
                
                if is_numeric_or_empty(sample).all():  # Check if all values in the sample are numeric or empty
                    # Replace any empty strings or spaces with '0'
                    df[col] = df[col].replace(r'^\s*$', '0', regex=True)
                    df[col] = df[col].fillna('0')  # Replace NaN with '0'
                    
                    # Attempt to convert the column to float
                    try:
                        df[col] = df[col].astype(float)
                        print(f"\033[0;32mSuccessfully converted  column '{ref_name} | {col}' numeric values.\033[0m")
                    except ValueError:
                        pass
                        print(f"Skipping conversion for column '{ref_name} | {col}' due to non-numeric values.")
                        continue
            return df
            
        time_start = time.time()
        
        #step 1: Convert all the numeric columns to float
        df = optimize_dataframe(df)
        # print(f"Time to clean numeric columns: {time.time() - time_start}")
        
        # Step 2: Format the numeric columns with two decimal places and thousand separators
        for col in df.select_dtypes(include=[float, int]).columns:
            df[col] = df[col].apply(lambda x: "{:,.2f}".format(x) if pd.notnull(x) else x)
        # print(f"Time to format numeric columns: {time.time() - time_start}")
        
        # Iterate over each column in the DataFrame
        for col in df.columns:
            if df[col].apply(self.is_date_or_empty).all():  # Check if all values are dates or empty
                df[col] = pd.to_datetime(df[col], errors='coerce')  # Cast the column to datetime
        
        # Fill NaN or NaT with empty string for non-numeric, non-date columns
        # Note that numeric columns are already converted to float and filled with '0'
        # So this will only affect non-numeric columns
        df[col] = df[col].fillna('')  
        
        return df
 
    def is_none_or_empty(self, df):
            resp = True
            try:
                return df is None or df.empty
            except:
                return resp
   
    def is_null_or_empty(self, val):
        if pd.isnull(val):  # Check for NaN or None
            return True
        val_str = str(val).strip()  # Convert to string and strip whitespace
        if val_str == '':  # Check if it's empty after stripping
            return True
        
        return False    
        
    def is_numeric_or_empty(self, val):
        if pd.isnull(val):  # Check for NaN or None
            return True
        val_str = str(val).strip()  # Convert to string and strip whitespace
        if val_str == '':  # Check if it's empty after stripping
            return True
        try:
            float(val_str)  # Try to convert to float
            return True
        except ValueError:
            return False        

    def is_date_or_empty(self,val):
        if pd.isnull(val):  # Check for NaN or None
            return True
        val_str = str(val).strip()  # Convert to string and strip whitespace
        if val_str == '':  # Check if it's empty after stripping
            return True
        try:
            pd.to_datetime(val_str)  # Try to convert to datetime
            return True
        except (ValueError, TypeError):
            return False
            
    def get_data_by_name(self, name):
        return getattr(self, name)
    
    def get_all_data(self):
        all_dfs = []
        for attr in dir(self):
            if 'account' in attr and 'dtype' not in attr:
                all_dfs.append([attr, getattr(self, attr)])
        return all_dfs


class create_new_grid():
    def __init__(self, 
                 col_val_list=None,
                 # Column Options
                 minWidth=100,
                 maxWidth=400, 
                 editable=True, 
                 filter=True, 
                 resizable=True, 
                 sortable=True, 
                 enableRowGroup=True, 
                 enablePivot=True,  # Ensure enablePivot is set to True
                 currency_symbol='$',

                 # Grid Options
                 rowSelection="multiple", 
                 use_checkbox=True,
                 rowMultiSelectWithClick=False, 
                 suppressRowDeselection=False, 
                 suppressRowClickSelection=False, 
                 groupSelectsChildren=True, 
                 groupSelectsFiltered=True, 
                 preSelectAllRows=False,
                 enable_pagination=True,

                 # Sidebar Options
                 show_SideBar=True,
                 show_filters=False,
                 show_columns=True,
                 show_defaultToolPanel=True,
                 hide_by_default=False
                 ):
        
        # if dataframe is None:
        #     print ('ERROR: No dataframe provided')
        #     return
        
        self.show_SideBar = show_SideBar
        self.show_filters = show_filters
        self.defaultToolPanel = show_defaultToolPanel
        self.show_columns = show_columns
        self.minWidth = minWidth
        self.maxwidth = maxWidth
        
        # self.dataframe = dataframe
        self.col_val_list = col_val_list
        
        self.editable = editable
        self.filter = filter
        self.resizable = resizable
        self.sortable = sortable
        self.enableRowGroup = enableRowGroup
        self.enablePivot = enablePivot
        self.rowSelection = rowSelection
        self.use_checkbox = use_checkbox
        self.enable_pagination = enable_pagination
        self.rowMultiSelectWithClick = rowMultiSelectWithClick
        self.suppressRowDeselection = suppressRowDeselection
        self.suppressRowClickSelection = suppressRowClickSelection
        self.groupSelectsChildren = groupSelectsChildren
        self.groupSelectsFiltered = groupSelectsFiltered
        self.preSelectAllRows = preSelectAllRows
        self.currency_symbol = currency_symbol
        self.hide_by_default = hide_by_default
        
    def create_default_grid(self, dataframe):
          
        if self.is_none_or_empty(dataframe):
            print ('ERROR: No dataframe provided')
            return
        # Apply formatting and right alignment to numeric columns in Ag-Grid
        
        builder = GridOptionsBuilder.from_dataframe(dataframe)
        
        builder.configure_selection(self.rowSelection  , self.use_checkbox)
        builder.configure_pagination(self.enable_pagination)
        builder.configure_side_bar(self.show_filters, self.show_columns, self.defaultToolPanel)  # Enable the sidebar with default options

        # for col in dataframe.select_dtypes(include=[float, int]).columns:
        #     builder.configure_column(col, type=["numericColumn", "customNumericFormat"], precision=2, valueFormatter="x.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })", cellStyle={'text-align': 'right'})
        
        # Add enablePivot option to column definitions
        gridoptions = builder.build()
        gridoptions['enableCharts'] = True  
        gridoptions['enableRangeSelection'] = True
        
        


        new_col_defs = []
        for col_list_item in gridoptions['columnDefs']:
            # !FIXME: Figure out Col Name Override
            # col_list_item['headerName']= col['headerName']            
            col_list_item['field'] =  col_list_item['headerName']
            col_list_item['filter'] = filter
            col_list_item['resizable'] = self.resizable
            col_list_item['sortable'] = self.sortable
            col_list_item['minWidth'] = self.minWidth # Minimum width in pixels; other values are integers
            col_list_item['editable'] = self.editable # Minimum width in pixels; other values are integers
            col_list_item['maxWidth'] = self.maxwidth  # Maximum width in pixels; other values are integers
            col_list_item['flex'] = 1  # Flex sizing; other values are integers
            
            # Check if 'type' key exists in col
            col_list_item['type'] = [] # 
            print(f"dtype of {col_list_item['headerName']}: {dataframe[col_list_item['headerName']].dtype}")
            if 'targetmin' in col_list_item['headerName']:
                pass
            if pd.api.types.is_numeric_dtype(dataframe[col_list_item['headerName']]):
                col_list_item['valueFormatter'] = "function(params) { return '$' + params.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }"
                col_list_item['cellStyle'] = {'textAlign': 'right'}

            # Editing
            col_list_item['editable'] = True  # False
            col_list_item['cellEditor'] = 'agTextCellEditor'  # 'agSelectCellEditor', 'agRichSelectCellEditor', 'agLargeTextCellEditor', custom editors

            # Sorting & Filtering
            col_list_item['sortable'] = True  # False
            col_list_item['sort'] = 'asc'  # 'desc', None
            col_list_item['filter'] = True  # False, or a specific filter type like 'agNumberColumnFilter', 'agTextColumnFilter'
            # col_list_item['filterParams'] = {}  # Parameters for the filter, depends on the filter type

            # Grouping & Aggregation
            col_list_item['groupable'] = True  # False
            col_list_item['enableRowGroup'] = True  # False
            col_list_item['rowGroup'] = False  # True, enables row grouping
            col_list_item['rowGroupIndex'] = None  # Index for row grouping; other values are integers
            col_list_item['enablePivot'] = True  # False
            col_list_item['pivot'] = False  # True, enables pivoting
            col_list_item['pivotIndex'] = None  # Index for pivoting; other values are integers
            if pd.api.types.is_numeric_dtype(col_list_item):
                col_list_item['aggFunc'] = 'sum'  # Set aggregation function to sum for numeric columns
            else:
                col_list_item['aggFunc'] = None  # 'min', 'max', 'avg', 'count', custom aggregation functions
            
            # Column Behavior
            col_list_item['checkboxSelection'] = False  # True, allows the column to have a checkbox for selection
            col_list_item['rowDrag'] = False  # True, enables row dragging
            col_list_item['lockPosition'] = False  # True, locks the column position
            col_list_item['lockVisible'] = False  # True, locks the column visibility
            col_list_item['lockPinned'] = False  # True, locks the column pinning (left or right)

            # Pinning
            col_list_item['pinned'] = None  # 'left', 'right', None for not pinned

            # Tooltip
            col_list_item['tooltipField'] = None  # Field name for a tooltip; other values are strings
            col_list_item['tooltipValueGetter'] = None  # A JavaScript function or string expression to get the tooltip value

            # Column Visibility
            col_list_item['hide'] = self.hide_by_default  # True to hide the column

            
            col_list_item['headerTooltip'] = None  # Tooltip for the column header; other values are strings
            col_list_item['headerCheckboxSelection'] = False  # True, allows a checkbox in the header for selecting all rows
            col_list_item['headerCheckboxSelectionFilteredOnly'] = False  # True, only selects filtered rows
            col_list_item['floatingFilter'] = False  # True, enables floating filters under the header
            col_list_item['menuTabs'] = ['filterMenuTab', 'generalMenuTab', 'columnsMenuTab']  # Tabs to show in the column menu
            col_list_item['sortableTooltip'] = False  # True to show a tooltip when the column is sorted
            col_list_item['columnGroupShow'] = None  # 'open', 'closed', None; controls when the column is shown in a group
            
            # Specifically set MarketValue to sum when pivoted
            if col_list_item['headerName'] == 'MarketValue':
                col_list_item['headerName'] = self.format_col_as_currency(col_list_item)
                # newcol['aggFunc'] = 'sum'

            new_col_defs.append(col_list_item)
        
        

        gridoptions['columnDefs'] = new_col_defs
        gridoptions['domLayout'] = 'normal'
        
        return gridoptions
    
    def format_col_as_currency(self, col):
        col["type"]= ["numericColumn","numberColumnFilter", "customNumericFormat"]
        col["custom_currency_symbol"]= self.currency_symbol
        col['hide'] = False  # True to hide the column
        col['precision'] = 2  # True to hide the column
        return col
    
    def is_none_or_empty(self, df):
            resp = True
            try:
                return df is None or df.empty
            except:
                return resp   
            
    def display_grid(self, dataframe=None, 
             grid_options=None, 
             height=700, 
             row_selection=True, 
             on_row_selected=None, 
             fit_columns_on_grid_load=False, 
             update_mode=GridUpdateMode.SELECTION_CHANGED, 
             data_return_mode="as_input", 
             conversion_errors='coerce', 
             theme='balham', 
             custom_css=None):
    
        if self.is_none_or_empty(dataframe):
            print ('ERROR: No dataframe provided')
            return

        # print(f"Type of dataframe before processing: {type(dataframe)}")

        if grid_options is None:
            grid_options = self.create_default_grid(dataframe=dataframe)
        
        # print(f"Type of dataframe after creating default grid: {type(dataframe)}")
     
        grid_return = AgGrid(dataframe, 
                        grid_options, 
                        height=height, 
                        row_selection=row_selection,
                        on_row_selected=on_row_selected,
                        fit_columns_on_grid_load=fit_columns_on_grid_load, 
                        update_mode=update_mode, 
                        data_return_mode=data_return_mode, 
                        conversion_errors=conversion_errors,
                        enable_enterprise_modules=True,
                        theme=theme, 
                        custom_css=custom_css, key=str(uuid.uuid4()))

        # print(f"Type of dataframe before processing: {type(dataframe)}")
        
        return grid_return

if __name__ == '__main__':
    def main():
        gmtc = gmtc_data()
        
        # #Holdings data prep
        # gmtc.account_holdings['marketvalue'] = pd.to_numeric(gmtc.account_holdings['marketvalue'], errors='coerce')
        
        # Accounts by Asset Class
        accounts_by_asset_class = gmtc.account_holdings.groupby(['accountnum', 'assetclass'])['marketvalue'].sum().reset_index()
        
        # Accounts by Sub Asset Class
        accounts_by_sub_asset_class = gmtc.account_holdings.groupby(['accountnum', 'assetclass'])['marketvalue'].sum().reset_index()
        st.caption(accounts_by_sub_asset_class.dtypes)
        #Models
        asset_class_models = gmtc.account_models[gmtc.account_models['policyclasstype'] == 'AssetClass']
        sub_asset_class_models = gmtc.account_models[gmtc.account_models['policyclasstype'] == 'AssetSubClass']

        allocation_summary = pd.merge(accounts_by_asset_class, asset_class_models, 
                                        left_on=['accountnum', 'assetclass'], 
                                        right_on=['accountnum', 'policyassetclassifier'], 
                                    how='outer')
        
        
        asset_allocation_by_account = create_new_grid(enablePivot=False)
        asset_allocation_by_account.display_grid( allocation_summary)
        
        
        for data_item in gmtc.get_all_data():
            try:
                name = data_item[0].replace('_', ' ').replace('account', '').strip().title()
                grid = create_new_grid(enablePivot=False)
                with st.expander(name, expanded=False):
                    grid.display_grid( data_item[1])
            except Exception as e:
                st.write(f"Error: {e}")
                st.write(f"Type After Error: {type(data_item[1])}")
                if isinstance(data_item[1], pd.DataFrame):
                    st.write(f"Columns After Error: {data_item[1].dtypes}")
                else:
                    st.write(f"Data After Error: {data_item[1]}")
    main()

    


