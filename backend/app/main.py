from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
import os
import re
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from bs4 import BeautifulSoup
import requests
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
_embeddings = None
_vector_store = None
_retriever = None
_gemini_client = None

# ============================================================
# AI MODEL (Gemini first, Groq fallback)
# ============================================================
def call_llm(prompt: str) -> str:
    """Call Gemini if available, otherwise fall back to Groq"""
    # Try Gemini first
    gemini_result = _try_gemini(prompt)
    if gemini_result:
        return gemini_result
    
    # Try Groq as fallback
    groq_result = _try_groq(prompt)
    if groq_result:
        return groq_result
    
    return None

def _try_gemini(prompt: str) -> str:
    """Call Gemini 2.5 Flash directly with retry logic"""
    global _gemini_client
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        return None
    
    # Skip Gemini if we recently hit rate limits (cooldown period)
    if hasattr(_try_gemini, '_last_429_time'):
        import time
        time_since_429 = time.time() - _try_gemini._last_429_time
        if time_since_429 < 60:  # 60 second cooldown
            return None
    
    try:
        if _gemini_client is None:
            import google.genai as genai
            _gemini_client = genai.Client(api_key=key)
        response = _gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        if response and response.text:
            logger.info("Used Gemini 2.5 Flash")
            return response.text
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            logger.warning("Gemini rate limited, backing off for 60s")
            import time
            _try_gemini._last_429_time = time.time()
        else:
            logger.warning(f"Gemini failed: {error_msg[:60]}")
    return None

