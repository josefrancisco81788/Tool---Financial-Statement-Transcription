"""
Financial Statement Transcription Core Module

This module contains the core extraction logic extracted from the proven
alpha-testing-v1 Streamlit application.
"""

from .extractor import FinancialDataExtractor
from .pdf_processor import PDFProcessor
from .config import Config

__all__ = ['FinancialDataExtractor', 'PDFProcessor', 'Config']
