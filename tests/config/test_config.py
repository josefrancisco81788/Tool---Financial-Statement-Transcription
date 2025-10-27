"""
Test configuration system for unified testing pipeline
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path
import yaml
import json


@dataclass
class TestConfig:
    """Configuration for test runs"""
    
    # Provider settings
    providers: List[str] = field(default_factory=lambda: ["openai", "anthropic"])
    provider_configs: Dict[str, Dict] = field(default_factory=dict)
    
    # Document settings
    document_sets: List[str] = field(default_factory=lambda: ["light", "origin"])
    custom_documents: List[str] = field(default_factory=list)
    
    # Test settings
    timeout_seconds: int = 300
    parallel_workers: int = 1
    retry_attempts: int = 3
    
    # Output settings
    output_formats: List[str] = field(default_factory=lambda: ["json", "csv", "html"])
    baseline_comparison: bool = True
    provider_comparison: bool = True
    
    # Validation settings
    accuracy_threshold: float = 0.6
    performance_threshold: float = 120.0  # seconds
    
    # Framework settings
    use_scoring_framework: bool = True
    production_readiness_check: bool = True
    
    @classmethod
    def from_yaml(cls, yaml_file: str) -> 'TestConfig':
        """Load configuration from YAML file"""
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
        
        # Convert to TestConfig object
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_file: str) -> 'TestConfig':
        """Load configuration from JSON file"""
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        return cls(**data)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'providers': self.providers,
            'provider_configs': self.provider_configs,
            'document_sets': self.document_sets,
            'custom_documents': self.custom_documents,
            'timeout_seconds': self.timeout_seconds,
            'parallel_workers': self.parallel_workers,
            'retry_attempts': self.retry_attempts,
            'output_formats': self.output_formats,
            'baseline_comparison': self.baseline_comparison,
            'provider_comparison': self.provider_comparison,
            'accuracy_threshold': self.accuracy_threshold,
            'performance_threshold': self.performance_threshold,
            'use_scoring_framework': self.use_scoring_framework,
            'production_readiness_check': self.production_readiness_check
        }
    
    def save_yaml(self, yaml_file: str):
        """Save configuration to YAML file"""
        with open(yaml_file, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
    
    def save_json(self, json_file: str):
        """Save configuration to JSON file"""
        with open(json_file, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


# Preset configurations
QUICK_CONFIG = TestConfig(
    providers=["anthropic"],
    document_sets=["light"],
    timeout_seconds=180,
    parallel_workers=1,
    retry_attempts=2,
    output_formats=["json", "csv"],
    baseline_comparison=False,
    provider_comparison=False,
    accuracy_threshold=0.5,
    performance_threshold=180.0
)

COMPREHENSIVE_CONFIG = TestConfig(
    providers=["openai", "anthropic"],
    document_sets=["light", "origin"],
    timeout_seconds=600,
    parallel_workers=2,
    retry_attempts=3,
    output_formats=["json", "csv", "html"],
    baseline_comparison=True,
    provider_comparison=True,
    accuracy_threshold=0.6,
    performance_threshold=300.0
)

REGRESSION_CONFIG = TestConfig(
    providers=["anthropic"],
    document_sets=["light"],
    timeout_seconds=300,
    parallel_workers=1,
    retry_attempts=3,
    output_formats=["json", "html"],
    baseline_comparison=True,
    provider_comparison=False,
    accuracy_threshold=0.6,
    performance_threshold=120.0
)












