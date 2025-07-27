from pydantic import BaseModel
from typing import Optional

class QuestionRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    session_id: str

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None 