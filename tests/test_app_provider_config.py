"""
Unit tests for app.py provider configuration and default behavior.

Tests verify that:
- Claude (Anthropic) is the default provider
- Validation only requires ANTHROPIC_API_KEY by default
- OpenAI is only checked when explicitly set
- Error messages guide users correctly
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import Config


class TestProviderConfiguration:
    """Test provider configuration and default behavior"""
    
    def setup_method(self):
        """Set up test fixtures - clear environment variables"""
        # Save original values
        self.original_provider = os.environ.get("AI_PROVIDER")
        self.original_anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        self.original_openai_key = os.environ.get("OPENAI_API_KEY")
        
        # Clear environment variables
        if "AI_PROVIDER" in os.environ:
            del os.environ["AI_PROVIDER"]
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
    
    def teardown_method(self):
        """Restore original environment variables"""
        if self.original_provider:
            os.environ["AI_PROVIDER"] = self.original_provider
        elif "AI_PROVIDER" in os.environ:
            del os.environ["AI_PROVIDER"]
            
        if self.original_anthropic_key:
            os.environ["ANTHROPIC_API_KEY"] = self.original_anthropic_key
        elif "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]
            
        if self.original_openai_key:
            os.environ["OPENAI_API_KEY"] = self.original_openai_key
        elif "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
    
    def test_default_provider_is_anthropic(self):
        """Test that default provider is Anthropic (Claude) when AI_PROVIDER is not set"""
        # No AI_PROVIDER set
        config = Config()
        
        assert config.AI_PROVIDER == "anthropic", "Default provider should be 'anthropic' (Claude)"
    
    def test_explicit_anthropic_provider(self):
        """Test that explicit AI_PROVIDER=anthropic works"""
        os.environ["AI_PROVIDER"] = "anthropic"
        config = Config()
        
        assert config.AI_PROVIDER == "anthropic"
    
    def test_explicit_openai_provider(self):
        """Test that explicit AI_PROVIDER=openai works"""
        os.environ["AI_PROVIDER"] = "openai"
        config = Config()
        
        assert config.AI_PROVIDER == "openai"
    
    def test_provider_case_insensitive(self):
        """Test that provider is case-insensitive"""
        os.environ["AI_PROVIDER"] = "ANTHROPIC"
        config = Config()
        
        # Config normalizes to lowercase
        assert config.AI_PROVIDER.lower() == "anthropic"
    
    def test_validation_requires_anthropic_key_by_default(self):
        """Test that validation requires ANTHROPIC_API_KEY when using default provider"""
        # No keys set, default provider
        config = Config()
        
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            config.validate()
    
    def test_validation_requires_anthropic_key_when_explicit(self):
        """Test that validation requires ANTHROPIC_API_KEY when AI_PROVIDER=anthropic"""
        os.environ["AI_PROVIDER"] = "anthropic"
        config = Config()
        
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            config.validate()
    
    def test_validation_requires_openai_key_when_explicit(self):
        """Test that validation requires OPENAI_API_KEY when AI_PROVIDER=openai"""
        os.environ["AI_PROVIDER"] = "openai"
        config = Config()
        
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            config.validate()
    
    def test_validation_passes_with_anthropic_key_default(self):
        """Test that validation passes with ANTHROPIC_API_KEY when using default provider"""
        os.environ["ANTHROPIC_API_KEY"] = "test_key"
        config = Config()
        
        # Should not raise
        assert config.validate() == True
    
    def test_validation_passes_with_anthropic_key_explicit(self):
        """Test that validation passes with ANTHROPIC_API_KEY when AI_PROVIDER=anthropic"""
        os.environ["AI_PROVIDER"] = "anthropic"
        os.environ["ANTHROPIC_API_KEY"] = "test_key"
        config = Config()
        
        # Should not raise
        assert config.validate() == True
    
    def test_validation_passes_with_openai_key_explicit(self):
        """Test that validation passes with OPENAI_API_KEY when AI_PROVIDER=openai"""
        os.environ["AI_PROVIDER"] = "openai"
        os.environ["OPENAI_API_KEY"] = "test_key"
        config = Config()
        
        # Should not raise
        assert config.validate() == True
    
    def test_validation_does_not_require_openai_key_for_default(self):
        """Test that OPENAI_API_KEY is NOT required when using default provider (Claude)"""
        os.environ["ANTHROPIC_API_KEY"] = "test_key"
        # No OPENAI_API_KEY set
        config = Config()
        
        # Should pass - only Anthropic key needed
        assert config.validate() == True
    
    def test_validation_does_not_require_anthropic_key_for_openai(self):
        """Test that ANTHROPIC_API_KEY is NOT required when using OpenAI provider"""
        os.environ["AI_PROVIDER"] = "openai"
        os.environ["OPENAI_API_KEY"] = "test_key"
        # No ANTHROPIC_API_KEY set
        config = Config()
        
        # Should pass - only OpenAI key needed
        assert config.validate() == True
    
    def test_invalid_provider_raises_error(self):
        """Test that invalid AI_PROVIDER value raises error"""
        os.environ["AI_PROVIDER"] = "invalid_provider"
        config = Config()
        
        with pytest.raises(ValueError, match="Invalid AI_PROVIDER"):
            config.validate()


class TestFinancialDataExtractorProvider:
    """Test that FinancialDataExtractor uses correct provider"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.original_provider = os.environ.get("AI_PROVIDER")
        self.original_anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        self.original_openai_key = os.environ.get("OPENAI_API_KEY")
        
        # Clear environment
        if "AI_PROVIDER" in os.environ:
            del os.environ["AI_PROVIDER"]
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
    
    def teardown_method(self):
        """Restore environment"""
        if self.original_provider:
            os.environ["AI_PROVIDER"] = self.original_provider
        if self.original_anthropic_key:
            os.environ["ANTHROPIC_API_KEY"] = self.original_anthropic_key
        if self.original_openai_key:
            os.environ["OPENAI_API_KEY"] = self.original_openai_key
    
    def test_extractor_defaults_to_anthropic(self):
        """Test that FinancialDataExtractor defaults to Anthropic (Claude)"""
        from core.extractor import FinancialDataExtractor
        
        # Set a dummy key to avoid initialization errors
        os.environ["ANTHROPIC_API_KEY"] = "test_key"
        
        extractor = FinancialDataExtractor()
        
        assert extractor.provider == "anthropic", "Extractor should default to 'anthropic' (Claude)"
    
    def test_extractor_uses_explicit_provider(self):
        """Test that FinancialDataExtractor uses explicit provider"""
        from core.extractor import FinancialDataExtractor
        
        os.environ["AI_PROVIDER"] = "openai"
        os.environ["OPENAI_API_KEY"] = "test_key"
        
        extractor = FinancialDataExtractor()
        
        assert extractor.provider == "openai", "Extractor should use explicit provider"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

