import sys
import os
sys.path.append('/Users/michasmi/code/communify/shared')

import streamlit as st
from streamlit_elements import elements, mui, html
from datetime import date, timedelta    
import finnhub
import yfinance as yf
import functions_common as oc2c
oc2c.configure_streamlit_page(Title="Streamlit UI Examples")
# import nasdaqdatalink
# import quandl

st.title("")
# Create a tab in the main page
Text_Tab0, Markdown_Tab1, Controls_Tab3, Data_Views_tab4, Mui_Tab2 = st.tabs(
    ["Text", "Markdown", "Controls", "Data Views", "MUI Components"])
with Mui_Tab2:
    with elements("MUI Components"):

        from streamlit_elements import editor, mui, sync, lazy

        if "content" not in st.session_state:
            st.session_state.content = "Default value"

        mui.Typography("Content: ", st.session_state.content)

        def update_content(value):
            st.session_state.content = value

        editor.Monaco(
            height=300,
            defaultValue=st.session_state.content,
            onChange=lazy(update_content)
        )

        mui.Button("Update content", onClick=sync())

        editor.MonacoDiff(
            original="Happy Streamlit-ing!",
            modified="Happy Streamlit-in' with Elements!",
            height=300,
        )

        # # mui.Typography("Autocomplete", component="h6")
        # with mui.Paper(elevation=3, variant="outlined", square=True):
        #     mui.TextField(
        #     label="My text input",
        #     defaultValue="Type here",
        #     variant="outlined",
        #     )
        #     mui.Collapse(in_=True)


with Text_Tab0:

    # {Begin} Page Title
    with st.container(border=True,):
        st.title('Title')
        st.caption('No divider allowed')
    st.divider()
    # {End}

    # Page Header
    with st.container(border=True,):
        st.header('Page Header',
                  divider=st.session_state['settings']['divider-color'],)
        st.caption('Can have a divider')
    st.divider()

    # Page Subheader
    with st.container(border=True,):
        st.subheader('Subheader', divider="gray")
        st.caption('Can have a divider')
    st.divider()

    with st.container(border=True,):
        st.text('Fixed width text')
    st.divider()

    with st.container(border=True,):
        st.subheader('Markdown',)
        st.markdown("*Streamlit* is **really** ***cool***.")
        st.markdown('''
            :red[Streamlit] :orange[can] :green[write] :blue[text] :violet[in]
            :gray[pretty] :rainbow[colors].''')
        st.markdown("Here's a bouquet &mdash;\
                    :tulip::cherry_blossom::rose::hibiscus::sunflower::blossom:")
        multi = '''If you end a line with two spaces,
        a soft return is used for the next line.
        Two (or more) newline characters in a row will result in a hard return.
        '''
        st.markdown(multi)
    with st.container(border=True,):
        st.subheader('Text Areas',)
        md = st.text_area('Type in your markdown string (without outer quotes)',
                          "Happy Streamlit-ing! :balloon:")

    st.header('Code', divider="blue")
    code = '''def hello():
        print("Hello, Streamlit!")
        #look at the code to see how this was specified as Python.
        '''
    st.code(code, language='python', line_numbers=True)
    st.divider()

    st.header('Formula / Latex', divider="blue")
    st.latex(r''' e^{i\pi} + 1 = 0 ''')
    st.divider()

    st.header('"Write"', divider="blue")
    st.write('Most objects')
    st.divider()

    st.header('Text Area', divider="blue")

    """\n
    **Key parameters**:\n
    :blue[label (str):] A short label explaining to the user what this input is for. The label can optionally contain Markdown and supports the following elements: Bold, Italics, Strikethroughs, Inline Code, Emojis, and Links.          This also supports: Emoji shortcodes, such as :+1: and :sunglasses:. For a list of all supported codes, see https://share.streamlit.io/streamlit/emoji-shortcodes.  LaTeX expressions, by wrapping them in "$" or "$$" (the "$$" must be on their own lines). Supported LaTeX functions are listed at https://katex.org/docs/supported.html. , where color needs to be replaced with any of the following supported colors: blue, green, orange, red, violet, gray/grey, rainbow. Unsupported elements are unwrapped so only their children (text contents) render. Display unsupported elements as literal characters by backslash-escaping them. E.g. 1\. Not an ordered list.
    :blue[on_change (callable):] An optional callback invoked when this text_area's value changes.\n
    :blue[args (tuple):] An optional tuple of args to pass to the callback.\n
    :blue[value (object or None):] The text value of this widget when it first renders. This will be cast to str internally. If None, will initialize empty and return None until the user provides input. Defaults to empty string.\n
    :blue[kwargs (dict):] An optional dict of kwargs to pass to the callback."""

    st.text_area("A short label to explain the text input", value="Initial value in the text box", height=None, max_chars=None, key=None,
                 help=None, on_change=None, args=None, kwargs=None, placeholder="An optional string when empty", disabled=False, label_visibility="visible")

with Controls_Tab3:
    st.button("Click me")
    # st.download_button("Download file", msft.history_metadata)
    st.link_button("Go to google", 'https://www.google.com')
    # st.data_editor("Edit data", msft.history_metadata)
    st.checkbox("I agree")
    st.toggle("Enable")
    st.radio("Pick one", ["cats", "dogs"])
    st.selectbox("Pick one", ["cats", "dogs"])
    st.multiselect("Buy", ["milk", "apples", "potatoes"])
    st.slider("Pick a number", 0, 100)
    st.select_slider("Pick a size", ["S", "M", "L"])
    st.text_input("First name")
    st.number_input("Pick a number", 0, 10)
    st.text_area("Text to translate")
    st.date_input("Your birthday")
    st.time_input("Meeting time")
    st.file_uploader("Upload a CSV")
    
    st.color_picker("Pick a color")
    if st.button("Show Video"):
        st.camera_input("Take a picture")
        

