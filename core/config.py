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
    
    def __init__(self):
        """Initialize configuration by reading current environment variables"""
        # AI Provider Configuration
        self.AI_PROVIDER: str = os.getenv("AI_PROVIDER", "openai")
        
        # OpenAI Configuration
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        self.OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "4000"))
        
        # Anthropic Configuration
        self.ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
        self.ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        self.ANTHROPIC_MAX_TOKENS: int = int(os.getenv("ANTHROPIC_MAX_TOKENS", "4096"))
        
        # API Configuration
        self.API_TITLE: str = "Financial Statement Transcription API"
        self.API_VERSION: str = "1.0.0"
        self.API_DESCRIPTION: str = "AI-powered financial data extraction from PDF documents and images"
        
        # File Processing Configuration
        self.MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "52428800"))  # 50MB
        self.SUPPORTED_FILE_TYPES: list = [".pdf", ".png", ".jpg", ".jpeg"]
        
        # Processing Configuration
        self.MAX_PAGES_TO_PROCESS: int = int(os.getenv("MAX_PAGES_TO_PROCESS", "100"))  # Allow up to 100 pages
        self.PARALLEL_WORKERS: int = int(os.getenv("PARALLEL_WORKERS", "5"))
        self.PROCESSING_TIMEOUT: int = int(os.getenv("PROCESSING_TIMEOUT", "900"))  # 15 minutes
        
        # Rate Limiting
        self.RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        self.RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
        
        # Logging
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    def validate(self) -> bool:
        """Validate that required configuration is present"""
        if self.AI_PROVIDER == "openai":
            if not self.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY environment variable is required when AI_PROVIDER is 'openai'")
        elif self.AI_PROVIDER == "anthropic":
            if not self.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY environment variable is required when AI_PROVIDER is 'anthropic'")
        else:
            raise ValueError(f"Invalid AI_PROVIDER: {self.AI_PROVIDER}. Must be 'openai' or 'anthropic'")
        return True
