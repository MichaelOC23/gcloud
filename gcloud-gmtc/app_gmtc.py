
import streamlit as st
from _class_streamlit_gmtc import streamlit_mytech 
stm = streamlit_mytech("", auth=False)
import time
import json
import uuid
import os
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode


st.session_state['devmode']=True
default_col_config = "gmtc_column_configuration.json"
numeric_field_list = ['marketvalue', 'accruedintb', 'acquisitionunitcost', 'amortization', 'bookvalue', 'estincomeb', 'taxcost', 'unrealgl', 'unreallongtermcapgl', 'unrealshorttermcapgl' ]



def main():
    def format_sb_df(df, col_name):
        placeholder_df = pd.DataFrame({col_name: ['Select...']})
        return pd.concat([placeholder_df, df], ignore_index=True)


    
    filter_container = st.container(border=True)
    fcol1, fcol2, fcol3, fcol4, fcol5 = st.columns([1,1,1,1,1], vertical_alignment='bottom')
    selected_account = fcol1.selectbox(label = "Select Account", options= format_sb_df(gmtc.dataframes['account_list'], 'accountnum'), key='selected_account', placeholder="Select an Account", label_visibility='visible', index=0)
    selected_portfolio = fcol2.selectbox(label = "Select Portfolio", options= format_sb_df(gmtc.dataframes['account_portfolios.csv'][['portnum']], 'portnum'), key='selected_portfolio', placeholder="Select an Portfolio", label_visibility='visible')
    selected_employee = fcol3.selectbox(label = "Select Employee", options= format_sb_df(gmtc.dataframes['account_employees.csv'][['employee']], 'employee'), key='selected_employee', placeholder="Select an Employee", label_visibility='visible')
    filter_button = fcol4.button("Set Context", "FilterButton", type='primary', use_container_width=True,)
    clear_filter_button = fcol5.button("Clear", "ClearFilterButton", type='secondary',use_container_width=True)
    
    pg = st.navigation([
        "Holdings":[
        st.Page(display_holdings, title= "Holdings All Accounts", url_path='holdings' ),
        ],
        "Other":[]
        st.Page(display_accounts_by_asset_class, title= "Accounts by Asset Class", url_path='display_accounts_by_asset_class'),
        # st.Page(display_accounts_by_asset_class, title= "Asset Class by Account", url_path='display_accounts_by_asset_class'),
        st.Page(display_accounts_by_sub_asset_class, title= "Asset Class by Sub Account", url_path='display_accounts_by_sub_asset_class'),
        st.Page(display_team, title= "Teams", url_path='display_team'),
        st.Page(display_account_transactions, title= "Transactions", url_path='display_account_transactions'),
        st.Page(display_account_performance, title= "Performance", url_path='display_account_performance'),
        st.Page(display_account_models, title= "Models", url_path='display_account_models'),
        st.Page(display_account_groups, title= "Account Groups", url_path='display_account_groups'),
        st.Page(display_account_employees, title= "Employees", url_path='display_account_employees'),
        st.Page(display_colored_grid, title= "123", url_path='display_colored_grid'),
        
        st.Page("CSVAnalyzer.py", title="CSV Analyzer"),
        st.Page("pandas-cheat-sheet.py", title="Pandas")]
    ])
    
    pg.run()

def load_and_process_csv(folder, filename):
    csv_path = os.path.join(folder, filename)
    dtype_path = csv_path.replace('.csv', '_dtype.json')
    pickle_path = csv_path.replace('.csv', '.pkl')

    # If a pickle file exists, load from it
    if os.path.exists(pickle_path):
        df = pd.read_pickle(pickle_path)
        print(f"\033[1;96mLoaded {filename} from pickle.\033[0m")
        return df

    # Otherwise, load the CSV
    start_time = time.time()
    if os.path.exists(dtype_path):
        with open(dtype_path, 'r') as dtype_file:
            dtype_dict = json.load(dtype_file)
        df = pd.read_csv(csv_path, dtype=dtype_dict)
        print(f"\033[1;96mLoaded {filename} with specified dtypes from CSV.\033[0m")
    else:
        # CSV Will be processed as new
        with open(f'gmtc/{filename}') as f:
            
            # Read , lower case and remove spaces from header
            header = f.readline().strip().split(',')
            clean_header = [col.strip().replace(' ', '_').lower() for col in header]

            # Load the rest of the file into a DataFrame using the cleaned header
            df = pd.read_csv(f, names=clean_header, dtype=str)
            
        # Drop rows where all elements are NaN
        df = df.dropna(how='all')
        
        # Remove \n from all fields in the DataFrame
        df = df.apply(lambda col: col.apply(lambda x: x.replace('\n', ' ').replace('\r', ' ') if isinstance(x, str) else x))
        
        # Reset the index after dropping rows
        df = df.reset_index(drop=True)
        
        # Cast the DataFrame Columns as their appropriate types
        df = inspect_and_cast(df, filename)
        
        # Save dtypes
        dtype_dict = df.dtypes.apply(lambda x: x.name).to_dict()
        with open(dtype_path, 'w') as dtype_file:
            json.dump(dtype_dict, dtype_file)
        print(f"\033[1;96mSaved dtypes for {filename}.\033[0m")

    # Save the processed DataFrame as a pickle
    df.to_pickle(pickle_path)
    print(f"\033[1;96mSaved {filename} as pickle.\033[0m")
    print(f"\033[1;96mTime to process {filename}: {time.time() - start_time}\033[0m")
    return df

