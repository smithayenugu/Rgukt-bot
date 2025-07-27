from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate
from bs4 import BeautifulSoup
import requests
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="RGUKT ChatBot API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for caching
_embeddings = None
_chat_model = None
_vector_store = None
_retriever = None
_rag_chain = None
_section_agents = None

def get_embeddings():
    """Get or create embeddings instance"""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings

def get_chat_model():
    """Get or create chat model instance"""
    global _chat_model
    if _chat_model is None:
        _chat_model = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="gemma2-9b-it"
        )
    return _chat_model

def get_vector_store():
    """Get or create vector store instance"""
    global _vector_store
    if _vector_store is None:
        embeddings = get_embeddings()
        _vector_store = Chroma(persist_directory="./rgukt2_db", embedding_function=embeddings)
    return _vector_store

def get_retriever():
    """Get or create retriever instance"""
    global _retriever
    if _retriever is None:
        vector_store = get_vector_store()
        _retriever = vector_store.as_retriever()
    return _retriever

def get_rag_chain():
    """Get or create RAG chain instance"""
    global _rag_chain
    if _rag_chain is None:
        chat_model = get_chat_model()
        retriever = get_retriever()
        
        prompt = ChatPromptTemplate.from_template("""
            You are a specialized assistant for RGUKT (Rajiv Gandhi University of Knowledge Technologies).
            Follow these strict guidelines:

            1. Structure your responses clearly with appropriate headings and sections
            2. Use markdown-style formatting for better readability
            3. For lists and steps, use proper numbering and bullet points
            4. Include relevant details under each section
            5. For complex topics, break down information into subsections
            6. Always cite sources when available
            7. Format responses in HTML with proper semantic structure

            When answering:
            - Start with a clear title/heading for the topic
            - Provide a brief overview/introduction
            - Break down information into logical sections
            - Use bullet points for lists
            - Include specific details and requirements
            - End with any additional relevant information or next steps

            Context:
            <context>
            {context}
            </context>

            User Question: {input}

            Assistant Response (provide structured, comprehensive information):
        """)

        question_answering_chain = create_stuff_documents_chain(chat_model, prompt)
        _rag_chain = create_retrieval_chain(retriever, question_answering_chain)
    
    return _rag_chain

def get_section_agents():
    """Get or create section agents"""
    global _section_agents
    if _section_agents is None:
        chat_model = get_chat_model()
        
        # Define URL groups for different sections
        url_groups = {
            "Academics": [
                "https://www.rgukt.ac.in/academicprogrammes.html",
                "https://www.rgukt.ac.in/curricula.html",
                "https://www.rgukt.ac.in/academiccalender.html",
                "https://www.rgukt.ac.in/examination.html"
            ],
            "Departments": [
                "https://www.rgukt.ac.in/cse.html",
                "https://www.rgukt.ac.in/che.html",
                "https://www.rgukt.ac.in/ce.html",
                "https://www.rgukt.ac.in/ece.html",
                "https://www.rgukt.ac.in/mme.html",
                "https://www.rgukt.ac.in/me.html"
            ],
            "Faculty": [
                "http://www.rgukt.ac.in/cse-faculty.html",
                "https://www.rgukt.ac.in/che-faculty.html",
                "https://www.rgukt.ac.in/ece-faculty.html",
                "https://www.rgukt.ac.in/me-faculty.html",
                "https://www.rgukt.ac.in/mme-faculty.html",
                "https://www.rgukt.ac.in/civil-faculty.html"
            ],
            "Facilities": [
                "https://www.rgukt.ac.in/hostels.html",
                "https://www.rgukt.ac.in/library/",
                "https://www.rgukt.ac.in/hospital.html"
            ],
            "About": [
                "http://www.rgukt.ac.in/about-introduction.html",
                "http://www.rgukt.ac.in/vision-mission.html",
                "https://www.rgukt.ac.in/vc.html",
                "https://www.rgukt.ac.in/gc.html"
            ],
            "StudentLife": [
                "http://www.rgukt.ac.in/stu-campuslife.html",
                "http://www.rgukt.ac.in/anti-ragging.html"
            ],
            "Placement": [
                "https://www.rgukt.ac.in/placement/"
            ],
            "Contact": [
                "https://www.rgukt.ac.in/contactus.html"
            ]
        }

        def create_section_tool(urls: list, section_name: str) -> Tool:
            def scrape_section(query: str) -> str:
                try:
                    content = []
                    for url in urls:
                        try:
                            response = requests.get(url, timeout=10)
                            soup = BeautifulSoup(response.content, 'html.parser')
                            
                            main_content = soup.find('div', class_='page-row')
                            if main_content:
                                headings = main_content.find_all(['h1', 'h2', 'h3', 'h4'])
                                paragraphs = main_content.find_all('p')
                                lists = main_content.find_all(['ul', 'ol'])
                                
                                for heading in headings:
                                    content.append(f"<h3>{heading.text.strip()}</h3>")
                                
                                for p in paragraphs:
                                    if p.text.strip():
                                        content.append(f"<p>{p.text.strip()}</p>")
                                
                                for lst in lists:
                                    items = lst.find_all('li')
                                    if items:
                                        content.append("<ul>")
                                        for item in items:
                                            content.append(f"<li>{item.text.strip()}</li>")
                                        content.append("</ul>")
                            
                            logger.info(f"Successfully scraped {url}")
                        except Exception as e:
                            logger.warning(f"Error scraping {url}: {str(e)}")
                    
                    if content:
                        return "\n".join(content)
                    return f"<p>No specific information found in the {section_name} section.</p>"
                except Exception as e:
                    return f"<p>Error accessing {section_name} section: {str(e)}</p>"

            return Tool(
                name=f"RGUKT_{section_name}_Tool",
                func=scrape_section,
                description=f"Retrieves accurate information from the RGUKT {section_name} section."
            )

        # Create tools for each section
        section_tools = [create_section_tool(urls, section) for section, urls in url_groups.items()]

        # Initialize agents for each section
        _section_agents = {
            section: initialize_agent(
                tools=[tool],
                llm=chat_model,
                agent_type=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                verbose=False,
                handle_parsing_errors=True,
                max_iterations=2
            ) for section, tool in zip(url_groups.keys(), section_tools)
        }
    
    return _section_agents