def _try_groq(prompt: str) -> str:
    """Call Groq as fallback"""
    try:
        from langchain_groq import ChatGroq
        # Your installed LangChain layout may not expose `langchain.prompts`.
        from langchain_core.messages import HumanMessage
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None
        
        models_to_try = ["openai/gpt-oss-20b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
        for model_name in models_to_try:
            try:
                llm = ChatGroq(api_key=api_key, model_name=model_name)
                result = llm.invoke([HumanMessage(content=prompt)])
                if result and hasattr(result, 'content'):
                    logger.info(f"Used Groq: {model_name}")
                    return result.content
            except Exception:
                continue
    except Exception as e:
        logger.warning(f"Groq failed: {str(e)[:60]}")
    return None


def get_embeddings():
    """Get or create embeddings instance"""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings

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

# --- HOD and Departments Lookup Tables ---
DEPARTMENTS = [
    "Bio Sciences", "Chemical Engineering", "Chemistry", "Civil Engineering",
    "Computer Science and Engineering", "Electrical Engineering",
    "Electronics and Communications Engineering", "Humanities and Social Sciences",
    "Management", "Mathematics", "Mechanical Engineering",
    "Metallurgical and Materials Engineering", "Physics",
]

BTECH_BRANCHES = [
    "Chemical Engineering", "Civil Engineering", "Computer Science and Engineering",
    "Electrical Engineering", "Electronics and Communications Engineering",
    "Mechanical Engineering", "Metallurgical and Materials Engineering",
]

def get_departments_info(query: str) -> str:
    """Check if query asks about departments/branches"""
    q = query.lower()
    branch_list_keywords = ["list of", "what are the branches", "what are the departments",
                            "what branches", "what departments", "name the branches",
                            "name the departments", "tell me the branches", "tell me the departments",
                            "branches available", "departments available", "branches offered",
                            "departments offered", "show me the branches", "show me the departments",
                            "how many branches", "how many departments", "all branches", "all departments",
                            "list branches", "list departments", "which branches", "which departments"]
    is_list = any(w in q for w in branch_list_keywords)
    if is_list and any(w in q for w in ["b.tech", "btech", "b tech", "engineering"]):
        return "BTech branches offered at RGUKT Basar:\n" + "\n".join(f"- {b}" for b in BTECH_BRANCHES)
    if "puc" in q and is_list:
        return "The PUC (Pre-University Course) at RGUKT Basar is a common program for all students during the first two years. It includes foundational subjects in Sciences, Mathematics, and Humanities."
    if is_list:
        return "Departments at RGUKT Basar:\n" + "\n".join(f"- {d}" for d in DEPARTMENTS)
    return None

# --- FAQ Lookup Table ---
# Hardcoded answers for common questions (saves API calls)
RGUKT_FAQ = {
    "eligibility_bt": """Eligibility Criteria and Requirements for B.Tech Programs at RGUKT Basar:

PROGRAM STRUCTURE:
- RGUKT offers a 6-year Integrated B.Tech program after 10th class examination (SSC)
- First part: 2-year Pre-University Course (PUC) equivalent to (TS) Intermediate
- Second part: 4-year Engineering course leading to B.Tech degree
- PUC offers tracks in Mathematics, Physics, Chemistry and Life sciences (MPC + BiPC)

ELIGIBILITY CRITERIA:
- Candidates must have passed the 10th Class (SSC) or equivalent examination
- Selection is based on merit in the 10th class board examination
- Priority is given to top rural students from Telangana (typically within top 5-10%)
- Admissions are conducted through a counseling process based on merit rank
- The program is designed for gifted rural youth of Telangana state

B.TECH BRANCHES OFFERED:
- Chemical Engineering
- Civil Engineering
- Computer Science and Engineering (CSE)
- Electrical Engineering (EEE)
- Electronics and Communications Engineering (ECE)
- Mechanical Engineering
- Metallurgical and Materials Engineering

HOW TO APPLY:
1. Applications are invited through the official RGUKT website (rgukt.ac.in)
2. Fill the online application form with personal and academic details
3. Upload required documents (photograph, signature, certificates)
4. Pay the application fee online
5. Appear for counseling based on merit rank
6. Select preferred branch during counseling
7. Report to the campus with original documents for verification

For updates, visit https://www.rgukt.ac.in regularly.""",

    "about_rgukt": """About Rajiv Gandhi University of Knowledge Technologies (RGUKT) Basar:

RGUKT Basar is a unique university established by the Government of erstwhile Andhra Pradesh that actively uses Information and Communication Technology (ICT) in teaching. It is perhaps the first of its kind in the country with an educational model that is intensely ICT based.

Key Facts:
- Located at Basar (the abode of Gnyana Saraswathi, Goddess of knowledge) in Nirmal District, Telangana
- Campus is set in about 272 acres near the banks of river Godavari
- Primary objective: provide high quality educational opportunities for the rural youth of the state
- Houses about 6000 students along with 250 faculty members and 120 support staff
- Accredited by NAAC with 'C' Grade
- Recognized Under Sections 2(f) and 12B of the UGC Act, 1956, as a State University

Campus Facilities:
- Academic blocks with more than 140 ICT equipped classrooms
- Well-equipped laboratories
- Libraries with more than 1,00,000 volumes
- Boys' and girls' hostels and mess blocks
- Laundromat, bank, ATM, Shopping Complex, post office, primary health center
- Indoor and outdoor recreational facilities, gymnasium, courts for basketball, badminton, table tennis, cricket
- 6 hostel blocks (3 for boys, 3 for girls) accommodating around 8000 students

The selection process follows approved rules and has very high competition where only the top rural graduates (mostly within the top 5%) get the opportunity to study at RGUKT.""",

    "vc_role": """Vice Chancellor of RGUKT Basar:

The current Vice Chancellor of RGUKT Basar is Prof. A. Govardhan.

PROFILE:
- B.E.(CSE) from Osmania University, Hyderabad
- M.Tech(CS) from Jawaharlal Nehru University (JNU), New Delhi
- Ph.D(CSE) from JNTU, Hyderabad
- PGDL(Leadership) from EMERITUS, Singapore
- Senior Professor of Computer Science & Engineering
- 30 years of Teaching and Research experience
- 555+ research papers published in International/National Journals/Conferences
- Guided 103 Ph.D theses and 140 M.Tech projects
- 5333 Google Scholar citations with h-index 31

ROLE AND RESPONSIBILITIES:
The Vice Chancellor is the chief academic and administrative officer of the university. Responsibilities include:
- Overall administration and governance of the university
- Chairing academic council and other statutory bodies
- Implementing academic policies and reforms
- Overseeing examinations, admissions, and research activities
- Representing the university at national and international forums
- Ensuring quality education and institutional development

Previous positions held include: Rector at JNTU Hyderabad, Registrar I/c, Principal at JNTUH CEH, Director of School of Information Technology, Director of Evaluation, and various other leadership roles.

Contact: vc@rgukt.ac.in | Phone: 08752-255111""",

    "grading_system": """Grading System at RGUKT Basar:

The grading system at RGUKT follows a comprehensive evaluation framework as per the Academic Regulations Handbook.

KEY COMPONENTS:
- The academic performance of students is evaluated through a combination of continuous internal assessment and semester-end examinations
- Grades are awarded based on the student's performance in theory courses, laboratory work, and project work
- The grading system uses letter grades with corresponding grade points to calculate the Semester Grade Point Average (SGPA) and Cumulative Grade Point Average (CGPA)

GRADING SCALE:
- O (Outstanding): 10 grade points
- A+ (Excellent): 9 grade points
- A (Very Good): 8 grade points
- B+ (Good): 7 grade points
- B (Above Average): 6 grade points
- C (Average): 5 grade points
- D (Pass): 4 grade points
- F (Fail): 0 grade points
- Ab (Absent): 0 grade points

AWARD OF DIVISION:
- First Class with Distinction: CGPA >= 8.0
- First Class: CGPA >= 6.5
- Second Class: CGPA >= 5.0
- Pass Class: CGPA >= 4.0

The minimum passing grade in each subject is D (4 grade points). Students who fail (F grade) must appear for remedial examinations or re-register for the course in the subsequent semester.""",

    "tech_fest": """Tech Fest and Cultural Events at RGUKT Basar:

RGUKT Basar encourages students to participate in various technical, cultural, and extracurricular activities to ensure a well-rounded education.

TECHNICAL EVENTS AND CLUBS:
- Students participate in national-level technical competitions and hackathons
- Projects like Garuda (drone/aviation projects), BAJA (all-terrain vehicle design), and SAE India competitions
- E-Cell (Entrepreneurship Cell) for fostering innovation and startup culture
- Various departmental technical clubs and societies

CULTURAL AND SOCIAL ACTIVITIES:
- Cultural and Social Activity Club organizes events throughout the year
- Students are encouraged to get involved in arts, music, drama, debate, and paintings
- Soft skills and edutainment sessions held from 7:30 PM to 10:30 PM
- Inter-campus competitions are held regularly
- NSS (National Service Scheme) activities for community service

CAMPUS LIFE:
- Daily academic program: 4 periods from 8 AM to 4 PM with lunch break
- Physical fitness activities in the morning
- Sports in the evening (indoor games like caroms, chess; outdoor games like volleyball, basketball)
- Evening programs in soft skills, reading classics, and selected movie programs
- Students explore talents in art, drama, and music

The goal is to give students a well-rounded education beyond just Sciences and Engineering.""",

    "fee": """Tuition and Fees at RGUKT Basar (per annum):

TUITION FEE:
- For TS/AP students (2024-25): Rs.37,000/- per annum (includes Rs.1,000/- exam fee)
- Fee-reimbursement eligible students can apply for scholarship
- For Other State students / Global Category: Rs.1,37,000/- per annum
- For NRI / International students: Rs.3,01,000/- per annum

ADDITIONAL FEES (at time of admission):
- Registration fee: Rs.1,000/- (Rs.500/- for SC/ST)
- Refundable caution deposit: Rs.2,000/- (by all)
- Medical insurance: Rs.700/- approximately (first two years)

APPLICATION FEE:
- OC/BC (TS & AP): Rs.500/-
- SC/ST (TS & AP): Rs.450/-
- Other States / Global: Rs.1,500/-
- NRI: US $100.00

Note: Students eligible for fee-reimbursement per State Govt guidelines can apply. Scholarship eligible students (except Telangana) pay tuition fee upfront, refunded when scholarship is sanctioned.""",

    "scholarship": """Scholarships and Financial Aid at RGUKT Basar:
- Full tuition waiver for all admitted students (government-sponsored)
- Post Matric Scholarship (PMS) for SC/ST/OBC students provided by the state government
- National Scholarships through the National Scholarship Portal
- Merit-cum-Means scholarships for economically weaker students
- Fee reimbursement for eligible reserved category students
Students can apply through the Telangana State e-Pass portal and National Scholarship Portal.""",

    "document": """Documents required for admission at RGUKT Basar:
1. SSC (10th Class) or equivalent mark sheet and certificate
2. Transfer Certificate (TC) from previous institution
3. Caste Certificate (if applicable) issued by competent authority
4. Income Certificate (for fee concession purposes)
5. Aadhar Card of student and parent/guardian
6. Passport size photographs (4-6 copies)
7. Medical Certificate
8. Residence Certificate (for proof of local status)
9. Migration Certificate (if from other boards)
10. Birth Certificate (for age proof)
Note: Original documents must be produced at the time of admission for verification.""",

    "apply admission": """How to apply for admission at RGUKT Basar:
1. Admissions are based on the RGUKT Common Entrance Test (CET) or state-level entrance exams
2. Eligible students are the top 1% of students who passed X class (SSC) from rural Telangana schools
3. Applications are invited through the official RGUKT website (rgukt.ac.in) during the admission period
4. Fill the online application form with personal and academic details
5. Upload required documents (photograph, signature, certificates)
6. Pay the application fee online
7. Appear for counseling based on merit rank
8. Select preferred campus and branch during counseling
9. Report to the allotted campus with original documents for verification
For updates, visit https://www.rgukt.ac.in regularly.""",

    "placement": """Placements at RGUKT Basar:
- Managed by the Training and Placement Division
- Training programs include professional development (mock interviews, group discussions, pre-placement talks)
- Personality development programs covering communication skills, presentation skills, and career planning
- Multiple companies visit for campus recruitment each year
- Students receive training in resume writing, interview skills, and aptitude tests
- The placement cell maintains relationships with various industries and organizations""",

    "library": """Library Facilities at RGUKT Basar:
- Central library with a large collection of books, journals, and digital resources
- Separate reading rooms for students
- Digital library with e-journals and online resources
- Book borrowing facility for students
- Reference section with competitive exam materials""",

    "hostel": """Hostel Facilities at RGUKT Basar:
- 6 hostel blocks (3 for boys, 3 for girls) accommodating around 8000 students
- Each hostel has a caretaker
- Student welfare overseen by wardens and a Chief Warden
- Separate staff for boys and girls hostels
- Facilities include mess, common rooms, and 24/7 security""",

    "hospital": """Medical Facilities at RGUKT Basar:
- A full-fledged hospital on campus
- 24/7 medical assistance available
- Regular health check-up camps
- Ambulance service for emergencies
- Tied up with district hospital for specialized treatments""",

    "anti ragging": """Anti-Ragging Measures at RGUKT Basar:
- Strict anti-ragging policy as per UGC guidelines
- Anti-ragging committee and squad
- Toll-free anti-ragging helpline
- Strict disciplinary action against offenders
- Awareness programs conducted regularly""",
}

def get_faq_info(query: str) -> str:
    """Check if query matches any FAQ"""
    q = query.lower()
    
    # Check placements
    if any(w in q for w in ["placement", "job", "career", "recruitment", "company"]):
        if not any(w in q for w in ["fee", "pay", "salary"]):
            return RGUKT_FAQ["placement"]
    
    # Check fees
    if any(w in q for w in ["fee", "fees", "tuition", "payment", "cost", "money", "expensive"]):
        return RGUKT_FAQ["fee"]
    
    # Check scholarships
    if any(w in q for w in ["scholarship", "financial aid", "free", "concession", "financial assistance"]):
        return RGUKT_FAQ["scholarship"]
    
    # Check documents
    if any(w in q for w in ["document", "document required", "certificate", "need to bring"]):
        return RGUKT_FAQ["document"]
    
    # Check admission/apply
    if any(w in q for w in ["apply for", "admission", "how to join", "how to get admission", "application", "counseling"]):
        return RGUKT_FAQ["apply admission"]
    
    # Check library
    if any(w in q for w in ["library", "book"]):
        return RGUKT_FAQ["library"]
    
    # Check hostel (use word boundary to avoid matching "hostel" inside other words)
    if re.search(r'\bhostel', q):
        return RGUKT_FAQ["hostel"]
    
    # Check medical
    if any(w in q for w in ["hospital", "medical", "health", "clinic", "doctor"]):
        return RGUKT_FAQ["hospital"]
    
    # Check anti-ragging
    if any(w in q for w in ["ragging", "ragging"]):
        return RGUKT_FAQ["anti ragging"]
    
    # Check B.Tech eligibility criteria
    if any(w in q for w in ["eligibility", "eligibility criteria", "requirements for b.tech", "b.tech eligibility", "btech eligibility", "b tech eligibility"]):
        return RGUKT_FAQ["eligibility_bt"]
    
    # Check about RGUKT
    if any(w in q for w in ["about rgukt", "about university", "tell me about rgukt", "what is rgukt", "rgukt information", "rgukt basar", "history of rgukt"]):
        return RGUKT_FAQ["about_rgukt"]
    
    # Check VC role
    if any(w in q for w in ["vice chancellor", "vc role", "role of vc", "role of vice chancellor", "who is vc", "who is the vice chancellor", "vice chancellor name"]):
        return RGUKT_FAQ["vc_role"]
    
    # Check grading system
    if any(w in q for w in ["grading", "grade", "grading system", "cgpa", "sgpa", "grade point", "how grading works", "how does grading", "award of division", "grade scale"]):
        return RGUKT_FAQ["grading_system"]
    
    # Check tech fest / cultural events
    if any(w in q for w in ["tech fest", "techfest", "cultural", "fest", "event", "extracurricular", "club", "hackathon", "garuda", "baja", "sae", "competition", "nss", "edutainment", "soft skills"]):
        return RGUKT_FAQ["tech_fest"]
    
    return None

# --- HOD Lookup Table ---
HOD_TABLE = {
    "physics": "Dr. G Devaraju", "chemical engineering": "Sirisala Vinay Kumar",
    "mechanical engineering": "Abbadi Charan Reddy", "civil engineering": "Shaik Khaleel",
    "computer science and engineering": "B Venkat Raman", "electrical engineering": "BHUKYA BHAVSINGH",
    "electronics & communications engineering": "Bathina Upenderrao",
    "metallurgical and materials engineering": "Kiran Kumar Atyam",
    "chemistry": "Dr. B. Srinivas", "mathematics": "Suresh Devanapalli",
    "telugu": "Dr. M.Rama Devi", "english": "A.Vijay Kumar",
    "bio-sciences": "Dr.A. Sai Krishna", "school of management": "Dr. Tirthala Naga Sai Kumar",
    "information technology": "B. Thilak", "cse": "B Venkat Raman",
    "ece": "Bathina Upenderrao", "eee": "BHUKYA BHAVSINGH",
    "me": "Abbadi Charan Reddy", "che": "Sirisala Vinay Kumar",
    "ce": "Shaik Khaleel", "mme": "Kiran Kumar Atyam",
}

def get_hod_info(query: str) -> str:
    """Check if query asks about an HOD"""
    q = query.lower()
    
    if not any(w in q for w in ["hod", "head of department", "head of the department", "who is the head"]):
        return None
    
    # Check if asking about responsibilities/role
    asking_about_role = any(w in q for w in ["role of", "duties of", "responsibilities of", "what does", "function", "responsibilities"])
    
    for dept_key, hod_name in HOD_TABLE.items():
        if len(dept_key) <= 3:
            if re.search(r'\b' + re.escape(dept_key) + r'\b', q):
                if asking_about_role:
                    return f"The Head of the {dept_key.title()} Department at RGUKT Basar is {hod_name}. As HOD, they are responsible for overseeing academic and administrative activities of the department, managing faculty, guiding students, and ensuring smooth department operations."
                else:
                    return f"The Head of the {dept_key.title()} Department at RGUKT Basar is {hod_name}."
        elif dept_key in q:
            if asking_about_role:
                return f"The Head of the {dept_key.title()} Department at RGUKT Basar is {hod_name}. As HOD, they are responsible for overseeing academic and administrative activities of the department, managing faculty, guiding students, and ensuring smooth department operations."
            else:
                return f"The Head of the {dept_key.title()} Department at RGUKT Basar is {hod_name}."
    
    if any(w in q for w in ["all", "list", "every"]):
        result = "Heads of Departments at RGUKT Basar:\n"
        for dept, name in sorted(HOD_TABLE.items()):
            if dept not in ["cse", "ece", "eee", "me", "che", "ce", "mme"]:
                result += f"- {name} → {dept.title()}\n"
        return result.strip()
    return None

# --- Website Scraper ---
RGUKT_URLS = {
    "home": "https://www.rgukt.ac.in/index.html",
    "about": "https://www.rgukt.ac.in/about-introduction.html",
    "about_rgukt": "https://www.rgukt.ac.in/about-rgukt.html",
    "vision": "https://www.rgukt.ac.in/vision-mission.html",
    "awards": "https://www.rgukt.ac.in/awards.html",
    "vc": "https://www.rgukt.ac.in/vc.html",
    "vc_succession": "https://www.rgukt.ac.in/vc-succession.html",
    "gc": "https://www.rgukt.ac.in/gc.html",
    "director": "https://www.rgukt.ac.in/director.html",
    "administration": "https://www.rgukt.ac.in/administration-section.html",
    "cd": "https://www.rgukt.ac.in/cd.html",
    "deans_and_hods": "https://www.rgukt.ac.in/deans-and-hods.html",
    "contact": "https://www.rgukt.ac.in/contactus.html",
    "academics": "https://www.rgukt.ac.in/academicprogrammes.html",
    "curricula": "https://www.rgukt.ac.in/curricula.html",
    "calendar": "https://www.rgukt.ac.in/academiccalender.html",
    "departments": "https://www.rgukt.ac.in/departments.html",
    "exams": "https://www.rgukt.ac.in/examination.html",
    "time_table": "https://www.rgukt.ac.in/time-table.html",
    # --- CSE ---
    "cse": "https://www.rgukt.ac.in/cse.html",
    "cse_curriculum": "https://www.rgukt.ac.in/cse-Curriculum.html",
    "cse_faculty": "https://www.rgukt.ac.in/cse-faculty.html",
    "cse_staff": "https://www.rgukt.ac.in/cse-staff.html",
    "cse_labmanual": "https://www.rgukt.ac.in/cse-labmanual.html",
    # --- ECE ---
    "ece": "https://www.rgukt.ac.in/ece.html",
    "ece_curriculum": "https://www.rgukt.ac.in/ece-Curriculum.html",
    "ece_faculty": "https://www.rgukt.ac.in/ece-faculty.html",
    "ece_staff": "https://www.rgukt.ac.in/ece-staff.html",
    "ece_labmanual": "https://www.rgukt.ac.in/ece-labmanual.html",
    # --- ME ---
    "me": "https://www.rgukt.ac.in/me.html",
    "me_curriculum": "https://www.rgukt.ac.in/me-Curriculum.html",
    "me_faculty": "https://www.rgukt.ac.in/me-faculty.html",
    "me_staff": "https://www.rgukt.ac.in/me-staff.html",
    "me_labmanual": "https://www.rgukt.ac.in/me-labmanual.html",
    # --- CHE ---
    "che": "https://www.rgukt.ac.in/che.html",
    "che_curriculum": "https://www.rgukt.ac.in/che-Curriculum.html",
    "che_faculty": "https://www.rgukt.ac.in/che-faculty.html",
    "che_staff": "https://www.rgukt.ac.in/che-staff.html",
    "che_labmanual": "https://www.rgukt.ac.in/che-labmanual.html",
    # --- CE (Civil) ---
    "civil": "https://www.rgukt.ac.in/ce.html",
    "civil_curriculum": "https://www.rgukt.ac.in/ce-Curriculum.html",
    "civil_faculty": "https://www.rgukt.ac.in/civil-faculty.html",
    "civil_staff": "https://www.rgukt.ac.in/ce-staff.html",
    "civil_labmanual": "https://www.rgukt.ac.in/ce-labmanual.html",
    # --- MME ---
    "mme": "https://www.rgukt.ac.in/mme.html",
    "mme_curriculum": "https://www.rgukt.ac.in/mme-Curriculum.html",
    "mme_faculty": "https://www.rgukt.ac.in/mme-faculty.html",
    "mme_staff": "https://www.rgukt.ac.in/mme-staff.html",
    "mme_labmanual": "https://www.rgukt.ac.in/mme-labmanual.html",
    # --- EEE ---
    "eee": "https://www.rgukt.ac.in/eee.html",
    "eee_curriculum": "https://www.rgukt.ac.in/eee-Curriculum.html",
    "eee_faculty": "https://www.rgukt.ac.in/eee-faculty.html",
    "eee_staff": "https://www.rgukt.ac.in/eee-staff.html",
    "eee_labmanual": "https://www.rgukt.ac.in/eee-labmanual.html",
    # --- Bio Sciences ---
    "bio_sciences": "https://www.rgukt.ac.in/bio-sciences.html",
    "bio_sciences_curriculum": "https://www.rgukt.ac.in/bio-sciences-Curriculum.html",
    "bio_sciences_faculty": "https://www.rgukt.ac.in/bio-sciences-faculty.html",
    "bio_sciences_staff": "https://www.rgukt.ac.in/bio-sciences-staff.html",
    "bio_sciences_labmanual": "https://www.rgukt.ac.in/bio-sciences-labmanual.html",
    # --- Chemistry ---
    "chemistry": "https://www.rgukt.ac.in/chemistry.html",
    "chemistry_curriculum": "https://www.rgukt.ac.in/chemistry-Curriculum.html",
    "chemistry_faculty": "https://www.rgukt.ac.in/chemistry-faculty.html",
    "chemistry_staff": "https://www.rgukt.ac.in/chemistry-staff.html",
    "chemistry_labmanual": "https://www.rgukt.ac.in/chemistry-labmanual.html",
    # --- HSS ---
    "hss": "https://www.rgukt.ac.in/hss.html",
    "hss_curriculum": "https://www.rgukt.ac.in/hss-Curriculum.html",
    "hss_faculty": "https://www.rgukt.ac.in/hss-faculty.html",
    "hss_staff": "https://www.rgukt.ac.in/hss-staff.html",
    "hss_labmanual": "https://www.rgukt.ac.in/hss-labmanual.html",
    # --- Maths ---
    "maths": "https://www.rgukt.ac.in/maths.html",
    "maths_curriculum": "https://www.rgukt.ac.in/maths-Curriculum.html",
    "maths_faculty": "https://www.rgukt.ac.in/maths-faculty.html",
    "maths_staff": "https://www.rgukt.ac.in/maths-staff.html",
    "maths_labmanual": "https://www.rgukt.ac.in/maths-labmanual.html",
    # --- Physics ---
    "physics": "https://www.rgukt.ac.in/physics.html",
    "physics_curriculum": "https://www.rgukt.ac.in/physics-Curriculum.html",
    "physics_faculty": "https://www.rgukt.ac.in/physics-faculty.html",
    "physics_staff": "https://www.rgukt.ac.in/physics-staff.html",
    "physics_labmanual": "https://www.rgukt.ac.in/physics-labmanual.html",
    # --- Management ---
    "management": "https://www.rgukt.ac.in/schoolmng.html",
    "management_curriculum": "https://www.rgukt.ac.in/schoolmng-Curriculum.html",
    "management_faculty": "https://www.rgukt.ac.in/schoolmng-faculty.html",
    "management_staff": "https://www.rgukt.ac.in/schoolmng-staff.html",
    "management_labmanual": "https://www.rgukt.ac.in/schoolmng-labmanual.html",
    # --- Library ---
    "library": "https://www.rgukt.ac.in/library/index.html",
    "library_objectives": "https://www.rgukt.ac.in/library/objectives.html",
    "library_services": "https://www.rgukt.ac.in/library/services.html",
    "library_rules": "https://www.rgukt.ac.in/library/rules.html",
    "library_enhancements": "https://www.rgukt.ac.in/library/enhancements.html",
    "library_periodicals": "https://www.rgukt.ac.in/library/periodicals.html",
    "library_digital": "https://www.rgukt.ac.in/library/digital-library.html",
    "library_staff": "https://www.rgukt.ac.in/library/staff.html",
    "library_contact": "https://www.rgukt.ac.in/library/contact.html",
    # --- Placements & Facilities ---
    "placement": "https://www.rgukt.ac.in/placement/index.html",
    "placement_gallery": "https://www.rgukt.ac.in/placement/scroll_gallery.html",
    "hostels": "https://www.rgukt.ac.in/hostels.html",
    "counseling": "https://www.rgukt.ac.in/counseling.html",
    "hospital": "https://www.rgukt.ac.in/hospital.html",
    "shopping": "https://www.rgukt.ac.in/shopping-complex.html",
    # --- Student Life ---
    "student_life": "https://www.rgukt.ac.in/stu-campuslife.html",
    "student_education": "https://www.rgukt.ac.in/stu-edurgukt.html",
    "alumni": "https://www.rgukt.ac.in/alumni.html",
    "admissions": "https://www.rgukt.ac.in/admissions2026.html",
    "anti_ragging": "https://www.rgukt.ac.in/anti-ragging.html",
    # --- Initiatives & R&D ---
    "e_cell": "https://www.rgukt.ac.in/e-cell.html",
    "swayam": "https://www.rgukt.ac.in/swayam-nptel.html",
    "rd": "https://www.rgukt.ac.in/rd.html",
    "iqac": "https://www.rgukt.ac.in/iqac.html",
    "rd_facilities": "https://www.rgukt.ac.in/rd-facilities.html",
    "rd_guest_lectures": "https://www.rgukt.ac.in/rd-guest-lectures.html",
    "rd_publications": "https://www.rgukt.ac.in/rd-publications.html",
    "rd_outreach": "https://www.rgukt.ac.in/rd-outreach.html",
    "rd_consultancy": "https://www.rgukt.ac.in/rd-consultancy-charges.html",
    "rd_news": "https://www.rgukt.ac.in/rd-news-updates.html",
    # --- Committees ---
    "grievance": "https://www.rgukt.ac.in/grievance.html",
    "cgc": "https://www.rgukt.ac.in/cgc.html",
    "pdc": "https://www.rgukt.ac.in/pdc.html",
    "cbc": "https://www.rgukt.ac.in/cbc.html",
    "cultural_club": "https://www.rgukt.ac.in/Cultural-Social-Activity-Club.html",
    "scst_cell": "https://www.rgukt.ac.in/sc-st-cell.html",
    "uic": "https://www.rgukt.ac.in/uic.html",
    # --- Info ---
    "gallery": "https://www.rgukt.ac.in/gallery-album.html",
    "rti": "https://www.rgukt.ac.in/rti.html",
    "notices": "https://www.rgukt.ac.in/notices-downloads.html",
    "tenders": "https://www.rgukt.ac.in/tenders.html",
    "terms": "https://www.rgukt.ac.in/term-of-use.html",
    "disclaimer": "https://www.rgukt.ac.in/disclaimer.html",
}

def scrape_url(url, max_lines=500):
    """Scrape a URL and return clean text content"""
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.content, 'html.parser')
        for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        body = soup.find('body') or soup
        text = body.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines[:max_lines])
    except Exception as e:
        logger.warning(f"Error scraping {url}: {e}")
        return ""

