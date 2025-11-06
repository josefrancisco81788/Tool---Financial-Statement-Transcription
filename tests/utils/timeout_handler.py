"""
Advanced timeout handling for unified testing pipeline
"""

import signal
import threading
import time
from typing import Callable, Any, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import functools

class TimeoutHandler:
    """Handles timeouts for test operations with cross-platform support"""
    
    def __init__(self, default_timeout: int = 300):
        self.default_timeout = default_timeout
    
    def execute_with_timeout(self, func: Callable, timeout: Optional[int] = None, *args, **kwargs) -> Any:
        """Execute function with timeout using ThreadPoolExecutor (Windows compatible)"""
        timeout = timeout or self.default_timeout
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=timeout)
            except TimeoutError:
                raise TimeoutError(f"Operation timed out after {timeout} seconds")
    
    def timeout_decorator(self, timeout: int):
        """Decorator for adding timeout to functions"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return self.execute_with_timeout(func, timeout, *args, **kwargs)
            return wrapper
        return decorator

# Global timeout handler instance
timeout_handler = TimeoutHandler()

















