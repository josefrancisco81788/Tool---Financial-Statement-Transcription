#!/usr/bin/env python3
"""
Test script to verify that app.py uses Claude (Anthropic) by default when processing files.

This script:
1. Uses the same initialization as app.py
2. Processes a live test file
3. Verifies that Claude (Anthropic) was used, not OpenAI
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Clear any existing AI_PROVIDER to test default behavior
if "AI_PROVIDER" in os.environ:
    original_provider = os.environ["AI_PROVIDER"]
    del os.environ["AI_PROVIDER"]
    print(f"⚠️  Cleared AI_PROVIDER (was: {original_provider}) to test default behavior")
else:
    original_provider = None
    print("✅ No AI_PROVIDER set - testing default behavior")

# Import components (same as app.py)
from core.extractor import FinancialDataExtractor
from core.pdf_processor import PDFProcessor

def verify_claude_usage(extractor: FinancialDataExtractor):
    """Verify that Claude (Anthropic) is being used"""
    print("\n" + "="*80)
    print("VERIFYING PROVIDER USAGE")
    print("="*80)
    
    # Check provider attribute
    provider = extractor.provider
    print(f"📋 Extractor provider: {provider}")
    
    # Check which client is initialized
    has_anthropic = extractor.anthropic_client is not None
    has_openai = extractor.openai_client is not None
    
    print(f"🔑 Anthropic client initialized: {has_anthropic}")
    print(f"🔑 OpenAI client initialized: {has_openai}")
    
    # Verify Claude is being used
    is_claude = (provider == "anthropic" and has_anthropic and not has_openai)
    
    if is_claude:
        print("✅ VERIFIED: Claude (Anthropic) is being used!")
        print("   - Provider set to 'anthropic'")
        print("   - Anthropic client is initialized")
        print("   - OpenAI client is NOT initialized")
    else:
        print("❌ WARNING: Claude may not be the active provider!")
        if provider != "anthropic":
            print(f"   - Provider is '{provider}', expected 'anthropic'")
        if not has_anthropic:
            print("   - Anthropic client is NOT initialized")
        if has_openai:
            print("   - OpenAI client IS initialized (should not be for Claude)")
    
    return is_claude

def test_live_file():
    """Test processing a live file to verify Claude usage"""
    
    # Live files available
    live_files = [
        "tests/live/1_FS_Raw.pdf",
        "tests/live/Y2024 Balance Sheet,Income Stateement & Cash Flow.pdf",
        "tests/live/2024 ASSAI Audited Financial Statements (2).pdf",
    ]
    
    # Find first available file
    test_file = None
    for file_path in live_files:
        if os.path.exists(file_path):
            test_file = file_path
            break
    
    if not test_file:
        print("❌ No live test files found!")
        print("   Available files should be in tests/live/")
        return False
    
    print("\n" + "="*80)
    print("TESTING WITH LIVE FILE")
    print("="*80)
    print(f"📄 Test file: {test_file}")
    print(f"📏 File size: {os.path.getsize(test_file) / 1024:.2f} KB")
    
    # Initialize components (same as app.py)
    print("\n[INIT] Initializing components (same as app.py)...")
    extractor = FinancialDataExtractor()
    pdf_processor = PDFProcessor(extractor)
    
    # Verify Claude is being used BEFORE processing
    print("\n[VERIFY] Verifying provider before processing...")
    is_claude = verify_claude_usage(extractor)
    
    if not is_claude:
        print("\n❌ Provider verification failed - stopping test")
        return False
    
    # Process a small portion of the file (first few pages) to verify API calls
    print("\n[PROCESS] Processing file (first 2 pages only for quick test)...")
    try:
        # Convert PDF to images
        images, page_info = pdf_processor.convert_pdf_to_images(test_file, enable_parallel=False)
        
        if not images:
            print("❌ No images extracted from PDF")
            return False
        
        print(f"✅ Extracted {len(images)} pages")
        
        # Process only first 2 pages for quick test
        test_pages = min(2, len(images))
        print(f"📄 Processing first {test_pages} pages to verify Claude API calls...")
        
        # Classify pages (this will make API calls)
        financial_pages = pdf_processor.classify_pages_with_vision(images[:test_pages])
        
        print(f"✅ Classification complete: {len(financial_pages)} financial pages identified")
        
        # Verify provider again after API calls
        print("\n[VERIFY] Verifying provider after API calls...")
        is_claude_after = verify_claude_usage(extractor)
        
        if is_claude_after:
            print("\n" + "="*80)
            print("✅ SUCCESS: Claude (Anthropic) was used for processing!")
            print("="*80)
            print("   - Provider correctly set to 'anthropic'")
            print("   - Anthropic client was used for API calls")
            print("   - OpenAI was NOT used")
            return True
        else:
            print("\n❌ Provider verification failed after API calls")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("="*80)
    print("CLAUDE VERIFICATION TEST")
    print("="*80)
    print("\nThis test verifies that app.py uses Claude (Anthropic) by default")
    print("when processing financial statement files.\n")
    
    # Check environment
    print("[ENV] Environment check:")
    print(f"   AI_PROVIDER: {os.getenv('AI_PROVIDER', 'NOT SET (defaults to anthropic)')}")
    print(f"   ANTHROPIC_API_KEY: {'✅ SET' if os.getenv('ANTHROPIC_API_KEY') else '❌ NOT SET'}")
    print(f"   OPENAI_API_KEY: {'✅ SET' if os.getenv('OPENAI_API_KEY') else '❌ NOT SET (not needed for Claude)'}")
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ ANTHROPIC_API_KEY not found!")
        print("   Please set ANTHROPIC_API_KEY in your .env file")
        return False
    
    # Run test
    success = test_live_file()
    
    # Restore original provider if it was set
    if original_provider:
        os.environ["AI_PROVIDER"] = original_provider
        print(f"\n🔄 Restored AI_PROVIDER to: {original_provider}")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