def find_relevant_urls(query):
    """Determine which URLs to scrape based on query"""
    q = query.lower()
    urls = []
    if any(w in q for w in ["faculty", "professor", "teacher", "staff", "hod", "head of", "lecturer"]):
        if "cse" in q or "computer science" in q: urls.append(RGUKT_URLS["cse_faculty"])
        if "ece" in q or "electronics" in q or "communication" in q: urls.append(RGUKT_URLS["ece_faculty"])
        if "mechanical" in q or "me" in q.split(): urls.append(RGUKT_URLS["me_faculty"])
        if "chemical" in q or "che" in q.split(): urls.append(RGUKT_URLS["che_faculty"])
        if "civil" in q or "ce" in q.split(): urls.append(RGUKT_URLS["civil_faculty"])
        if "mme" in q or "metallurgy" in q: urls.append(RGUKT_URLS["mme_faculty"])
        if not urls: urls = [v for k, v in RGUKT_URLS.items() if 'faculty' in k]
    if any(w in q for w in ["department", "branch", "cse", "ece", "mechanical", "chemical", "civil", "mme", "b.tech", "btech"]):
        urls.append(RGUKT_URLS["departments"])
        is_general = any(w in q for w in ["all", "list", "available", "offer", "what are", "what is"])
        if not is_general:
            for key in ["cse", "ece", "me", "che", "civil", "mme"]:
                if key in q or (key == "me" and "mechanical" in q):
                    dept_key = key
                    if key == "me" and "mechanical" in q: dept_key = "me"
                    if dept_key in RGUKT_URLS: urls.append(RGUKT_URLS[dept_key])
    if any(w in q for w in ["academic", "program", "course", "curriculum", "study", "admission", "syllabus"]):
        urls.extend([RGUKT_URLS["academics"], RGUKT_URLS["curricula"]])
    if any(w in q for w in ["exam", "test", "result", "grade", "time table", "timetable"]):
        urls.extend([RGUKT_URLS["exams"], RGUKT_URLS["time_table"]])
    if any(w in q for w in ["about", "history", "mission", "vision", "tell me about rgukt", "what is rgukt"]):
        urls.extend([RGUKT_URLS["about"], RGUKT_URLS["about_rgukt"], RGUKT_URLS["vision"]])
    if any(w in q for w in ["vice chancellor", "vc", "chancellor", "director", "governing", "administration", "administrative", "officer", "registrar", "dean", "ao "]):
        urls.extend([RGUKT_URLS["vc"], RGUKT_URLS["gc"], RGUKT_URLS["contact"], RGUKT_URLS["administration"]])
    if any(w in q for w in ["eligibility", "eligibility criteria", "requirements for b.tech", "b.tech eligibility", "btech eligibility"]):
        urls.extend([RGUKT_URLS["admissions"], RGUKT_URLS["academics"]])
    if any(w in q for w in ["grading", "grade", "grading system", "cgpa", "sgpa", "grade point", "award of division"]):
        urls.extend([RGUKT_URLS["exams"], RGUKT_URLS["academics"]])
    if any(w in q for w in ["tech fest", "techfest", "cultural", "fest", "extracurricular", "club", "hackathon", "edutainment"]):
        urls.extend([RGUKT_URLS["student_life"], RGUKT_URLS["cultural_club"], RGUKT_URLS["e_cell"]])
    if any(w in q for w in ["hostel", "accommodation", "warden", "chief warden", "outpass", "leave", "mess", "dining"]):
        urls.extend([RGUKT_URLS["hostels"], RGUKT_URLS["anti_ragging"]])
    if any(w in q for w in ["library", "book", "books"]): urls.append(RGUKT_URLS["library"])
    if any(w in q for w in ["hospital", "medical", "health", "clinic", "infirmary"]): urls.append(RGUKT_URLS["hospital"])
    if any(w in q for w in ["placement", "job", "career", "recruitment", "company", "internship"]): urls.append(RGUKT_URLS["placement"])
    if any(w in q for w in ["contact", "address", "phone", "email", "reach", "call"]): urls.append(RGUKT_URLS["contact"])
    if any(w in q for w in ["student life", "campus life", "ragging", "club", "activity", "student", "event", "project", "garuda", "baja", "saeindia", "competition"]):
        urls.extend([RGUKT_URLS["home"], RGUKT_URLS["student_life"], RGUKT_URLS["anti_ragging"]])
    if any(w in q for w in ["calendar", "schedule", "semester", "holiday", "vacation"]): urls.append(RGUKT_URLS["calendar"])
    # --- LABORATORY queries ---
    if any(w in q for w in ["lab", "laboratory", "labmanual", "practical"]):
        # Add lab manual pages for the relevant department
        if "cse" in q or "computer science" in q:
            urls.append(RGUKT_URLS.get("cse_labmanual", ""))
        if "ece" in q or "electronics" in q or "communication" in q:
            urls.append(RGUKT_URLS.get("ece_labmanual", ""))
        if "mechanical" in q or "me" in q.split():
            urls.append(RGUKT_URLS.get("me_labmanual", ""))
        if "chemical" in q or "che" in q.split():
            urls.append(RGUKT_URLS.get("che_labmanual", ""))
        if "civil" in q or "ce" in q.split():
            urls.append(RGUKT_URLS.get("civil_labmanual", ""))
        if "mme" in q or "metallurgy" in q:
            urls.append(RGUKT_URLS.get("mme_labmanual", ""))
        if "eee" in q or "electrical" in q:
            urls.append(RGUKT_URLS.get("eee_labmanual", ""))
        if "bio" in q or "biology" in q or "life science" in q:
            urls.append(RGUKT_URLS.get("bio_sciences_labmanual", ""))
        if "chemist" in q:
            urls.append(RGUKT_URLS.get("chemistry_labmanual", ""))
        if "physic" in q:
            urls.append(RGUKT_URLS.get("physics_labmanual", ""))
        if "math" in q:
            urls.append(RGUKT_URLS.get("maths_labmanual", ""))
        if "management" in q or "mba" in q or "school of management" in q:
            urls.append(RGUKT_URLS.get("management_labmanual", ""))
        # If no specific department matched, add all lab manuals
        if not any(x in q for x in ["cse","ece","mechanical","chemical","civil","mme","eee","bio","chemist","physic","math","management"]):
            for key, url in RGUKT_URLS.items():
                if "labmanual" in key:
                    urls.append(url)
    if RGUKT_URLS["home"] not in urls: urls.append(RGUKT_URLS["home"])
    if len(urls) <= 1:
        urls.extend([RGUKT_URLS["about"], RGUKT_URLS["academics"], RGUKT_URLS["contact"],
                     RGUKT_URLS["departments"], RGUKT_URLS["student_life"],
                     RGUKT_URLS["hostels"], RGUKT_URLS["vc"]])
    seen = set()
    return [x for x in urls if not (x in seen or seen.add(x))]