def inspect_and_cast(df, filename):
    def is_numeric_or_empty(s):
        try:
            s_float = pd.to_numeric(s, errors='coerce')
            return s_float.notna() | s.isna()
        except ValueError:
            return False

    def optimize_dataframe(df, max_rows=500):
        for col in df.columns:
            sample = df[col].iloc[:max_rows]
            if is_numeric_or_empty(sample).all():
                df[col] = df[col].replace(r'^\s*$', '0', regex=True)
                df[col] = df[col].fillna('0')
                try:
                    df[col] = df[col].astype(float)
                except ValueError:
                    continue
        return df

    df = optimize_dataframe(df)

    for col in df.columns:
        if df[col].apply(is_date_or_empty).all():
            df[col] = pd.to_datetime(df[col], errors='coerce')

    df = df.fillna('')  
    return df

def is_date_or_empty(val):
    if pd.isnull(val):
        return True
    val_str = str(val).strip()
    if val_str == '':
        return True
    try:
        pd.to_datetime(val_str)
        return True
    except (ValueError, TypeError):
        return False

class gmtc_data:
    def __init__(self, folder='gmtc_data'):
        self.folder = folder
        self.dataframes = {}
        self.load_all_data()

    def load_all_data(self):
        start_time = time.time()
        csv_files = [f for f in os.listdir(self.folder) if f.endswith('.csv')]

        for file in csv_files:
            df = load_and_process_csv(self.folder, file)
            if df is not None:
                # Data Clean Up
                # Add accountnum column to all relevant dataframes
                if 'portnum' in df.columns:
                    df['accountnum'] = df['portnum'].str.replace(r'\.\d+$', '', regex=True)
                # Establish a readable 'secid' column
                # Step 1: Create the 'secid' column with the value of 'ticker'
                if 'ticker' in df.columns and 'secid' not in df.columns:
                    df['secid'] = df['ticker']
                
                if 'secid' in df.columns and 'cusip' in df.columns:
                    # Step 2: Where 'ticker' is empty/blank/null, set 'secid' to 'cusip'
                    df['secid'] = np.where(df['secid'].isnull() | df['secid'].str.strip().eq(''), df['cusip'], df['secid'])
                        
                    # Step 3: Set any remaining blanks in 'secid' to 'USD'
                    df['secid'] = df['secid'].replace('', 'USD')
                    df['secid'] = df['secid'].fillna('USD')
                
                self.dataframes[file] = df
        

        print(f"\033[1;96mLoaded all CSV files in {time.time() - start_time} seconds.\033[0m")
        self.load_extended_dataframes()
    
    def load_extended_dataframes(self):
        
        
        # Wealth Strategists Account Portfolios in
        wealth_strategists_df = self.dataframes.get('employee_account_coverage.csv')
        wealth_strategists_df = wealth_strategists_df[wealth_strategists_df['coveragerole']=='Wealth Strategist']
        wealth_strategists_df = wealth_strategists_df[['lastn', 'firstn', 'coveragerole', 'telephone', 'fax', 'gpacct']]
        self.dataframes['wealth_strategists'] = wealth_strategists_df.rename(columns={
        'firstn': 'Strategist First Name',
        'lastn': 'Strategist Last Name',
        'telephone': 'Strategist Tel.',
        'fax': 'Strategist Fax',
        'coveragerole': 'Strategist Role',
        'gpacct': 'Account #',
        })
        
        
        # Wealth Advisor Account Portfolios in
        wealth_advisor_df = self.dataframes.get('employee_account_coverage.csv')
        wealth_advisor_df = wealth_advisor_df[wealth_advisor_df['coveragerole']=='Wealth Advisor']
        wealth_advisor_df = wealth_advisor_df[['lastn', 'firstn', 'coveragerole', 'telephone', 'fax', 'gpacct']]
        self.dataframes['wealth_advisors'] = wealth_advisor_df.rename(columns={
        'firstn': 'Advisor First Name',
        'lastn': 'Advisor Last Name',
        'telephone': 'Advisor Tel.',
        'fax': 'Advisor Fax',
        'coveragerole': 'Advisor Role',
        'gpacct': 'Account #',
        })
        
        
        # Portfolio Manager Portfolios in
        portfolio_manager_df = self.dataframes.get('employee_account_coverage.csv')
        portfolio_manager_df = portfolio_manager_df[portfolio_manager_df['coveragerole']=='Portfolio Manager']
        portfolio_manager_df = portfolio_manager_df[['lastn', 'firstn', 'coveragerole', 'telephone', 'fax', 'gpacct']]
        self.dataframes['portfolio_managers'] = portfolio_manager_df.rename(columns={
        'firstn': 'Manager First Name',
        'lastn': 'Manager Last Name',
        'telephone': 'Manager Tel.',
        'fax': 'Manager Fax',
        'coveragerole': 'Manager Role',
        'gpacct': 'Account #',
        })
        
        
        holdings_df = self.dataframes.get('account_holdings.csv')
        # print(f"Holding Count: {holdings_df.shape[0]}")
        
        # Merrge Account Portfolios in
        portfolios_df = self.dataframes.get('account_portfolios.csv')
        holdings_portfolio_df = pd.merge(holdings_df, portfolios_df,  on=['portnum', 'accountnum'], how='outer')    
        # print(f"Holding Count: {holdings_portfolio_df.shape[0]}")
        
        # Merge Wealth Advisors
        holdings_portfolio_wa_df = pd.merge(holdings_portfolio_df, wealth_advisor_df,  left_on=['accountnum'], right_on=['gpacct'], how='inner')    
        # print(f"Holding Count: {holdings_portfolio_wa_df.shape[0]}")
        
        # Merge Portfolio Managers
        holdings_portfolio_wa_pm_df = pd.merge(holdings_portfolio_wa_df, portfolio_manager_df,  left_on=['accountnum'], right_on=['gpacct'], how='inner')    
        # print(f"Holding Count: {holdings_portfolio_wa_pm_df.shape[0]}")
        
        # Merge Wealth Strategists
        holdings_portfolio_wa_pm_ws_df = pd.merge(holdings_portfolio_wa_pm_df, wealth_strategists_df,  left_on=['accountnum'], right_on=['gpacct'], how='inner')    
        # print(f"Holding Count: {holdings_portfolio_wa_pm_ws_df.shape[0]}")
        
        self.dataframes['holdings_wide'] = holdings_portfolio_wa_pm_ws_df
        self.dataframes['account_list'] = pd.DataFrame(holdings_portfolio_wa_pm_ws_df['accountnum'].unique(), columns=['accountnum'])
        
        self.dataframes['account_employees.csv']['employee'] = self.dataframes['account_employees.csv']['firstn'] + ' ' + self.dataframes['account_employees.csv']['lastn']

        

    def get_data_by_name(self, name):
        return self.dataframes.get(name)

    def get_all_data(self):
        return self.dataframes

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
                 hide_by_default=False,
                path_to_col_config=default_col_config
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
        self.column_config = {}
        if path_to_col_config is not None:
            self.column_config = json.load(open(path_to_col_config))
        
        
    def create_default_grid(self, dataframe, print_headers=False, fields_to_group_by=[], col_dict={}):
          
        if self.is_none_or_empty(dataframe):
            print ('ERROR: No dataframe provided')
            return
        # Apply formatting and right alignment to numeric columns in Ag-Grid
        
        builder = GridOptionsBuilder.from_dataframe(dataframe)
        
        builder.configure_selection(self.rowSelection  , self.use_checkbox)
        builder.configure_pagination(self.enable_pagination)
        builder.configure_side_bar(self.show_filters, self.show_columns, self.defaultToolPanel)  # Enable the sidebar with default options
        builder.configure_auto_height(autoHeight=True)
        
        # Add enablePivot option to column definitions
        gridoptions = builder.build()
        gridoptions['enableCharts'] = True  
        gridoptions['enableRangeSelection'] = True
        
        new_col_defs = []
        for col_list_item in gridoptions['columnDefs']:
            col_list_item['field'] =  col_list_item['headerName']
            col_list_item['filter'] = None
            col_list_item['resizable'] = self.resizable
            col_list_item['sortable'] = self.sortable
            col_list_item['editable'] = self.editable # Minimum width in pixels; other values are integers            
            col_list_item['flex'] = 1  # Flex sizing; other values are integers

            # Editing
            col_list_item['cellEditor'] = 'agTextCellEditor'  # 'agSelectCellEditor', 'agRichSelectCellEditor', 'agLargeTextCellEditor', custom editors

            # Sorting & Filtering
            col_list_item['sort'] = None  # 'asc', 'desc', None
            col_list_item['filter'] = True  # False, or a specific filter type like 'agNumberColumnFilter', 'agTextColumnFilter'

            # Grouping & Aggregation
            col_list_item['groupable'] = True  # False
            col_list_item['enableRowGroup'] = True  # False
            col_list_item['columnGroupShow'] = None  # 'open', 'closed', None; controls when the column is shown in a group
            # col_list_item['groupHideOpenParents'] = True 
            col_list_item['rowGroupPanelShow'] = True
            
            if pd.api.types.is_numeric_dtype(dataframe[col_list_item['field']]):
                col_list_item['cellStyle'] = {'textAlign': 'right'}
                col_list_item['headerClass'] = 'ag-right-aligned-header'
                col_list_item['precision'] = 2
                col_list_item['valueFormatter'] = "(x === undefined || x === null) ? '' : Number(x).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})"
                col_list_item['aggFunc'] = 'sum' # Set aggregation function to sum for numeric columns
            
            # Enable the grouping for spcified fields
            if col_list_item['field'] in fields_to_group_by:
                # Row Grouping
                group_index = fields_to_group_by.index(col_list_item['field'])
                col_list_item['rowGroup'] = True  # True, enables row grouping
                col_list_item['rowGroupIndex'] = group_index  # Index for row grouping; other values are integers
                col_list_item['showRowGroup']=True
                col_list_item['groupDisplayType'] = 'singleColumn'
                                                    # 'singleColumn': single group column automatically added by the grid.
                                                    # 'multipleColumns': a group column per row group is added automatically.
                                                    # 'groupRows': group rows are automatically added instead of group columns.
                
            else: 
                col_list_item['rowGroup'] = False  # True, enables row grouping
                col_list_item['rowGroupIndex'] = None  # Index for row grouping; other values are integers
                col_list_item['showRowGroup']=False
                col_list_item['pinned'] = None  # 'left', 'right', None for not pinned
                
            col_list_item['enablePivot'] = True  # False
            col_list_item['pivot'] = False  # True, enables pivoting
            col_list_item['pivotIndex'] = None  # Index for pivoting; other values are integers

            
            # Column Behavior
            col_list_item['checkboxSelection'] = False  # True, allows the column to have a checkbox for selection
            col_list_item['rowDrag'] = False  # True, enables row dragging
            col_list_item['lockPosition'] = False  # True, locks the column position
            col_list_item['lockVisible'] = False  # True, locks the column visibility
            

            # Pinning
            # col_list_item['pinned'] = 'left'  # 'left', 'right', None for not pinned
            col_list_item['lockPinned'] = False  # True, locks the column pinning (left or right)

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
            
            #! Apply Overrides
            if col_dict != {}:
                if col_list_item['field'] in col_dict and col_dict[col_list_item['field']]!= None:
                    for key in col_dict[col_list_item['field']].keys():
                        if key != 'type':
                            col_list_item[key] = col_dict[col_list_item['field']][key]
                    col_list_item['sortkey']= col_dict[col_list_item['field']].get('sortkey', 10000)


            if not col_list_item['hide']:
                title_string = col_list_item['headerName']
                field_string = col_list_item['field']
                max_char_values = int(dataframe[field_string].astype(str).apply(len).max())
                max_char = max(len(title_string), max_char_values)
                col_list_item['minWidth'] = max(100, min(max_char*15, 200))
                # print(f"{col_list_item['headerName']}: {col_list_item['minWidth']}")
            
            new_col_defs.append(col_list_item)
            # "cellStyle": {"textAlign": "right"},
        
        with open(f"col_defs.json", 'w') as f:
            json.dump(new_col_defs, f)
        new_col_defs = sorted(new_col_defs, key=lambda x: x.get('sortkey', 10000))

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
             fit_columns_on_grid_load=True, 
             update_mode=GridUpdateMode.SELECTION_CHANGED,  
             data_return_mode="as_input", 
             conversion_errors='coerce', 
             theme='material', 
             custom_css=None, title="", col_dict_key=None, fields_to_group_by=[]):

        if col_dict_key and self.column_config !={}:
            col_dict = self.column_config[col_dict_key]
        else: col_dict = {}
            
        if self.is_none_or_empty(dataframe):
            print ('ERROR: No dataframe provided')
            return
        for col in dataframe.columns:
            #Format the dates
            if pd.api.types.is_datetime64_any_dtype(dataframe[col]):
                # Convert the 'acquitiondate' column to datetime and format it as 'DD-MMM-YYYY'
                dataframe[col] = pd.to_datetime(dataframe[col]).dt.strftime('%d %b %Y')
                dataframe[col] = dataframe[col].fillna('')
            elif pd.api.types.is_numeric_dtype(dataframe[col]):
                dataframe[col] = dataframe[col].fillna(0)
            else:
                dataframe[col] = dataframe[col].fillna('')

        height = min(dataframe.shape[0]*40, height)
        if grid_options is None:
            grid_options = self.create_default_grid(dataframe=dataframe, fields_to_group_by=fields_to_group_by, col_dict = col_dict )
        
        # sorted_holdings = dict(sorted(holdings['holdings'].items(), key=lambda x: x[1]['sortkey']))

        if title is not None and title != '':
            st.subheader(title, divider=True)
        
        
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

        if st.session_state['devmode']:
            missing_columns = {}
            with st.expander('Data View Configuraiton', expanded=True):
                df_config_col, grid_config_col = st.columns([1,1])
                for f in dataframe.columns:
                    if f not in col_dict.keys():
                        cellStyle_str = {'textAlign':'right'}
                        aggfunc_str = 'first'
                        if f"{dataframe[f].dtype}" == 'float64': 
                            cellStyle_str = {'textAlign':'right'} 
                            aggfunc_str = 'sum'
                        missing_columns[f] = {  
                                                'headerName': f,
                                                'type': f"{dataframe[f].dtype}",
                                                'hide': False,
                                                'aggFunc': aggfunc_str,
                                                'rowGroup': False,
                                                'pinned': False,
                                                'cellStyle':cellStyle_str
                        }
        df_config_col.json(missing_columns)
        grid_config_col.write(grid_return.grid_options)


            
                        
                
        # print(f"Type of dataframe before processing: {type(dataframe)}")
        
        return grid_return


