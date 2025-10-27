"""
Provider management system for unified testing pipeline
"""

from typing import Dict, List, Optional
from .base_provider import BaseTestProvider, TestResult
from .openai_provider import OpenAITestProvider
from .anthropic_provider import AnthropicTestProvider


class ProviderManager:
    """Manages different AI providers for testing"""
    
    def __init__(self):
        self.providers: Dict[str, BaseTestProvider] = {
            "openai": OpenAITestProvider(),
            "anthropic": AnthropicTestProvider()
        }
    
    def get_provider(self, provider_name: str) -> Optional[BaseTestProvider]:
        """Get a provider by name"""
        return self.providers.get(provider_name.lower())
    
    def list_providers(self) -> List[str]:
        """List available providers"""
        return list(self.providers.keys())
    
    def validate_provider(self, provider_name: str) -> bool:
        """Validate a specific provider"""
        provider = self.get_provider(provider_name)
        if not provider:
            print(f"   ❌ Provider not found: {provider_name}")
            return False
        
        print(f"🔍 Validating {provider_name} provider...")
        return provider.validate_configuration()
    
    def validate_all_providers(self) -> Dict[str, bool]:
        """Validate all available providers"""
        results = {}
        for provider_name in self.providers:
            results[provider_name] = self.validate_provider(provider_name)
        return results
    
    def test_provider(self, provider_name: str, document_path: str, timeout: int = 300) -> TestResult:
        """Test a specific provider with a document"""
        provider = self.get_provider(provider_name)
        if not provider:
            return TestResult(
                provider=provider_name,
                document=document_path,
                timestamp=0,
                processing_time=0,
                success=False,
                error_message=f"Provider not found: {provider_name}"
            )
        
        return provider.test_document(document_path, timeout)
    
    def test_multiple_providers(self, provider_names: List[str], document_path: str, timeout: int = 300) -> Dict[str, TestResult]:
        """Test multiple providers with the same document"""
        results = {}
        for provider_name in provider_names:
            print(f"🧪 Testing {provider_name} with {document_path}...")
            results[provider_name] = self.test_provider(provider_name, document_path, timeout)
        return results












