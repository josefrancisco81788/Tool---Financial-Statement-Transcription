"""
Input validation system for unified testing pipeline
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Result of validation operation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class ValidationSystem:
    """Validates inputs and configurations for testing pipeline"""
    
    def __init__(self):
        self.supported_providers = ["openai", "anthropic"]
        self.supported_document_sets = ["light", "origin"]
        self.supported_formats = [".pdf", ".png", ".jpg", ".jpeg"]
        self.max_file_size = 50 * 1024 * 1024  # 50MB
    
    def validate_provider(self, provider: str) -> ValidationResult:
        """Validate provider configuration"""
        errors = []
        warnings = []
        
        if provider not in self.supported_providers:
            errors.append(f"Unsupported provider: {provider}")
        
        # Check API key availability
        api_key_var = f"{provider.upper()}_API_KEY"
        if not os.getenv(api_key_var):
            errors.append(f"Missing {api_key_var} environment variable")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_document_path(self, document_path: str) -> ValidationResult:
        """Validate document file path"""
        errors = []
        warnings = []
        
        path = Path(document_path)
        
        if not path.exists():
            errors.append(f"Document file does not exist: {document_path}")
            return ValidationResult(False, errors, warnings)
        
        if not path.is_file():
            errors.append(f"Path is not a file: {document_path}")
        
        # Check file extension
        if path.suffix.lower() not in self.supported_formats:
            errors.append(f"Unsupported file format: {path.suffix}")
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > self.max_file_size:
            errors.append(f"File too large: {file_size / (1024*1024):.1f}MB (max: {self.max_file_size / (1024*1024)}MB)")
        
        if file_size == 0:
            errors.append("File is empty")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_document_set(self, document_set: str) -> ValidationResult:
        """Validate document set"""
        errors = []
        warnings = []
        
        if document_set not in self.supported_document_sets:
            errors.append(f"Unsupported document set: {document_set}")
        
        # Check if document set directory exists
        set_path = Path(f"tests/fixtures/{document_set}")
        if not set_path.exists():
            errors.append(f"Document set directory does not exist: {set_path}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_test_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate complete test configuration"""
        errors = []
        warnings = []
        
        # Validate providers
        for provider in config.get("providers", []):
            provider_result = self.validate_provider(provider)
            errors.extend(provider_result.errors)
            warnings.extend(provider_result.warnings)
        
        # Validate document sets
        for doc_set in config.get("document_sets", []):
            doc_result = self.validate_document_set(doc_set)
            errors.extend(doc_result.errors)
            warnings.extend(doc_result.warnings)
        
        # Validate timeout
        timeout = config.get("timeout_seconds", 300)
        if timeout < 30:
            warnings.append("Timeout is very short (< 30 seconds)")
        if timeout > 1800:
            warnings.append("Timeout is very long (> 30 minutes)")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

# Global validation system instance
validator = ValidationSystem()

















