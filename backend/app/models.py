from pydantic import BaseModel
from typing import Optional, List

class ChatMessage(BaseModel):
    user_message: str
    bot_response: str
    timestamp: str

class ChatHistory(BaseModel):
    messages: List[ChatMessage]
    session_id: str 