import streamlit as st
import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from dotenv import load_dotenv
import time
import faiss  # Required for saving and loading FAISS indexes
import pickle  # For saving metadata alongside FAISS

load_dotenv()

## Load API Keys
os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY")
os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")

# Set up LLM and embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
llm = ChatGroq(groq_api_key=os.getenv("GROQ_API_KEY"), model_name="Llama3-8b-8192")

prompt = ChatPromptTemplate.from_template(
    """
    Answer the questions based on the provided context only.
    Please provide the most accurate respone based on the question
    <context>
    {context}
    <context>
    Question:{input}
    """
)

# File paths for FAISS index and metadata
INDEX_FILE = "faiss_index.faiss"
METADATA_FILE = "faiss_metadata.pkl"

# Function to create and save the vector database
def create_and_save_vector_database():

    st.write("Training model and creating vector database...")
    loader = PyPDFDirectoryLoader("rgukt_datasets")
    docs = loader.load()  # Load documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    final_documents = text_splitter.split_documents(docs)
    
    # Create FAISS vector database
    vector_store = FAISS.from_documents(final_documents, embeddings)
    
    # Save the FAISS index and metadata
    vector_store.save_local(INDEX_FILE)
    with open(METADATA_FILE, "wb") as f:
        pickle.dump(final_documents, f)
    
    st.write("Vector database created and saved to disk.")



# Function to load the vector database from disk
def load_vector_database():
    st.write("Loading vector database from disk...")
    vector_store = FAISS.load_local(INDEX_FILE, embeddings, allow_dangerous_deserialization=True)
    with open(METADATA_FILE, "rb") as f:
        final_documents = pickle.load(f)
    return vector_store, final_documents

st.title("RGUKT ChatBot")
user_prompt = st.text_input("Enter your query about rgukt-basar")

# Initialize vector database
if "vectors" not in st.session_state:
    if os.path.exists(INDEX_FILE) and os.path.exists(METADATA_FILE):
        # Load pre-trained FAISS index
        st.session_state.vectors, st.session_state.final_documents = load_vector_database()
    else:
        # Create and save FAISS index if it doesn't exist
        create_and_save_vector_database()
        st.session_state.vectors, st.session_state.final_documents = load_vector_database()

if user_prompt:
    # Ensure vector embedding is initialized before running the query
    if "vectors" not in st.session_state:
        st.write("Vector database is not initialized.")
    else:
        # Create the document chain and retriever
        document_chain = create_stuff_documents_chain(llm, prompt)
        retriever = st.session_state.vectors.as_retriever()
        retrieval_chain = create_retrieval_chain(retriever, document_chain)

        # Process query and retrieve response
        start = time.process_time()
        response = retrieval_chain.invoke({"input": user_prompt})
        st.write(f"Response time: {time.process_time() - start:.2f} seconds")

        st.write(response['answer'])

        # Display retrieved document context
        with st.expander("Document similarity search"):
            for i, doc in enumerate(response['context']):
                st.write(doc.page_content)
                st.write("----------------------------")