def resolve_followup_question(current_query: str, chat_history: List[Dict[str, str]]) -> str:
    """If current query is a follow-up (his/her/their), expand it using previous answer"""
    if not chat_history:
        return current_query
    
    q = current_query.lower()
    # Check if it's a follow-up question
    is_followup = any(p in q for p in ["his ", "her ", "their ", "him ", "he ", "she "])
    if not is_followup:
        return current_query
    
    # Find last assistant message
    last_assistant_msg = None
    for msg in reversed(chat_history):
        if msg.get("role") == "assistant":
            last_assistant_msg = msg.get("content", "")
            break
    
    if not last_assistant_msg:
        return current_query
    
    # Clean HTML from last response
    last_answer = strip_raw_html(last_assistant_msg)
    
    # Extract the subject from the previous answer
    # Look for patterns like "The CSE HOD is..." or "Dr. X is..."
    subject = None
    
    # Try to find a person name in the last answer
    name_patterns = [
        r"(?:is|are)\s+(Dr\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"(?:is|are)\s+(Prof\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"(?:is|are)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
    ]
    for pattern in name_patterns:
        m = re.search(pattern, last_answer)
        if m:
            subject = m.group(1).strip()
            break
    
    # If no name found, try to find the topic
    if not subject:
        # Look for department mentions
        dept_match = re.search(r"(Computer Science|Electronics|Mechanical|Civil|Chemical|Metallurgical|Electrical)", last_answer, re.IGNORECASE)
        if dept_match:
            subject = f"the {dept_match.group(1)} department"
        else:
            # Just use the last user question as context
            for msg in reversed(chat_history):
                if msg.get("role") == "user":
                    subject = msg.get("content", "").replace("?", "").strip()
                    break
    
    if subject:
        # Rewrite the follow-up question
        expanded = f"{current_query} (referring to {subject})"
        return expanded
    
    return current_query

def build_conversation_context(chat_history):
    if not chat_history: return ""
    recent = chat_history[-6:]
    lines = []
    for msg in recent:
        if "role" in msg:
            role = "User" if msg.get("role") == "user" else "Assistant"
            text = msg.get("content", "")
        else:
            role = "User" if msg.get("type") == "user" else "Assistant"
            text = msg.get("text", "")
        if role == "Assistant":
            text = strip_raw_html(text)
            if len(text) > 500: text = text[:500] + "..."
        lines.append(f"{role}: {text}")
    return "\n".join(lines)

# --- Pydantic Models ---
class ChatMessage(BaseModel):
    text: str
    chat_history: List[Dict[str, str]] = []

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    chat_history: List[Dict[str, str]]

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing RGUKT ChatBot API...")
    try:
        get_embeddings()
        get_vector_store()
        get_retriever()
        # Test LLM availability
        test = call_llm("say ok")
        if test:
            logger.info("LLM model ready")
        else:
            logger.warning("No LLM model available (Gemini + Groq both unavailable)")
        logger.info("All components initialized successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

def strip_raw_html(text):
    text = re.sub(r'```html\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = re.sub(r'<!DOCTYPE[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</?html[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</?head[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</?body[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<meta[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<title[^>]*>.*?</title>', '', text, flags=re.IGNORECASE|re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE|re.DOTALL)
    text = re.sub(r'\s+style="[^"]*"', '', text)
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    return text.strip()

def format_text(text):
    while '**' in text:
        text = text.replace('**', '<strong>', 1)
        text = text.replace('**', '</strong>', 1)
    return text

def format_response(raw_response, topic, styles):
    cleaned = strip_raw_html(raw_response)
    html = f"""
    <div style="{styles['container']}">
        <h1 style="{styles['main_title']}">{topic}</h1>
        <div style="{styles['overview_section']}">
    """
    lines = cleaned.split('\n')
    in_list = False
    current_list = []
    for line in lines:
        line = line.strip()
        if not line: continue
        fline = format_text(line)
        if line.startswith('###'):
            if in_list:
                html += "<ul style='{0}'>".format(styles['list']) + "".join(current_list) + "</ul>"
                current_list = []
                in_list = False
            html += '<h3 style="{0}">{1}</h3>'.format(styles["subheading"], fline)
        elif line.startswith('##'):
            if in_list:
                html += "<ul style='{0}'>".format(styles['list']) + "".join(current_list) + "</ul>"
                current_list = []
                in_list = False
            html += '<h2 style="{0}">{1}</h2>'.format(styles["heading"], fline)
        elif line.startswith(('- ', '* ', '• ')):
            in_list = True
            current_list.append('<li style="{0}">{1}</li>'.format(styles["list_item"], fline[2:]))
        elif line.startswith(('1.', '2.', '3.')):
            in_list = True
            current_list.append('<li style="{0}">{1}</li>'.format(styles["list_item"], fline[2:]))
        else:
            if in_list:
                html += "<ul style='{0}'>".format(styles['list']) + "".join(current_list) + "</ul>"
                current_list = []
                in_list = False
            html += '<p style="{0}">{1}</p>'.format(styles["paragraph"], fline)
    if in_list:
        html += "<ul style='{0}'>".format(styles['list']) + "".join(current_list) + "</ul>"
    html += f"""
        </div>
        <div style="{styles['footer']}">
            <p>Source: RGUKT Official Information</p>
        </div>
    </div>
    """
    return html

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    try:
        logger.info(f"Received chat message: {message.text[:50]}...")
        try:
            updated_history = message.chat_history.copy() if message.chat_history else []
            updated_history.append({"role": "user", "content": message.text})
        except Exception:
            updated_history = [{"role": "user", "content": message.text}]

        styles = {
            'container': 'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; max-width: 800px; margin: 0 auto; line-height: 1.6;',
            'main_title': 'color: #000000; font-size: 28px; font-weight: 700; margin-bottom: 24px; padding-bottom: 12px; border-bottom: 1px solid #e0e0e0;',
            'heading': 'color: #000000; font-size: 22px; font-weight: 600; margin: 20px 0 12px 0; padding-bottom: 8px; border-bottom: 1px solid #e0e0e0;',
            'subheading': 'color: #000000; font-size: 18px; font-weight: 600; margin: 16px 0 8px 0;',
            'paragraph': 'color: #000000; margin: 12px 0; font-size: 16px; line-height: 1.6;',
            'list': 'margin: 12px 0 12px 24px; padding: 0;',
            'list_item': 'margin: 8px 0; color: #000000; font-size: 16px; line-height: 1.6;',
            'footer': 'margin-top: 24px; padding-top: 16px; border-top: 1px solid #e0e0e0; color: #000000; font-size: 14px;',
            'overview_section': 'background: #ffffff; border-radius: 8px; padding: 16px; margin: 16px 0;'
        }

        greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
        topic = message.text.strip('?').title()

        if message.text.lower().strip() in greetings:
            response = f"""
            <div style="{styles['container']}">
                <p style="{styles['paragraph']}">Hello! How can I assist you with RGUKT university-related queries?</p>
            </div>
            """
        else:
            # Resolve follow-up questions (e.g. "what is his name" -> "what is his name (referring to CSE HOD)")
            resolved_text = resolve_followup_question(message.text, message.chat_history)
            
            # Step 0: Check simple hardcoded lookups (departments list, HOD name)
            # These are pure factual lookups that don't need LLM
            dept_answer = get_departments_info(resolved_text)
            if dept_answer:
                raw_response = dept_answer
            elif get_hod_info(resolved_text):
                # HOD lookup handles both name and role questions
                raw_response = get_hod_info(resolved_text)
            else:
                raw_response = None

            if raw_response is None:
                # Step 1: Collect ALL sources - FAQ, Web scraping, RAG vector store
                conv_history = build_conversation_context(updated_history[:-1])

                # Get FAQ info (as supplementary context, not as final answer)
                faq_info = get_faq_info(resolved_text)
                
                # Scrape relevant web pages
                urls = find_relevant_urls(message.text)
                if not urls: urls = [RGUKT_URLS["about"], RGUKT_URLS["academics"]]

                scraped_content = []
                for url in urls:
                    content = scrape_url(url)
                    if content:
                        scraped_content.append(f"--- Source: {url} ---\n{content}")

                all_content = "\n\n".join(scraped_content)

                # Retrieve from PDF vector database (RAG)
                pdf_context = ""
                try:
                    retriever = get_retriever()
                    pdf_docs = retriever.invoke(resolved_text)
                    if pdf_docs:
                        pdf_context = "\n".join([d.page_content[:800] for d in pdf_docs[:5]])
                except Exception:
                    pass

                # Combine ALL sources
                info_sources = ""
                if pdf_context:
                    info_sources += f"\n\nRGUKT Document Database (from official PDFs):\n{pdf_context}"
                if faq_info:
                    info_sources += f"\n\nRGUKT FAQ Information:\n{faq_info}"
                if all_content:
                    info_sources += f"\n\nRGUKT Website Content:\n{all_content}"

                if info_sources:
                    # Limit context size to avoid 413 errors
                    max_context = 6000
                    truncated_sources = info_sources[:max_context]
                    if len(info_sources) > max_context:
                        truncated_sources += "\n\n[Content truncated due to length...]"
                    
                    prompt = f"""You are an assistant for RGUKT (Rajiv Gandhi University of Knowledge Technologies), Basar campus.

CONVERSATION HISTORY:
{conv_history}

Answer the user's question using ALL the information provided below. Check every source carefully.

Rules:
1. Answer concisely and directly based on the available information from ALL sources.
2. If the information doesn't contain the answer, say "I don't have this information available in the RGUKT database."
3. NEVER make up names, dates, or facts.
4. Do not mention "scraped web content", "PDF", "FAQ", or "documents" in your answer - just answer naturally.

Information from all sources:
{truncated_sources}

User's Question: {resolved_text}

Answer:"""
                    raw_response = call_llm(prompt)

                    # Show which sources contributed to the answer (debug visibility request)
                    sources_used = []
                    if faq_info:
                        sources_used.append("RGUKT FAQ")
                    if pdf_context:
                        sources_used.append("Academic Regulations PDF")
                    if all_content:
                        sources_used.append("RGUKT website pages")
                    if sources_used:
                        raw_response = (raw_response or "") + "\n\nSources used: " + ", ".join(sources_used)

                    if not raw_response:
                        # If LLM unavailable, try extract answer directly from context
                        name_match = re.search(r"(?:is|are)\s+((?:Dr\.|Prof\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", truncated_sources, re.IGNORECASE)
                        if name_match:
                            raw_response = f"The person referred to is {name_match.group(1)}."
                        else:
                            raw_response = "I'm sorry, I couldn't process your request at this time. The AI models are currently unavailable due to rate limits. The question was interpreted as: " + resolved_text
                else:
                    raw_response = "I couldn't find any relevant information on the official RGUKT website for your query."

            response = format_response(raw_response, topic, styles)

        try:
            updated_history.append({"role": "assistant", "content": response})
        except Exception:
            pass

        logger.info("Chat response generated successfully")
        return ChatResponse(response=response, timestamp=datetime.now().isoformat(), chat_history=updated_history)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/clear-history", response_model=ChatResponse)
async def clear_history():
    return ChatResponse(response="Chat history cleared", timestamp=datetime.now().isoformat(), chat_history=[])

@app.get("/")
async def read_root():
    return {"message": "RGUKT ChatBot API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    try:
        get_embeddings()
        get_vector_store()
        get_retriever()
        return {"status": "healthy", "components": "all initialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")