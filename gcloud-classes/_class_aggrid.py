
import time
import uuid
import pandas as pd
import json
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

class AggridUtils():
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
        
        self.grid_options = {}
        
    def create_default_grid(self, dataframe, header_dict={}):
          
        if self.is_none_or_empty(dataframe):
            print ('ERROR: No dataframe provided')
        
        if header_dict == {}:
            for col in gridoptions['columnDefs']:
                header_dict[col["headerName"]] = col["headerName"]
            with open('grid_header.json', 'w') as f:
                f.write (json.dumps (header_dict))
    
        
            # print("Header Column Names: {}".format(dataframe.columns)
        # Apply formatting and right alignment to numeric columns in Ag-Grid
        
        builder = GridOptionsBuilder.from_dataframe(dataframe)
        
        builder.configure_selection(self.rowSelection  , self.use_checkbox)
        builder.configure_pagination(self.enable_pagination)
        builder.configure_side_bar(self.show_filters, self.show_columns, self.defaultToolPanel)  
        # Enable the sidebar with default options
        # for col in dataframe.select_dtypes(include=[float, int]).columns:
        #     builder.configure_column(col, type=["numericColumn", "customNumericFormat"], precision=2, valueFormatter="x.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })", cellStyle={'text-align': 'right'})
        
        # Add enablePivot option to column definitions
        gridoptions = builder.build()
        gridoptions['enableCharts'] = True  
        gridoptions['enableRangeSelection'] = True
        

        new_col_defs = []
        for col_list_item in gridoptions['columnDefs']:
            
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
            
            if pd.api.types.is_numeric_dtype(dataframe[col_list_item['headerName']]):
                    col_list_item['aggFunc'] = 'sum' # Set aggregation function to sum for numeric columns
            else:
                col_list_item['aggFunc'] = 'max'  # 'min', 'max', 'avg', 'count', custom aggregation functions
            
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
                        # Column Visibility
            if col_list_item["headerName"] in header_dict:
                # col_list_item['field'] = header_dict[col_list_item["headerName"]]
                col_list_item['headerName'] = header_dict[col_list_item["headerName"]]
                col_list_item['hide'] = False # True to hide the column
            else:
                col_list_item['field'] =  col_list_item['headerName']
                col_list_item['hide'] = self.hide_by_default

            new_col_defs.append(col_list_item)
        
        

        gridoptions['columnDefs'] = new_col_defs
        gridoptions['domLayout'] = 'normal'
        
        self.grid_options = gridoptions
    
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

        if self.grid_options == {}:
            self.grid_options = self.create_default_grid(dataframe=dataframe)
        
        print(f"Type of dataframe after creating default grid: {type(dataframe)}")
     
        grid_return = AgGrid(dataframe, 
                        self.grid_options, 
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
