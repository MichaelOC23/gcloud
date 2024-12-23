
import streamlit as st
from utils._class_streamlit_pf import streamlit_mytech 
stm = streamlit_mytech("", auth=False)
import time
import json
import uuid
import os
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
# import plotly.graph_objects as go


st.session_state['devmode']=False    
default_col_config = "personal_finance_config.json"
numeric_field_list = ['marketvalue', 'accruedintb', 'acquisitionunitcost', 'amortization', 'bookvalue', 'estincomeb', 'taxcost', 'unrealgl', 'unreallongtermcapgl', 'unrealshorttermcapgl' ]
if 'use_group_by' not in st.session_state:
    st.session_state['use_group_by'] = ['accountnum', 'shortname']

acct_context = None
port_context = None

if 'selected_account' in st.session_state:
    if 'Select'  in st.session_state['selected_account']:
        acct_context = None
    elif not isinstance(st.session_state['selected_account'], list):
        acct_context = [st.session_state['selected_account']]
    else:
        acct_context = st.session_state['selected_account']

if 'selected_portfolio' in st.session_state:
    if 'Select'  in st.session_state['selected_portfolio']:
        port_context = None
    elif not isinstance(st.session_state['selected_portfolio'], list):
        port_context = [st.session_state['selected_portfolio']]
    else:
        port_context = st.session_state['selected_portfolio']
    



def main():
    
     
    pg = st.navigation({
        "Personal Finance":[
            st.Page(display_transaction_files, title= "By Asset Class", url_path='display_by_asset_class'),
        ],
        "Tools":[
            st.Page("utils/CSVAnalyzer.py", title="Data File Analysis"),
            st.Page("utils/pandas-cheat-sheet.py", title="Logic"),
            ]
    }, expanded=True)
    
    pg.run()

def apply_context_to_df(df):
    if acct_context and "Select" not in acct_context:
        df = df[df['accountnum'].isin(acct_context)]
    
    if port_context and "Select" not in port_context:
        df = df[df['portnum'].isin(port_context)]
    return df
        


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
        with open(f'transaction-files-test/{filename}') as f:
            
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

class personal_finance:
    def __init__(self, folder='transaction-files'):
        self.folder = folder
        self.dataframes = {}
        self.load_all_data()

    def load_all_data(self):
        start_time = time.time()
        csv_files = [f for f in os.listdir(self.folder) if f.endswith('.csv')]

        for file in csv_files:
            df = load_and_process_csv(self.folder, file)
            if df is not None:
                self.dataframes[file] = df
        

        print(f"\033[1;96mLoaded all CSV files in {time.time() - start_time} seconds.\033[0m")
        # self.load_extended_dataframes()
    

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

        min_grid_height = 300
        
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

        height = min(max(dataframe.shape[0]*80, min_grid_height), height)
        if grid_options is None:
            grid_options = self.create_default_grid(dataframe=dataframe, fields_to_group_by=fields_to_group_by, col_dict = col_dict )
        
        # sorted_holdings = dict(sorted(holdings['holdings'].items(), key=lambda x: x[1]['sortkey']))

        
        
        with st.container(key=f"{uuid.uuid4}", border=True):
            if title is not None and title != '':
                if st.session_state['devmode']:
                    st.code(f"{st.session_state['use_group_by']}")    
                st.markdown(f"#### :gray[{title}]  \n___")
            
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
                            custom_css=custom_css, key=str(f"{title} {uuid.uuid4()}"))

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
        
        return grid_return

class personal_finance_menu:
    def __init__ (self):
        self.pf = personal_finance()

