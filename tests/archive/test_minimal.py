#!/usr/bin/env python3
"""
Minimal test to verify basic functionality without getting stuck
"""

import os
import sys
from pathlib import Path

print("🚀 Starting minimal test...")

# Test 1: Basic imports
print("📦 Testing imports...")
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from core.config import Config
    print("   ✅ Config imported")
except Exception as e:
    print(f"   ❌ Config import failed: {e}")
    sys.exit(1)

# Test 2: Environment variable
print("🔧 Testing environment setup...")
os.environ['AI_PROVIDER'] = 'anthropic'
print(f"   ✅ AI_PROVIDER set to: {os.environ.get('AI_PROVIDER')}")

# Test 3: Config initialization
print("⚙️  Testing config initialization...")
try:
    config = Config()
    print(f"   ✅ Config initialized")
    print(f"   📋 AI Provider: {config.AI_PROVIDER}")
    print(f"   🔑 Anthropic Key: {'✅ Set' if config.ANTHROPIC_API_KEY else '❌ Missing'}")
except Exception as e:
    print(f"   ❌ Config initialization failed: {e}")
    sys.exit(1)

# Test 4: Basic document check
print("📄 Testing document availability...")
doc_path = "tests/fixtures/light/AFS2024 - statement extracted.pdf"
if Path(doc_path).exists():
    print(f"   ✅ Document found: {doc_path}")
    print(f"   📊 Size: {Path(doc_path).stat().st_size} bytes")
else:
    print(f"   ❌ Document not found: {doc_path}")
    sys.exit(1)

print("\n🎉 Minimal test completed successfully!")
print("📋 All basic components are working")
print("🔧 Ready for more complex testing")












