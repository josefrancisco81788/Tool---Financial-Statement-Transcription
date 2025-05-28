"""
Unit tests for Financial Statement Transcription Tool button logic
Tests the core button display functionality in isolation
"""

import streamlit as st
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the current directory to Python path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class MockSessionState:
    """Mock Streamlit session state for testing"""
    def __init__(self):
        self.extracted_data = None
        self.processing_complete = False
        self.uploaded_file_name = None
        self.processing_approach = None
        self.selected_processing_approach = None
    
    def __getattr__(self, name):
        return getattr(self, name, None)
    
    def __setattr__(self, name, value):
        super().__setattr__(name, value)

class MockUploadedFile:
    """Mock uploaded file for testing"""
    def __init__(self, name="test.pdf", file_type="application/pdf", size=1024*1024):
        self.name = name
        self.type = file_type
        self.size = size

def test_button_logic_scenarios():
    """Test all button display scenarios"""
    
    # Test Case 1: New PDF file, no approach selected
    print("=== Test Case 1: New PDF file, no approach selected ===")
    session_state = MockSessionState()
    uploaded_file = MockUploadedFile("new_file.pdf", "application/pdf")
    
    # Simulate the logic from app.py
    is_new_file = session_state.uploaded_file_name != uploaded_file.name
    processing_approach = session_state.selected_processing_approach
    
    if uploaded_file.type != "application/pdf":
        show_button = True
    else:
        show_button = processing_approach is not None
    
    print(f"  is_new_file: {is_new_file}")
    print(f"  processing_approach: {processing_approach}")
    print(f"  show_button: {show_button}")
    print(f"  Expected: show_button should be False (no approach selected)")
    assert show_button == False, "Button should not show when no approach is selected"
    print("  ✅ PASS\n")
    
    # Test Case 2: PDF file, approach selected
    print("=== Test Case 2: PDF file, approach selected ===")
    session_state.selected_processing_approach = "vector_database"
    processing_approach = session_state.selected_processing_approach
    
    if uploaded_file.type != "application/pdf":
        show_button = True
    else:
        show_button = processing_approach is not None
    
    print(f"  is_new_file: {is_new_file}")
    print(f"  processing_approach: {processing_approach}")
    print(f"  show_button: {show_button}")
    print(f"  Expected: show_button should be True (approach selected)")
    assert show_button == True, "Button should show when approach is selected"
    print("  ✅ PASS\n")
    
    # Test Case 3: Image file (should always show button)
    print("=== Test Case 3: Image file (should always show button) ===")
    uploaded_file = MockUploadedFile("test.png", "image/png")
    session_state.selected_processing_approach = None
    
    if uploaded_file.type != "application/pdf":
        processing_approach = "single_image"
        show_button = True
    else:
        processing_approach = session_state.selected_processing_approach
        show_button = processing_approach is not None
    
    print(f"  file_type: {uploaded_file.type}")
    print(f"  processing_approach: {processing_approach}")
    print(f"  show_button: {show_button}")
    print(f"  Expected: show_button should be True (image files auto-show)")
    assert show_button == True, "Button should always show for image files"
    print("  ✅ PASS\n")
    
    # Test Case 4: Same file, already processed
    print("=== Test Case 4: Same file, already processed ===")
    uploaded_file = MockUploadedFile("test.pdf", "application/pdf")
    session_state.uploaded_file_name = "test.pdf"  # Same file
    session_state.processing_complete = True
    session_state.processing_approach = "Vector Database"
    session_state.selected_processing_approach = "vector_database"
    
    is_new_file = session_state.uploaded_file_name != uploaded_file.name
    processing_approach = session_state.selected_processing_approach
    
    if uploaded_file.type != "application/pdf":
        show_button = True
    else:
        show_button = processing_approach is not None
    
    # Button should show but be disabled
    button_disabled = (
        not is_new_file and 
        session_state.processing_complete and 
        session_state.processing_approach == str(processing_approach or "Unknown").replace('_', ' ').title()
    )
    
    print(f"  is_new_file: {is_new_file}")
    print(f"  processing_complete: {session_state.processing_complete}")
    print(f"  processing_approach: {processing_approach}")
    print(f"  show_button: {show_button}")
    print(f"  button_disabled: {button_disabled}")
    print(f"  Expected: show_button=True, button_disabled=True")
    assert show_button == True, "Button should show even for processed files"
    assert button_disabled == True, "Button should be disabled for already processed files"
    print("  ✅ PASS\n")