def display_transaction_files():
    st.write('Displaying Transaction Files')
    
    # # # Accounts by Asset Class
    # group_by = st.session_state['use_group_by'] + ['assetclass']
    # # st.code(f"Group By: {group_by}")
    

    # holdings_df1 = pf.dataframes.get('account_holdings.csv')
    # account_totals = holdings_df1.groupby('accountnum')['marketvalue'].sum().reset_index()
    # by_asset_class = holdings_df1.groupby(group_by)['marketvalue'].sum().reset_index()
    # merged_totals_df = pd.merge(by_asset_class, account_totals, how='inner', left_on=['accountnum'], right_on=['accountnum'])
    # merged_totals_df = merged_totals_df.rename(columns={'marketvalue_y': 'totalvalue', 'marketvalue_x': 'currentvalue'})
    



    # models_df = pf.dataframes['account_models.csv'][pf.dataframes['account_models.csv']['policyclasstype']==f'Asset{aclass}']
    # merged_df = pd.merge(merged_totals_df, models_df, how='inner', left_on=['accountnum', f'asset{aclass.lower()}'], right_on=['accountnum', f'{model.lower()}assetclassifier'])
    # merged_df['currentallocation'] = (merged_df['currentvalue'] / merged_df['totalvalue']) *100
    # merged_df['policydrift'] = (merged_df['currentallocation'] - merged_df['policypercent'])
    # merged_df['targetdrift'] = (merged_df['currentallocation'] - merged_df['targetpercent']) 
    # df = apply_context_to_df(merged_df)

    
    
    # investment_list = df['shortname'].unique().tolist()

    # asset_class_list = df[f'asset{aclass.lower()}'].unique().tolist()

    # actual_values_dict = {}
    # for asset_class in asset_class_list:
    #     actual_values_dict[asset_class] = df[df[f'asset{aclass.lower()}'] == asset_class]['currentallocation'].tolist()


    # min_values_dict = {}
    # for asset_class in asset_class_list:
    #     min_values_dict[asset_class] = df[df[f'asset{aclass.lower()}'] == asset_class][f'{model.lower()}minimumpercent'].tolist()


    # max_values_dict = {}
    # for asset_class in asset_class_list:
    #     max_values_dict[asset_class] = df[df[f'asset{aclass.lower()}'] == asset_class][f'{model.lower()}maximumpercent'].tolist()


    # # Create the figure
    # fig = go.Figure()

    # # Add bar for each asset class
    # for asset_class in asset_class_list:
    #     actual = actual_values_dict[asset_class]
    #     min_value = min_values_dict[asset_class]
    #     max_value = max_values_dict[asset_class]

    #     # Calculate error bars
    #     error_y = [(max_v - actual[i], actual[i] - min_v) for i, (max_v, min_v) in enumerate(zip(max_value, min_value))]
    #     upper_errors = [e[0] for e in error_y]
    #     lower_errors = [e[1] for e in error_y]

    #     # Add trace for this asset class
    #     fig.add_trace(go.Bar(
    #         x=investment_list,
    #         y=actual,
    #         error_y=dict(
    #             type='data',
    #             symmetric=False,
    #             array=upper_errors,
    #             arrayminus=lower_errors
    #         ),
    #         name=asset_class
    #     ))

    # # Update the layout for better readability
    # fig.update_layout(
    #     title="Portfolio Actual Value with Min/Max Range for Each Asset Class",
    #     xaxis_title="Account",
    #     yaxis_title="Market Value Drift",
    #     barmode='group'  # Group bars by categories
    # )

    # # Display the chart in Streamlit
    # st.plotly_chart(fig)

    
    # by_asset_class_grid = create_new_grid(path_to_col_config='gmtc_column_configuration.json', enablePivot=False)
    # by_asset_class_grid.display_grid( df, title="Drift by Asset Class",col_dict_key='holdings')
  



if __name__ == '__main__':
    
    pf = personal_finance()
    
    
    def set_filter_values():
        if 'selected_group_by' not in st.session_state or st.session_state['selected_group_by'] is None or st.session_state['selected_group_by'] == 'Account':
            st.session_state['use_group_by'] = ['accountnum', 'shortname']
        elif st.session_state['selected_group_by'] == 'Portfolio':
            st.session_state['use_group_by'] = ['accountnum', 'shortname', 'portnum']
        
        
    
    
    @st.dialog("Filter", width="large")
    def page_filters():
        def format_sb_df(df, col_name):
            placeholder_df = pd.DataFrame({col_name: ['Select...']})
            return pd.concat([placeholder_df, df], ignore_index=True)

        filter_container = st.container(border=True)
        fcol1, fcol2, fcol3, = filter_container.columns([1,1,1], vertical_alignment='top')
        selected_account = fcol1.multiselect(label = "Select Account", options= format_sb_df(pf.dataframes['account_list'], 'accountnum'), key='selected_account', placeholder="Select an Account", label_visibility='visible')
        selected_portfolio = fcol2.selectbox(label = "Select Portfolio", options= format_sb_df(pf.dataframes['account_portfolios.csv'][['portnum']], 'portnum'), key='selected_portfolio', placeholder="Select an Portfolio", label_visibility='visible')
        selected_employee = fcol3.selectbox(label = "Select Employee", options= format_sb_df(pf.dataframes['account_employees.csv'][['employee']], 'employee'), key='selected_employee', placeholder="Select an Employee", label_visibility='visible')
        selected_group_by = fcol1.radio('Group By', ['Account', 'Portfolio'], key="selected_group_by",horizontal=False)
        
        if fcol3.button("Set Filter", "FilterButton", type='primary', use_container_width=True, on_click=set_filter_values):
            st.rerun()
        

    ph_title,   ph_filter, ph_clear= st.columns([7,1,1], vertical_alignment="bottom")
    page_title_text = ph_title.markdown("### :gray[Advisor Portal > Portfolio Management]")
    settings_pop = ph_filter.button(f"Context", "SettingsButton", type='primary', use_container_width=True, on_click=page_filters)
    
    if ph_clear.button("Clear", "ClearFilterButton", type='secondary',use_container_width=True):
        filters = ['selected_account', 'selected_portfolio', 'selected_employee']
        for f in filters:
            if f in st.session_state:
                st.session_state[f] = None
    st.divider()
    main()
        

    
    