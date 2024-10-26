import pandas as pd

import streamlit as st  
st.set_page_config(layout="wide")

from st_aggrid import AgGrid, JsCode, GridOptionsBuilder, GridUpdateMode, DataReturnMode

import functions_streamlit as st_func
import functions_sql as psql


@st.cache_data
def get_transactions_data_as_df():
    df = psql.execute_sql("SELECT * FROM transaction")
    return df

st.header("Personal Expenses")
st.subheader("Transaction Data")

# df = pd.read_csv('https://raw.githubusercontent.com/andfanilo/streamlit-aggrid/main/README.md')
# df = pd.read_csv('Output/standardized.csv')

df = get_transactions_data_as_df()

st_func.get_grid(df, 'outercircles', 'transaction')
# AgGrid(df)
print('done ')    
