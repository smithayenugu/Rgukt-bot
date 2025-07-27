#!/usr/bin/env python3
"""
Startup script for RGUKT ChatBot API
This script ensures proper initialization and runs the FastAPI server
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """Start the FastAPI server"""
    print("🚀 Starting RGUKT ChatBot API...")
    
    # Check if .env file exists
    env_file = current_dir / ".env"
    if not env_file.exists():
        print("⚠️  Warning: .env file not found. Please create one with your GROQ_API_KEY")
        print("   Example .env file:")
        print("   GROQ_API_KEY=your_groq_api_key_here")
    
    # Run the server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main() 