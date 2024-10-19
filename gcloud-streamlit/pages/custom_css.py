import datetime

import numpy as np
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder


now = int(datetime.datetime.now().timestamp())
start_ts = now - 3 * 30 * 24 * 60 * 60


st.cache_data 
def make_data():
    df = pd.DataFrame(
        {
            "timestamp": np.random.randint(start_ts, now, 20),
            "side": [np.random.choice(["buy", "sell"]) for i in range(20)],
            "base": [np.random.choice(["JPY", "GBP", "CAD"]) for i in range(20)],
            "quote": [np.random.choice(["EUR", "USD"]) for i in range(20)],
            "amount": list(
                map(
                    lambda a: round(a, 2),
                    np.random.rand(20) * np.random.randint(1, 1000, 20),
                )
            ),
            "price": list(
                map(
                    lambda p: round(p, 5),
                    np.random.rand(20) * np.random.randint(1, 10, 20),
                )
            ),
        }
    )
    df["cost"] = round(df.amount * df.price, 2)
    df.insert(
        0,
        "datetime",
        df.timestamp.apply(lambda ts: datetime.datetime.fromtimestamp(ts)),
    )
    return df.sort_values("timestamp").drop("timestamp", axis=1)


df = make_data()
gb = GridOptionsBuilder.from_dataframe(df)

row_class_rules = {
    "trade-buy-green": "data.side == 'buy'",
    "trade-sell-red": "data.side == 'sell'",
}
gb.configure_grid_options(rowClassRules=row_class_rules)
grid_options = gb.build()

# custom_css = {
#     ".ag-root.ag-unselectable.ag-layout-normal": {
#         "font-size": "13px !important",
#         "font-family": "Roboto, sans-serif !important"
#     },
#     ".ag-header-cell-text": {
#         "color": "#495057 !important"
#     },
#     ".ag-theme-alpine .ag-ltr .ag-cell": {
#         "color": "#444 !important"
#     },
#     ".ag-theme-alpine .ag-row-odd": {
#         "background": "rgba(243, 247, 249, 0.3) !important",
#         "border": "1px solid #eee !important"
#     },
#     ".ag-theme-alpine .ag-row-even": {
#         "border-bottom": "1px solid #eee !important"
#     },
#     ".ag-theme-light button": {
#         "font-size": "0 !important",
#         "width": "auto !important",
#         "height": "24px !important",
#         "border": "1px solid #eee !important",
#         "margin": "4px 2px !important",
#         "background": "#3162bd !important",
#         "color": "#fff !important",
#         "border-radius": "3px !important"
#     },
#     ".ag-theme-light button:before": {
#         "content": "'Confirm' !important",  # Correct usage of single quotes inside CSS content
#         "position": "relative !important",
#         "z-index": "1000 !important",
#         "top": "0 !important",
#         "font-size": "12px !important",
#         "left": "0 !important",
#         "padding": "4px !important"
#     }
# }

st.title("rowClassRules Test")
AgGrid(df, theme="streamlit",  gridOptions=grid_options)
# AgGrid(df, theme="streamlit", custom_css=custom_css, gridOptions=grid_options)


