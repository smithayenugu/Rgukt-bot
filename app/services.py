import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import Dict
from .models import ChatMessage, ChatHistory

# Load environment variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

class ChatService:
    def __init__(self):
        self.initialize_if_needed()
        self.rag_chain = self.setup_rag_chain()
        self.chat_histories: Dict[str, ChatHistory] = {}

    def initialize_documents(self):
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

    def initialize_vectorstore(self, final_docs):
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        return Chroma.from_documents(
            documents=final_docs,
            embedding=embeddings,
            persist_directory="./rgukt2_db"
        )

    def initialize_if_needed(self):
        if not os.path.exists("./rgukt2_db"):
            final_docs = self.initialize_documents()
            self.initialize_vectorstore(final_docs)

    def setup_rag_chain(self):
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        db = Chroma(persist_directory="./rgukt2_db", embedding_function=embeddings)
        retriever = db.as_retriever()

        system_prompt = """
        You are an AI assistant for RGUKT (Rajiv Gandhi University of Knowledge Technologies). 
        You must only answer questions using the provided context, which is extracted from the Academic Regulations Handbook. 

        Your responses must:
        1. Be concise, precise, and fact-based, without introductory phrases like 'According to the handbook...'.
        2. Only include specific section numbers, page references, or detailed citations when directly relevant to the query.
        3. Use bullet points or numbered lists for clarity when multiple points are required.
        4. Maintain a professional and formal tone at all times.
        5. Avoid any attempt to answer queries that are outside the scope of the provided handbook.

        If the query is not related to RGUKT or the handbook, respond with:
        "I'm sorry, I can only assist with queries related to RGUKT."

        Context:
        {context}
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

        llm = ChatGroq(groq_api_key=groq_api_key, model_name="Mixtral-8x7B-32768")
        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        return create_retrieval_chain(retriever, question_answer_chain)

    async def process_question(self, question: str, session_id: str) -> str:
        try:
            # Get response from RAG chain
            response = self.rag_chain.invoke({"input": question})
            answer = response['answer']
            
            # Create chat message
            message = ChatMessage(
                user_message=question,
                bot_response=answer,
                timestamp=datetime.now().isoformat()
            )
            
            # Store in chat history
            if session_id not in self.chat_histories:
                self.chat_histories[session_id] = ChatHistory(
                    messages=[],
                    session_id=session_id
                )
            
            self.chat_histories[session_id].messages.append(message)
            
            return answer
            
        except Exception as e:
            raise Exception(f"Error processing question: {str(e)}")

    def get_chat_history(self, session_id: str) -> ChatHistory:
        return self.chat_histories.get(session_id) 