class gmtc_menu:
    def __init__ (self):
        self.gmtc = gmtc_data()

gmtc = gmtc_data()

def display_holdings():
    
    holdings_df = gmtc.dataframes.get('account_holdings.csv')
    holdings_df_grid = create_new_grid(path_to_col_config='gmtc_column_configuration.json', enablePivot=False)
    holdings_df_grid.display_grid( holdings_df, title="Holdings (All Accounts)", col_dict_key='holdings')
    
def display_accounts_by_asset_class():
    # # Accounts by Asset Class
    holdings_df1 = gmtc.dataframes.get('account_holdings.csv')
    accounts_by_asset_class = holdings_df1.groupby(['accountnum', 'assetclass'])[numeric_field_list].sum().reset_index()
    accounts_by_asset_class_grid = create_new_grid(path_to_col_config='gmtc_column_configuration.json', enablePivot=False)
    accounts_by_asset_class_grid.display_grid( accounts_by_asset_class, title="Accounts by Asset Class",col_dict_key='holdings')

def display_accounts_by_sub_asset_class():
    # # Accounts by Asset Class
    holdings_df1 = gmtc.dataframes.get('account_holdings.csv')
    accounts_by_sub_asset_class = holdings_df1.groupby(['accountnum', 'assetsubclass'])['marketvalue', 'accruedintb', 'acquisitionunitcost', 'amortization', 'bookvalue', 'estincomeb', 'taxcost', 'unrealgl', 'unreallongtermcapgl', 'unrealshorttermcapgl' ].sum().reset_index()
    accounts_by_sub_asset_class_grid = create_new_grid(path_to_col_config='gmtc_column_configuration.json', enablePivot=False)
    accounts_by_sub_asset_class_grid.display_grid( accounts_by_sub_asset_class, title="Accounts by Sub Asset Class")

