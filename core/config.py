"""
Configuration module for Financial Statement Transcription API
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for the Financial Statement Transcription API"""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "4000"))
    
    # API Configuration
    API_TITLE: str = "Financial Statement Transcription API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "AI-powered financial data extraction from PDF documents and images"
    
    # File Processing Configuration
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "52428800"))  # 50MB
    SUPPORTED_FILE_TYPES: list = [".pdf", ".png", ".jpg", ".jpeg"]
    
    # Processing Configuration
    MAX_PAGES_TO_PROCESS: int = int(os.getenv("MAX_PAGES_TO_PROCESS", "100"))  # Allow up to 100 pages
    PARALLEL_WORKERS: int = int(os.getenv("PARALLEL_WORKERS", "5"))
    PROCESSING_TIMEOUT: int = int(os.getenv("PROCESSING_TIMEOUT", "900"))  # 15 minutes
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        return True
