import os
from dotenv import load_dotenv
import streamlit as st
from langchain_groq import ChatGroq
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize PDF loader and process documents
def initialize_documents():
    loader = PyPDFLoader('Academic_Regulations_Hand_Book.pdf')
    documents = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", "!", "?"],
        chunk_size=1000,
        chunk_overlap=50,
        length_function=len,
        is_separator_regex=False
    )
    return text_splitter.split_documents(documents)

# Initialize embeddings and vector store
def initialize_vectorstore(final_docs):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return Chroma.from_documents(
        documents=final_docs,
        embedding=embeddings,
        persist_directory="./rgukt2_db"
    )

# Setup RAG chain
def setup_rag_chain():
    # Initialize embeddings and retriever
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma(persist_directory="./rgukt2_db", embedding_function=embeddings)
    retriever = db.as_retriever()

    # Setup prompt template
    system_prompt = """
You are an AI assistant for RGUKT (Rajiv Gandhi University of Knowledge Technologies). 
You must only answer questions using the provided context, which is extracted from the Academic Regulations Handbook. 

Your responses must:
1. Be concise, precise, and fact-based, without introductory phrases like 'According to the handbook...'.
2. Only include specific section numbers, page references, or detailed citations when directly relevant to the query.
3. Use bullet points or numbered lists for clarity when multiple points are required.
4. Maintain a professional and formal tone at all times.
5. Avoid any attempt to answer queries that are outside the scope of the provided handbook.

Ensure to cover queries related to the following topics using the relevant information from the handbook:
- Admissions
- Academics
- Placements
- Faculty
- Students
- Hostels
- Fees
- Programs
- Alumni
- Duration and Program of Study
- Allocation of Seats in Engineering Branches
- Rules and Regulations of Attendance
- Regulations for Granting Withdrawal on Medical Grounds and Taking Re-admission
- Scheme of Instruction and Examination
- Grading System and Award of Division
- Award of Degree
- Examination Fees
- Rules of Promotion
- Remedial Examination Rules
- General Rules of Examinations
- Transitory Regulations
- Rules Regarding Conduct and Discipline

If the query is not related to RGUKT or the handbook, respond with:
"I'm sorry, I can only assist with queries related to RGUKT."

Context:
{context}
"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # Initialize LLM and create chain
    llm = ChatGroq(groq_api_key=groq_api_key, model_name="Mixtral-8x7B-32768")
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, question_answer_chain)

def main():
    st.title("RguBot")
    
    # Initialize documents and vector store if not already done
    if not os.path.exists("./rgukt2_db"):
        final_docs = initialize_documents()
        vectorstore = initialize_vectorstore(final_docs)
    
    # Setup RAG chain
    rag_chain = setup_rag_chain()
    
    # Get user input
    input_question = st.text_input("What's in your mind?")
    
    # Generate response
    if input_question:
        try:
            response = rag_chain.invoke({"input": input_question})
            st.write(response['answer'])
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
