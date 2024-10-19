import streamlit as st
import chromadb
from chromadb.utils import embedding_functions



# Initialize client
# client = chromadb.PersistentClient(path="chroma")

client = None
if client is None:
    client = chromadb.PersistentClient(path="./chroma")

# Sidebar for navigation
st.sidebar.title("Chroma Cheat Sheet")
nav_option = st.sidebar.radio("Navigation", ["Client Initialization", "Collection Methods", "Utility Methods"])

# Client Initialization
if nav_option == "Client Initialization":
    st.title("Client Initialization")
    
    st.subheader("In-memory Chroma")
    if st.button("Initialize In-memory Client"):
        client = chromadb.Client()
        st.success("In-memory client initialized successfully!")
    
    st.subheader("Persistent Chroma")
    path = st.text_input("Enter path for persistent data", "/path/to/data")
    if st.button("Initialize Persistent Client"):
        client = chromadb.PersistentClient(path=path)
        st.success(f"Persistent client initialized at {path}")
    
    st.subheader("HTTP Client")
    host = st.text_input("Enter host", "localhost")
    port = st.number_input("Enter port", value=8000)
    if st.button("Initialize HTTP Client"):
        client = chromadb.HttpClient(host=host, port=port)
        st.success(f"HTTP client initialized at {host}:{port}")

# Collection Methods
elif nav_option == "Collection Methods":
    st.title("Collection Methods")
    
    # Create a new collection
    collection_name = st.text_input("Enter collection name", "testname")
    if st.button("Create Collection"):
        collection = client.create_collection(collection_name)
        st.success(f"Collection '{collection_name}' created successfully!")
    
    # List all collections
    if st.button("List Collections"):
        collections = client.list_collections()
        st.write("Collections:")
        for collection in collections:
            st.write(f"- {collection.name}")
    
    # Add items to a collection
    if st.button("Add Items to Collection"):
        # get a collection or create if it doesn't exist already
        collection = client.get_or_create_collection(collection_name)
        embeddings = [[1.5, 2.9, 3.4], [9.8, 2.3, 2.9]]
        metadatas = [{"style": "style1"}, {"style": "style2"}]
        ids = ["uri9", "uri10"]
        collection.add(embeddings=embeddings, metadatas=metadatas, ids=ids)
        st.success("Items added to collection successfully!")
    
    # Query a collection
    if st.button("Query Collection"):
        # get a collection or create if it doesn't exist already
        collection = client.get_or_create_collection(collection_name)
        query_embeddings = [[1.1, 2.3, 3.2], [5.1, 4.3, 2.2]]
        n_results = st.number_input("Number of results", value=2, min_value=1)
        where = st.text_input("Filter (e.g., {'style': 'style2'})", "{}")
        where = eval(where) if where else None
        results = collection.query(query_embeddings=query_embeddings, n_results=n_results, where=where)
        st.write("Query Results:")
        for result in results:
            st.write(result)

# Utility Methods
else:
    st.title("Utility Methods")
    
    if st.button("Reset Database"):
        client.reset()
        st.warning("Database has been reset!")
    
    if st.button("Check Heartbeat"):
        heartbeat = client.heartbeat()
        st.write(f"Heartbeat: {heartbeat}")