def display_team():
    
    # Wealth Strategist
    wealth_strategists_df_grid = create_new_grid(path_to_col_config='gmtc_column_configuration.json', enablePivot=False)
    wealth_strategists_df_grid.display_grid( gmtc.dataframes['wealth_advisors'], title="Wealth Strategists")
    
    # Wealth Advisor
    wealth_advisor_df_grid = create_new_grid(path_to_col_config='gmtc_column_configuration.json', enablePivot=False)
    wealth_advisor_df_grid.display_grid( gmtc.dataframes['wealth_strategists'], title="Wealth Advisors")
    
    
    # Portfolio Manager 
    portfolio_manager_df_grid = create_new_grid(enablePivot=False)
    portfolio_manager_df_grid.display_grid( gmtc.dataframes['portfolio_managers'], title="Portfolio Managers")

def display_account_transactions():
    grid = create_new_grid(enablePivot=False)
    grid.display_grid( gmtc.dataframes['account_transactions.csv'], title="Transactions",col_dict_key='transactions')

def display_account_performance():
    grid = create_new_grid(enablePivot=False)
    grid.display_grid( gmtc.dataframes['account_transactions.csv'], title="Performance")
    
def display_account_models():
    
    ACgrid = create_new_grid(enablePivot=False)
    ACgrid.display_grid( gmtc.dataframes['account_models.csv'][gmtc.dataframes['account_models.csv']['policyclasstype']=='AssetClass'],
                        title="Asset Class Models", fields_to_group_by=['policymodelclass'])
    
    ASCgrid = create_new_grid(enablePivot=False)
    ASCgrid.display_grid( gmtc.dataframes['account_models.csv'][gmtc.dataframes['account_models.csv']['policyclasstype']=='AssetSubClass'], 
                         title="Asset Sub Class Models")
    