with Data_Views_tab4:
    stock_list = {'IVV', 'AAPL', 'NVDA', 'MSFT', 'ITOT', 'IEFA', 'RMBS', 'QUAL', 'ESGU', 'DAL', 'GOOGL', 'MTSI', 'AMZN', 'HSCZ', 'TMUS', 'IXN', 'AER', 'DVN', 'KBR', 'USMV', 'LLY', 'IGT', 'VST', 'ACHC', 'CRTO', 'GOOG', 'NOW', 'JPM', 'UNH', 'V', 'CAR', 'MOH', 'VECO', 'CLF', 'ETN', 'ESGE', 'FTI', 'LUV', 'PG', 'VRNS', 'DUK', 'AVY', 'SIZE', 'CLH', 'KD', 'THS', 'KAR', 'PNC', 'BKU', 'APO', 'ENTG', 'WIX', 'HAE', 'ORA', 'TPX', 'CIEN', 'LNG', 'MAR', 'IEMG', 'UBER', 'CCK', 'PLD', 'MCK', 'TSLA', 'CB', 'SSYS', 'ITRI', 'TJX', 'OSIS', 'ORCL', 'MDLZ', 'BANC', 'TDG', 'OIS', 'JBLU', 'VRTX', 'WCN', 'ABBV', 'CI', 'MET', 'MDT', 'CAL', 'APH', 'PXD', 'HBAN', 'LGF', 'T', 'KO', 'MCD', 'XPO', 'CRNC', 'ULTA', 'SPGI', 'ADI', 'VREX', 'MSI', 'BKNG', 'WFC', 'CRL', 'TT', 'TW', 'BOX', 'ATRC', 'DTM', 'TEX', 'TMO', 'GXO', 'HD', 'XOM',
                  'DXCM', 'PDCO', 'STZ', 'BMY', 'SMAR', 'PKG', 'AME', 'LIN', 'EQH', 'TOL', 'REGN', 'LVS', 'ELV', 'RLJ', 'PLCE', 'CNNE', 'BSX', 'CHS', 'NKE', 'SHW', 'BLK', 'VMI', 'HON', 'ADEA', 'JNJ', 'BA', 'PTEN', 'WRBY', 'AON', 'FCX', 'ZIMV', 'CMA', 'CSCO', 'ODP', 'JCI', 'EPAC', 'VIAV', 'CGNT', 'TCBI', 'COHR', 'UIS', 'TKO', 'DLTR', 'DRQ', 'REZI', 'FI', 'ICE', 'VRNT', 'CNDT', 'PSX', 'ADSK', 'IART', 'BX', 'CNP', 'INTU', 'ECL', 'OSPN', 'ZTS', 'STWD', 'COO', 'ACA', 'RDWR', 'FCPT', 'BFH', 'ALL', 'LAB', 'LW', 'TRU', 'UA', 'COP', 'TRGP', 'BYON', 'MRCY', 'GS', 'NVT', 'INVZ', 'CEVA', 'BW', 'VSAT', 'BMRN', 'FTCH', 'CWBHF', 'CEG', 'EXC', 'SMTC', 'CVSI', 'ESGU', 'IVV', 'IVW', 'EFG', 'EFV', 'EMXC', 'IEMG', 'GOVT', 'HYDB', 'ICVT', 'IUSB', 'TLT', 'OEF', 'QUAL', 'USMV', 'IFRA', 'IXC', 'IYW', 'LQD', 'MBB', 'TFLO', 'TIP', 'EMB'}
    finnhub_client = finnhub.Client(api_key=os.environ['FINNHUB_API_KEY'])

    # Variable as today's date (with no time)
    today = date.today()

    # 30 days prior to today
    thirty_days_prior = today - timedelta(days=30)

    # ? Page Level Code
    # Tab1, Tab2, Tab3 = st.tabs(["Components", "Data Views", "TBD"])

    # ? Data to use
    msft = yf.Ticker("MSFT")
    # ? Standard Data Components
    # t16 = st.header('Data Components', divider="blue")
    company_profile2 = finnhub_client.company_profile2(symbol='CSCO')

    # Data Frame
    st.subheader('Data Frame')
    st.dataframe(company_profile2)
    st.dataframe(msft.quarterly_balance_sheet)
    st.divider()

    # JSON
    st.subheader('JSON')
    st.json(company_profile2)
    st.divider()

    # Metric
    st.subheader('Metric / KPI')
    st.metric('AAPL Price', 42.54, .023)
    st.divider()

    # Table
    st.subheader('Table')
    st.table(company_profile2)
    st.divider()

    # get all stock info
    msft.info

    # get historical market data
    hist = msft.history(period="1mo")

    # show meta information about the history (requires history() to be called first)
    msft.history_metadata

    # show actions (dividends, splits, capital gains)
    msft.actions
    msft.dividends
    msft.splits
    msft.capital_gains  # only for mutual funds & etfs

    # show share count
    msft.get_shares_full(start="2022-01-01", end=None)

    # show financials:
    # - income statement
    msft.income_stmt
    msft.quarterly_income_stmt
    # - balance sheet
    msft.balance_sheet

    # - cash flow statement
    msft.cashflow
    msft.quarterly_cashflow
    # see `Ticker.get_income_stmt()` for more options

with Markdown_Tab1:
    oc2c.display_markdown_helper()
