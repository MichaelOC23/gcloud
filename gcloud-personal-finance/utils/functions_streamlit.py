
from attr import field
from st_aggrid import AgGrid, JsCode, GridOptionsBuilder, GridUpdateMode, DataReturnMode
import functions_model_generation as model_gen
import json

def create_default_grid_options(
        dataframe = None, col_val_list = None,
        # Column Options
        minWidth=5, 
        editable=True, 
        filter=True, 
        resizable=True, 
        sortable=True, 
        enableRowGroup=True, 

        # Grid Options
        rowSelection="multiple", 
        use_checkbox=True,
        rowMultiSelectWithClick=False, 
        suppressRowDeselection=False, 
        suppressRowClickSelection=False, 
        groupSelectsChildren=True, 
        groupSelectsFiltered=True, 
        preSelectAllRows=False,

        # Sidebar Options
        sideBar=True,
        entity_attributes=None):
    
    builder = GridOptionsBuilder.from_dataframe(dataframe)
    
    builder.configure_selection(selection_mode='multiple', use_checkbox=True)
    builder.configure_pagination(enabled=True)

    field_dict = {}
    if entity_attributes:
        for attribute_dict in entity_attributes:
            field_dict.update(attribute_dict)
                

    # export the dictionary to json
    json_text = json.dumps(entity_attributes)

    gridoptions = builder.build()
    
    new_columns = []
    for col in gridoptions['columnDefs']:
        newcol = {}
        newcol['headerName']= col['headerName']
        newcol['field'] =  col['headerName']
        newcol['minWidth'] = minWidth
        newcol['editable'] = editable
        # Check if 'type' key exists in col
        if 'type' in col:
            newcol['type'] = col['type']
        else:
            newcol['type'] = [] # 
        newcol['filter'] = filter
        newcol['resizable'] = resizable
        newcol['sortable'] = sortable
        newcol['enableRowGroup'] = enableRowGroup
        new_columns.append(newcol)
    
    grid_options =  {
        "defaultColDef": {
            "minWidth": minWidth,
            "editable": editable,
            "filter": filter,
            "resizable": resizable,
            "sortable": sortable,
            "enableRowGroup": enableRowGroup
        },
        "statusBar": 
            {
            "statusPanels": 
                    [
                        {
                        "statusPanel": 'agAggregationComponent',
                        "statusPanelParams": 
                            {
                            # possible values are: 'count', 'sum', 'min', 'max', 'avg'
                            "aggFuncs": ['min', 'max', 'avg']
                            }
                        }
                    ]
            },
                    
        "sideBar": sideBar,
        "enableAdvancedFilter": True,
        "enableCharts": True,
        "enableRangeSelection": True,
        "columnDefs": new_columns,
        # The columnDefs section is ignored as per your request
        "rowSelection": rowSelection,
        "useCheckbox": use_checkbox,
        "pagination": False,
        "paginationAutoPageSize": True,
        # "onSelectionChanged": on_row_selected,
        "rowMultiSelectWithClick": rowMultiSelectWithClick,
        "suppressRowDeselection": suppressRowDeselection,
        "suppressRowClickSelection": suppressRowClickSelection,
        "groupSelectsChildren": groupSelectsChildren,
        "groupSelectsFiltered": groupSelectsFiltered,
        "preSelectAllRows": False    
        
    }

    
    
    return grid_options
   
def get_grid(dataframe=None, grid_options=None, height=700, row_selection=True, on_row_selected=None, 
             fit_columns_on_grid_load=True, update_mode=GridUpdateMode.SELECTION_CHANGED, data_return_mode="as_input", 
             conversion_errors='coerce', theme='balham', custom_css=None, model=None, entity=None):
    
    entity_attributes = None
    if model and entity:
        entity_attributes = model_gen.get_model_entity_definition(model, entity)

    grid_options = create_default_grid_options(dataframe, entity_attributes=entity_attributes)
     
    grid_return = AgGrid(dataframe, #: pandas.core.frame.DataFrame, 
                     grid_options, #: typing.Optional[typing.Dict] = None, 
                     height=height, #: int = 7, 
                     row_selection=row_selection,
                     on_row_selected=on_row_selected,
                     #width=None, #! Deprecated
                     fit_columns_on_grid_load=fit_columns_on_grid_load, #: bool = False, 
                     update_mode=update_mode, #: st_aggrid.shared.GridUpdateMode = GridUpdateMode.None, 
                        # GridUpdateMode.NO_UPDATE
                        # GridUpdateMode.MANUAL
                        # GridUpdateMode.VALUE_CHANGED #!Editing
                        # GridUpdateMode.SELECTION_CHANGED #!Navigation
                        # GridUpdateMode.FILTERING_CHANGED
                        # GridUpdateMode.SORTING_CHANGED
                        # GridUpdateMode.MODEL_CHANGED
                        # !modes can be combined with bitwise OR operator | for instance: GridUpdateMode = VALUE_CHANGED | SELECTION_CHANGED | FILTERING_CHANGED | SORTING_CHANGED
                     data_return_mode=data_return_mode, #: st_aggrid.shared.DataReturnMode = 'as_input', 
                        # DataReturnMode.AS_INPUT -> Returns grid data as inputed. Includes cell editions
                        # DataReturnMode.FILTERED -> Returns filtered grid data, maintains input order
                        # DataReturnMode.FILTERED_AND_SORTED -> Returns grid data filtered and sorted
                        #! Defaults to DataReturnMode.AS_INPUT.
                     #allow_unsafe_jscode: bool = False, 
                     #enable_enterprise_modules: bool = False, 
                     #license_key: typing.Optional[str] = None, 
                     #try_to_convert_back_to_original_types: bool = True, 
                     conversion_errors=conversion_errors, #
                    #  Behaviour when conversion fails. One of:
                    #     ’raise’ -> invalid parsing will raise an exception.
                    #     ’coerce’ -> then invalid parsing will be set as NaT/NaN.
                    #     ’ignore’ -> invalid parsing will return the input.
                     #reload_data: bool = False, 
                     theme=theme, 
                        # 'streamlit' -> follows default streamlit colors
                        # 'alpine' -> follows default streamlit colors
                        # 'balham' -> follows default streamlit colors
                        # 'material' -> follows default streamlit colors
                     #key: typing.Optional[typing.Any] = None, 
                     custom_css=custom_css,
                     # default_column_parameters
                     )
    
    # Activate this line to see the input parameters    
    #st.write(locals())

    # st.write(locals()['height'])    
    # st.write(locals()['fit_columns_on_grid_load'])
    # st.write(locals()['update_mode'])
    # st.write(locals()['data_return_mode'])
    # # st.write(input_parameters['conversion_errors'])
    # # st.write(input_parameters['theme'])
    # # st.write(input_parameters['custom_css'])
    return grid_return

if __name__ == "__main__":
    import pandas as pd
    import streamlit as st  
    st.set_page_config(layout="wide")

    from st_aggrid import AgGrid, JsCode, GridOptionsBuilder, GridUpdateMode, DataReturnMode
    import functions_sql as psql


    @st.cache_data
    def get_transactions_data_as_df():
        df = psql.execute_sql("SELECT * FROM transaction")
        return df

    st.header("Personal Expenses")
    st.subheader("Transaction Data")

    df = get_transactions_data_as_df()

    get_grid(df, model='outercircles', entity='transaction')
    
    print('done ')  