# Pydantic models
class ChatMessage(BaseModel):
    text: str
    chat_history: List[Dict[str, str]] = []

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    chat_history: List[Dict[str, str]]

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    logger.info("Initializing RGUKT ChatBot API...")
    try:
        # Pre-initialize components
        get_embeddings()
        get_chat_model()
        get_vector_store()
        get_retriever()
        get_rag_chain()
        get_section_agents()
        logger.info("All components initialized successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Handle chat messages"""
    try:
        logger.info(f"Received chat message: {message.text[:50]}...")
        
        # Safely handle chat history
        try:
            updated_history = message.chat_history.copy() if message.chat_history else []
            updated_history.append({"role": "user", "content": message.text})
        except Exception as e:
            logger.warning(f"Error handling chat history: {str(e)}")
            updated_history = [{"role": "user", "content": message.text}]

        # CSS styles
        styles = {
            'container': 'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; max-width: 800px; margin: 0 auto; line-height: 1.6;',
            'main_title': 'color: #000000; font-size: 28px; font-weight: 700; margin-bottom: 24px; padding-bottom: 12px; border-bottom: 1px solid #e0e0e0;',
            'section': 'background: #ffffff; border-radius: 8px; padding: 20px; margin: 16px 0;',
            'heading': 'color: #000000; font-size: 22px; font-weight: 600; margin: 20px 0 12px 0; padding-bottom: 8px; border-bottom: 1px solid #e0e0e0;',
            'subheading': 'color: #000000; font-size: 18px; font-weight: 600; margin: 16px 0 8px 0;',
            'paragraph': 'color: #000000; margin: 12px 0; font-size: 16px; line-height: 1.6;',
            'list': 'margin: 12px 0 12px 24px; padding: 0;',
            'list_item': 'margin: 8px 0; color: #000000; font-size: 16px; line-height: 1.6;',
            'footer': 'margin-top: 24px; padding-top: 16px; border-top: 1px solid #e0e0e0; color: #000000; font-size: 14px;',
            'overview_section': 'background: #ffffff; border-radius: 8px; padding: 16px; margin: 16px 0;'
        }

        # Check for greetings
        greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
        if message.text.lower().strip() in greetings:
            response = f"""
            <div style="{styles['container']}">
                <p style="{styles['paragraph']}">Hello! How can I assist you with RGUKT university-related queries?</p>
            </div>
            """
        else:
            # Format chat history with proper validation
            formatted_history = ""
            if message.chat_history:
                try:
                    formatted_history = "\n".join([
                        f"{'User' if msg.get('role') == 'user' else 'Assistant'}: {msg.get('content', '')}"
                        for msg in message.chat_history
                        if isinstance(msg, dict) and 'role' in msg and 'content' in msg
                    ])
                except Exception as e:
                    logger.warning(f"Error formatting chat history: {str(e)}")
                    formatted_history = ""

            # Try RAG chain first
            try:
                rag_chain = get_rag_chain()
                context_response = rag_chain.invoke({
                    "input": message.text,
                    "chat_history": formatted_history
                })
                
                if "I'm sorry" in context_response['answer'] or "cannot respond" in context_response['answer']:
                    # Fallback to section agents
                    query = message.text.lower()
                    section_responses = []

                    section_keywords = {
                        "Academics": ["course", "program", "curriculum", "academic", "study", "examination"],
                        "Departments": ["department", "cse", "ece", "mechanical", "chemical", "civil"],
                        "Faculty": ["faculty", "professor", "teacher", "staff"],
                        "Facilities": ["hostel", "library", "hospital", "facility"],
                        "About": ["about", "vision", "mission", "vice-chancellor", "director", "vc"],
                        "StudentLife": ["student", "campus", "life", "ragging"],
                        "Placement": ["placement", "job", "career", "recruitment"],
                        "Contact": ["contact", "address", "phone", "email"]
                    }

                    section_agents = get_section_agents()
                    for section, keywords in section_keywords.items():
                        if any(keyword in query for keyword in keywords):
                            try:
                                section_response = section_agents[section].invoke({
                                    "input": message.text,
                                    "chat_history": formatted_history
                                })
                                section_responses.append(section_response['output'])
                            except Exception as e:
                                logger.warning(f"Error with {section} agent: {str(e)}")

                    if section_responses:
                        raw_response = "\n".join(section_responses)
                    else:
                        raw_response = "I'm sorry, I can only assist with RGUKT university-related queries."
                else:
                    raw_response = context_response['answer']
                    
            except Exception as e:
                logger.error(f"Error in RAG chain: {str(e)}")
                raw_response = "I'm sorry, I encountered an error while processing your query. Please try again."

            # Format the response
            def format_text(text):
                while '**' in text:
                    text = text.replace('**', '<strong>', 1)
                    text = text.replace('**', '</strong>', 1)
                return text

            topic = message.text.strip('?').title()
            formatted_response = f"""
            <div style="{styles['container']}">
                <h1 style="{styles['main_title']}">{topic}</h1>
                <div style="{styles['overview_section']}">
            """

            lines = raw_response.split('\n')
            in_list = False
            current_list = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                formatted_line = format_text(line)

                if line.startswith('###'):
                    if in_list:
                        formatted_response += f"<ul style='{styles['list']}'>" + "".join(current_list) + "</ul>"
                        current_list = []
                        in_list = False
                    formatted_response += f'<h3 style="{styles["subheading"]}">{format_text(line.replace("###", "").strip())}</h3>'
                
                elif line.startswith('##'):
                    if in_list:
                        formatted_response += f"<ul style='{styles['list']}'>" + "".join(current_list) + "</ul>"
                        current_list = []
                        in_list = False
                    formatted_response += f'<h2 style="{styles["heading"]}">{format_text(line.replace("##", "").strip())}</h2>'

                elif line.startswith(('- ', '* ', '• ')):
                    in_list = True
                    current_list.append(f'<li style="{styles["list_item"]}">{format_text(line[2:])}</li>')

                elif line.startswith(('1.', '2.', '3.')):
                    in_list = True
                    current_list.append(f'<li style="{styles["list_item"]}">{format_text(line[2:])}</li>')

                else:
                    if in_list:
                        formatted_response += f"<ul style='{styles['list']}'>" + "".join(current_list) + "</ul>"
                        current_list = []
                        in_list = False
                    formatted_response += f'<p style="{styles["paragraph"]}">{formatted_line}</p>'

            if in_list:
                formatted_response += f"<ul style='{styles['list']}'>" + "".join(current_list) + "</ul>"

            formatted_response += f"""
                </div>
                <div style="{styles['footer']}">
                    <p>Source: RGUKT Official Information</p>
                </div>
            </div>
            """

            response = formatted_response

                # Safely add assistant response to history
        try:
            updated_history.append({"role": "assistant", "content": response})
        except Exception as e:
            logger.warning(f"Error adding assistant response to history: {str(e)}")

        logger.info("Chat response generated successfully")
        
        return ChatResponse(
            response=response,
            timestamp=datetime.now().isoformat(),
            chat_history=updated_history
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/clear-history", response_model=ChatResponse)
async def clear_history():
    """Clear chat history"""
    return ChatResponse(
        response="Chat history cleared",
        timestamp=datetime.now().isoformat(),
        chat_history=[]
    )

@app.get("/")
async def read_root():
    """Health check endpoint"""
    return {"message": "RGUKT ChatBot API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test components
        get_embeddings()
        get_chat_model()
        get_vector_store()
        get_retriever()
        get_rag_chain()
        get_section_agents()
        
        return {
            "status": "healthy",
            "components": {
                "embeddings": "initialized",
                "chat_model": "initialized", 
                "vector_store": "initialized",
                "retriever": "initialized",
                "rag_chain": "initialized",
                "section_agents": "initialized"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")