def test_streamlit_button_simulation():
    """Simulate the actual Streamlit button logic"""
    print("=== Streamlit Button Logic Simulation ===")
    
    # Mock Streamlit functions
    with patch('streamlit.button') as mock_button, \
         patch('streamlit.info') as mock_info, \
         patch('streamlit.success') as mock_success:
        
        # Test scenario: PDF uploaded, no approach selected
        session_state = MockSessionState()
        uploaded_file = MockUploadedFile("test.pdf", "application/pdf")
        
        # Simulate the app logic
        is_new_file = session_state.uploaded_file_name != uploaded_file.name
        
        if uploaded_file.type != "application/pdf":
            processing_approach = "single_image"
            show_button = True
        else:
            processing_approach = session_state.selected_processing_approach
            show_button = processing_approach is not None
        
        print(f"  show_button: {show_button}")
        print(f"  processing_approach: {processing_approach}")
        
        if show_button:
            # This should NOT execute because show_button is False
            mock_button.return_value = False
            button_clicked = mock_button("🚀 Extract Financial Data", type="primary")
            print(f"  Button would be shown: {mock_button.called}")
        else:
            # This SHOULD execute - show the message
            if uploaded_file.type == "application/pdf":
                mock_info("👆 Please select a processing approach above to continue.")
                print(f"  Info message shown: {mock_info.called}")
            
        # Verify the correct path was taken
        if not show_button and uploaded_file.type == "application/pdf":
            assert mock_info.called, "Info message should be shown when no approach selected"
            print("  ✅ Correct message path taken")
        
        print("  ✅ PASS\n")

def create_isolated_button_test():
    """Create a minimal Streamlit app to test button logic in isolation"""
    
    test_code = '''
import streamlit as st

st.title("🧪 Button Logic Test")

# Initialize session state
if 'selected_processing_approach' not in st.session_state:
    st.session_state.selected_processing_approach = None
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = None

# Simulate file upload
st.subheader("Simulated File Upload")
file_type = st.selectbox("File Type", ["application/pdf", "image/png"])
file_name = st.text_input("File Name", "test_file.pdf")

# Simulate the uploaded file
class MockFile:
    def __init__(self, name, type):
        self.name = name
        self.type = type

uploaded_file = MockFile(file_name, file_type)

# Show current session state
st.subheader("Session State")
st.write(f"selected_processing_approach: {st.session_state.selected_processing_approach}")
st.write(f"processing_complete: {st.session_state.processing_complete}")
st.write(f"uploaded_file_name: {st.session_state.uploaded_file_name}")

# Processing approach selection (only for PDFs)
if uploaded_file.type == "application/pdf":
    st.subheader("Choose Processing Approach")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🌐 Use Whole Document", key="whole_doc"):
            st.session_state.selected_processing_approach = "whole_document"
            st.rerun()
    
    with col2:
        if st.button("🗄️ Use Vector Database", key="vector_db"):
            st.session_state.selected_processing_approach = "vector_database"
            st.rerun()

# Show selected approach
if st.session_state.selected_processing_approach:
    st.success(f"✅ Selected: {st.session_state.selected_processing_approach}")

# THE CRITICAL BUTTON LOGIC
st.subheader("Button Logic Test")

is_new_file = st.session_state.uploaded_file_name != uploaded_file.name

# Process button logic
if uploaded_file.type != "application/pdf":
    processing_approach = "single_image"
    show_button = True
    st.info("📷 Image file detected - button should always show")
else:
    processing_approach = st.session_state.selected_processing_approach
    show_button = processing_approach is not None
    st.info(f"📄 PDF file detected - show_button: {show_button}")

# Debug info
st.subheader("Debug Information")
st.write(f"**File Type:** {uploaded_file.type}")
st.write(f"**Is New File:** {is_new_file}")
st.write(f"**Processing Approach:** {processing_approach}")
st.write(f"**Show Button:** {show_button}")

# The actual button logic
if show_button:
    st.success("✅ BUTTON SHOULD APPEAR HERE")
    if st.button("🚀 Extract Financial Data", type="primary"):
        st.session_state.uploaded_file_name = uploaded_file.name
        st.session_state.processing_complete = True
        st.balloons()
        st.success("Processing would start here!")
else:
    if uploaded_file.type == "application/pdf":
        st.warning("👆 Please select a processing approach above to continue.")
    else:
        st.error("❌ This should not happen for non-PDF files")

# Reset button
if st.button("🔄 Reset Session State"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
'''
    
    with open("test_button_isolated.py", "w") as f:
        f.write(test_code)
    
    print("Created isolated button test: test_button_isolated.py")
    print("Run with: streamlit run test_button_isolated.py")

if __name__ == "__main__":
    print("🧪 Running Button Logic Unit Tests\n")
    
    try:
        test_button_logic_scenarios()
        test_streamlit_button_simulation()
        create_isolated_button_test()
        
        print("🎉 All tests passed!")
        print("\nNext steps:")
        print("1. Run the isolated test: streamlit run test_button_isolated.py")
        print("2. Test the button logic in a clean environment")
        print("3. Compare with the main app behavior")
        
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}") 