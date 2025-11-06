"""
Comprehensive error handling for unified testing pipeline
"""

import logging
import traceback
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ErrorInfo:
    """Structured error information"""
    error_type: str
    message: str
    severity: ErrorSeverity
    context: Dict[str, Any]
    traceback: Optional[str] = None
    recoverable: bool = False

class ErrorHandler:
    """Handles errors throughout the testing pipeline"""
    
    def __init__(self):
        self.error_log = []
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        log_dir = Path("tests/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'error.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
        """Handle and categorize errors"""
        error_info = ErrorInfo(
            error_type=type(error).__name__,
            message=str(error),
            severity=self._determine_severity(error),
            context=context or {},
            traceback=traceback.format_exc(),
            recoverable=self._is_recoverable(error)
        )
        
        self.error_log.append(error_info)
        self.logger.error(f"Error handled: {error_info.message}", exc_info=True)
        
        return error_info
    
    def _determine_severity(self, error: Exception) -> ErrorSeverity:
        """Determine error severity based on error type"""
        if isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorSeverity.HIGH
        elif isinstance(error, (ValueError, TypeError)):
            return ErrorSeverity.MEDIUM
        elif isinstance(error, (FileNotFoundError, PermissionError)):
            return ErrorSeverity.HIGH
        else:
            return ErrorSeverity.LOW
    
    def _is_recoverable(self, error: Exception) -> bool:
        """Determine if error is recoverable"""
        recoverable_errors = (ConnectionError, TimeoutError, ValueError)
        return isinstance(error, recoverable_errors)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors encountered"""
        severity_counts = {}
        for error in self.error_log:
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_errors": len(self.error_log),
            "severity_breakdown": severity_counts,
            "recoverable_errors": sum(1 for e in self.error_log if e.recoverable),
            "critical_errors": sum(1 for e in self.error_log if e.severity == ErrorSeverity.CRITICAL)
        }

# Global error handler instance
error_handler = ErrorHandler()

















