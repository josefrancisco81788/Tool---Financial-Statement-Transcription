#!/usr/bin/env python3
"""
Simple test script for the Financial Statement Transcription API
"""

import requests
import json
import os
from pathlib import Path

# API base URL
API_BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_api_docs():
    """Test if API documentation is accessible"""
    print("\nTesting API documentation...")
    try:
        response = requests.get(f"{API_BASE_URL}/docs")
        print(f"Status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_openapi_spec():
    """Test if OpenAPI specification is accessible"""
    print("\nTesting OpenAPI specification...")
    try:
        response = requests.get(f"{API_BASE_URL}/openapi.json")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            spec = response.json()
            print(f"API Title: {spec.get('info', {}).get('title', 'Unknown')}")
            print(f"Version: {spec.get('info', {}).get('version', 'Unknown')}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Financial Statement Transcription API")
    print("=" * 50)
    
    # Check if API is running
    print("Checking if API is running...")
    if not test_health_check():
        print("❌ API is not running. Please start the API first:")
        print("   cd api && python main.py")
        return
    
    print("✅ API is running!")
    
    # Test API documentation
    if test_api_docs():
        print("✅ API documentation is accessible")
    else:
        print("❌ API documentation is not accessible")
    
    # Test OpenAPI specification
    if test_openapi_spec():
        print("✅ OpenAPI specification is accessible")
    else:
        print("❌ OpenAPI specification is not accessible")
    
    print("\n" + "=" * 50)
    print("🎉 API setup appears to be working!")
    print("\nNext steps:")
    print("1. Visit http://localhost:8000/docs for interactive API documentation")
    print("2. Test file upload endpoints with a sample PDF or image")
    print("3. Check the API endpoints for financial data extraction")

if __name__ == "__main__":
    main() 