def display_account_groups():
    grid = create_new_grid(enablePivot=False)
    grid.display_grid( gmtc.dataframes['account_groups.csv'], title="Account Groups")
    
def display_account_employees():
    grid = create_new_grid(enablePivot=False)
    grid.display_grid( gmtc.dataframes['account_employees.csv'], title="Employees")

def display_colored_grid():
        
    # Sample data
    
    df = gmtc.dataframes['account_models.csv']

    # Set up the grid options
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_grid_options(domLayout='normal')

    # Define CSS for banded rows and gridlines
    grid_css = """
    /* Banded rows */
    .ag-row:nth-child(odd) {
        background-color: #f2f2f2;  /* Light gray for odd rows */
    }
    .ag-row:nth-child(even) {
        background-color: #ffffff;  /* White for even rows */
    }

    /* Header styling */
    .ag-header {
        background-color: #003366;  /* Dark blue for headers */
        color: #ffffff;  /* White text in headers */
        border-bottom: 2px solid #333333;  /* Dark gray border below header */
    }

    /* Cell border styling */
    .ag-cell {
        border-color: #cccccc !important;  /* Light gray borders for cells */
        background-color: #e6f7ff;  /* Light blue fill for cells */
    }

    /* Gridlines (global) */
    .ag-root .ag-header, .ag-root .ag-cell {
        border-color: #333333 !important;  /* Dark gray for all gridlines */
    }

    /* Cell hover effect */
    .ag-cell:hover {
        background-color: #d6eaf8 !important;  /* Slightly darker blue when hovering */
    }

    /* Pinned columns (if any) */
    .ag-pinned-left-header, .ag-pinned-left-cell {
        background-color: #004488;  /* Different color for pinned columns */
        border-right: 2px solid #333333;  /* Border for pinned columns */
    }
    """
    custom_css = {
    ".ag-row-hover": {"background-color": "red !important"},
    ".ag-header-cell-label": {"background-color": "orange !important"}
    }

    # Display AG Grid in Streamlit with custom CSS
    # st.markdown(f"<style>{grid_css}</style>", unsafe_allow_html=True)
    AgGrid(df, gridOptions=gb.build(),theme='material', custom_css=custom_css, allow_unsafe_jscode=True)
  
if __name__ == '__main__':
    main()
    
    