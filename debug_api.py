#!/usr/bin/env python3
"""
Debug script to test API processing functions directly
"""

import os
import sys
import io
import time

# Add the parent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_whole_document_processing():
    """Test the whole document processing function directly"""
    print("🔍 Testing Whole Document Processing Function")
    print("=" * 50)
    
    try:
        # Import the function
        import app
        process_pdf_with_whole_document_context = app.process_pdf_with_whole_document_context
        init_chromadb = app.init_chromadb
        from openai import OpenAI
        
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        if not client.api_key:
            print("❌ OpenAI API key not found")
            return
        
        # Initialize ChromaDB
        print("📊 Initializing ChromaDB...")
        chroma_client = init_chromadb()
        print("✅ ChromaDB initialized")
        
        # Test with sample file
        sample_file_path = "test_financial_statement.pdf"
        if not os.path.exists(sample_file_path):
            print(f"❌ Sample file not found: {sample_file_path}")
            return
        
        print(f"📁 Testing with: {sample_file_path}")
        
        # Read file
        with open(sample_file_path, 'rb') as f:
            file_content = f.read()
        
        # Create file-like object
        pdf_file = io.BytesIO(file_content)
        pdf_file.name = sample_file_path
        
        # Process with whole document approach
        print("🔄 Processing with whole document approach...")
        start_time = time.time()
        
        result = process_pdf_with_whole_document_context(pdf_file, client)
        
        processing_time = time.time() - start_time
        print(f"⏱️ Processing time: {processing_time:.2f} seconds")
        
        # Display result
        print(f"\n📊 Result type: {type(result)}")
        if isinstance(result, dict):
            print(f"📁 Keys: {list(result.keys())}")
            for key, value in result.items():
                if isinstance(value, dict):
                    print(f"  📂 {key}: {list(value.keys()) if value else 'Empty'}")
                    # Show some sample data for important keys
                    if key in ['line_items', 'summary_metrics'] and value:
                        for subkey, subvalue in list(value.items())[:3]:  # Show first 3 items
                            if isinstance(subvalue, dict):
                                print(f"    📄 {subkey}: {list(subvalue.keys())[:5]}...")  # Show first 5 keys
                            else:
                                print(f"    📄 {subkey}: {type(subvalue).__name__}")
                elif isinstance(value, list):
                    print(f"  📂 {key}: {len(value)} items")
                    if value and len(value) > 0:
                        print(f"    📄 First item type: {type(value[0]).__name__}")
                else:
                    print(f"  📂 {key}: {type(value).__name__}")
                    if key in ['statement_type', 'company_name', 'period']:
                        print(f"    📄 Value: {value}")
        else:
            print(f"📄 Result: {result}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_csv_export(data):
    """Test CSV export function"""
    print("\n📋 Testing CSV Export")
    print("=" * 30)
    
    try:
        from app import create_ifrs_csv_export
        
        csv_data = create_ifrs_csv_export(data)
        print(f"📄 CSV data type: {type(csv_data)}")
        print(f"📏 CSV data length: {len(csv_data) if csv_data else 0}")
        
        if csv_data:
            print("📋 CSV Preview:")
            lines = csv_data.split('\n')[:10]
            for line in lines:
                print(f"  {line}")
        else:
            print("❌ No CSV data generated")
        
        return csv_data
        
    except Exception as e:
        print(f"❌ CSV export error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main debug function"""
    print("🐛 API Debug Script")
    print("=" * 50)
    
    # Test whole document processing
    result = test_whole_document_processing()
    
    if result:
        # Test CSV export
        test_csv_export(result)
    
    print("\n🎯 Debug complete!")

if __name__ == "__main__":
    main() 