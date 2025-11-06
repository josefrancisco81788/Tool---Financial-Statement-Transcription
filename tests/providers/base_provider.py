"""
Base provider class for unified testing pipeline
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import time
import os
from datetime import datetime


@dataclass
class TestResult:
    """Enhanced result from a single test run with field-level data"""
    
    # Basic info
    provider: str
    document: str
    success: bool
    error: Optional[str] = None
    
    # Performance metrics
    processing_time: float = 0.0
    extraction_rate: float = 0.0
    format_accuracy: float = 0.0
    overall_score: float = 0.0
    
    # Field-level extraction data
    extracted_fields: Dict[str, Any] = field(default_factory=dict)
    template_fields: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
    field_accuracy: Dict[str, float] = field(default_factory=dict)
    
    # Additional metadata
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    api_calls_made: int = 0
    pages_processed: int = 0
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    
    # Legacy fields for backward compatibility
    error_message: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    csv_integration: Optional[float] = None
    
    # Production readiness
    production_ready: Optional[bool] = None
    production_issues: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.production_issues is None:
            self.production_issues = []


class BaseTestProvider(ABC):
    """Base class for all test providers"""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.config = None
        
        # Import utilities
        try:
            from utils.timeout_handler import timeout_handler
            from utils.error_handler import error_handler
            from utils.validation import validator
            self.timeout_handler = timeout_handler
            self.error_handler = error_handler
            self.validator = validator
        except ImportError:
            # Fallback if utilities not available
            self.timeout_handler = None
            self.error_handler = None
            self.validator = None
    
    @abstractmethod
    def validate_configuration(self) -> bool:
        """Validate provider configuration and health"""
        pass
    
    @abstractmethod
    def test_document(self, document_path: str, timeout: int = 300) -> TestResult:
        """Test a single document with this provider"""
        pass
    
    def set_config(self, config: Dict[str, Any]):
        """Set provider-specific configuration"""
        self.config = config
    
    def _create_test_result(self, document: str, success: bool, 
                          extracted_data: Optional[Dict] = None,
                          error_message: Optional[str] = None,
                          processing_time: float = 0.0,
                          extracted_fields: Optional[Dict[str, Any]] = None,
                          template_fields: Optional[List[str]] = None,
                          missing_fields: Optional[List[str]] = None,
                          field_accuracy: Optional[Dict[str, float]] = None,
                          confidence_scores: Optional[Dict[str, float]] = None,
                          api_calls_made: int = 0,
                          pages_processed: int = 0) -> TestResult:
        """Create an enhanced TestResult object"""
        return TestResult(
            provider=self.provider_name,
            document=document,
            success=success,
            error=error_message,
            processing_time=processing_time,
            extracted_data=extracted_data,  # Legacy field
            error_message=error_message,    # Legacy field
            extracted_fields=extracted_fields or {},
            template_fields=template_fields or [],
            missing_fields=missing_fields or [],
            field_accuracy=field_accuracy or {},
            confidence_scores=confidence_scores or {},
            api_calls_made=api_calls_made,
            pages_processed=pages_processed
        )
    
    def _set_environment_variable(self, provider: str):
        """Set AI_PROVIDER environment variable"""
        os.environ['AI_PROVIDER'] = provider
    
    def _get_document_name(self, document_path: str) -> str:
        """Extract document name from path"""
        return Path(document_path).name
