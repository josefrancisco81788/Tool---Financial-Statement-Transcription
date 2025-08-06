import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    app_name: str = "Financial Statement Transcription API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # File Processing
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    sync_file_size_limit: int = 5 * 1024 * 1024  # 5MB
    allowed_file_types: list = [".pdf", ".jpg", ".jpeg", ".png"]
    
    # OpenAI Settings
    openai_api_key: Optional[str] = None
    
    # Database Settings
    database_url: str = "sqlite:///./financial_statements.db"
    
    # Processing Settings
    default_processing_approach: str = "auto"
    default_output_format: str = "csv"
    
    # Job Management
    job_timeout: int = 300  # 5 minutes
    max_concurrent_jobs: int = 5
    
    # Security
    cors_origins: list = ["*"]  # Configure for production
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load OpenAI API key from environment
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

settings = Settings() 