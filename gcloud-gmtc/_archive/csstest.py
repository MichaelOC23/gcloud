import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid
from st_aggrid import GridUpdateMode, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder

#Define some data
cat_data = {'Cat': ['Fluffy', 'Whiskers', 'Simba', 'Nala', 'Oliver', 'Charlie', 'Max', 'Lucy', 'Mittens', 'Daisy'],
                'Frequency of Grooming': np.random.randint(low=1, high=7, size=10),
                'Duration of Grooming (minutes)': np.random.randint(low=5, high=30, size=10),
                'Method': ['Licking', 'Brushing', 'Licking', 'Brushing', 'Licking', 'Brushing', 'Licking', 'Brushing', 'Licking', 'Brushing']}
cat_df = pd.DataFrame(cat_data)



custom_css = {
    ".ag-root.ag-unselectable.ag-layout-normal": 
        {
            "font-size": "13px !important",
            "font-family": "Roboto, sans-serif !important;"
        },
    ".ag-header-cell-text": 
        {
            "color": "#495057 !important;"
        },
    ".ag-theme-alpine .ag-ltr .ag-cell": 
        {
            "color": "#444444 !important;"
        },
    ".ag-theme-alpine .ag-row-odd": 
        {
            "background": "rgba(243, 247, 249, 0.3) !important;",
            "border": "1px solid #eee !important;"
        },
    ".ag-theme-alpine .ag-row-even": 
        {
            "border-bottom": "1px solid #3162bd !important;"
        },
    ".ag-theme-light button": 
        {
            "font-size": "0 !important;", 
            "width": "auto !important;",
            "height": "24px !important;",
            "border": "1px solid #eee !important;", 
            "margin": "4px 2px !important;",
            "background": "#3162bd !important;", 
            "color": "#3162bd !important;",
            "border-radius": "3px !important;"
        },
    ".ag-theme-light button:before": 
        {
            "content": "‘Confirm’ !important", 
            "position": "relative !important",
            "z-index": "1000 !important", 
            "top": "0 !important",
            "font-size": "12px !important", 
            "left": "0 !important",
            "padding": "4px !important"
        },
}


# # Define custom CSS
# custom_css = {
#     ".ag-row-hover": {"background-color": "red !important"},
#     ".ag-header-cell-label": {"background-color": "orange !important"}
#     }
#Build Table
gd = GridOptionsBuilder.from_dataframe(cat_df)


ag_grid_d = AgGrid(
cat_df,
height=150,
title='query',
gridOptions=gd.build(),
# theme=config.GRID_THEME,
update_mode=GridUpdateMode.MANUAL,
# data_return_mode=DataReturnMode.AS_INPUT,
custom_css=custom_css,
allow_unsafe_jscode=True
)


# table = AgGrid(
#     cat_df,
#     custom_css=custom_css,
#     allow_unsafe_jscode=True
# )