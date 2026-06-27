import uuid
from datetime import datetime
import json
from typing import Any

def generate_session_id() -> str:
    """Generate a unique session ID"""
    return str(uuid.uuid4())

def format_timestamp(dt: datetime) -> str:
    """Format datetime to string"""
    return dt.isoformat()

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    return text.strip()

def create_error_response(message: str, error_code: str = None) -> dict:
    """Create standardized error response"""
    return {
        "detail": message,
        "error_code": error_code,
        "timestamp": datetime.now().isoformat()
    }

def safe_json_serialize(obj: Any) -> str:
    """Safely serialize object to JSON string"""
    def default(o):
        if hasattr(o, '__dict__'):
            return o.__dict__
        return str(o)
    
    return json.dumps(obj, default=default) 