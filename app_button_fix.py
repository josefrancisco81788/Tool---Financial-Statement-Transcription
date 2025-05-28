"""
Fixed button logic for the Financial Statement Transcription Tool
This isolates and fixes the button display issue
"""

import streamlit as st

def test_button_logic():
    st.title("🔧 Fixed Button Logic Test")
    
    # Mock session state initialization
    if 'selected_processing_approach' not in st.session_state:
        st.session_state.selected_processing_approach = None
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'uploaded_file_name' not in st.session_state:
        st.session_state.uploaded_file_name = None
    if 'processing_approach' not in st.session_state:
        st.session_state.processing_approach = None
    
    # Mock file upload
    st.subheader("File Upload Simulation")
    file_type = st.selectbox("File Type", ["application/pdf", "image/png"])
    file_name = st.text_input("File Name", "test_document.pdf")
    
    # Create mock uploaded file
    class MockFile:
        def __init__(self, name, type):
            self.name = name
            self.type = type
    
    uploaded_file = MockFile(file_name, file_type)
    is_new_file = st.session_state.uploaded_file_name != uploaded_file.name
    
    st.write(f"**File:** {uploaded_file.name}")
    st.write(f"**Type:** {uploaded_file.type}")
    st.write(f"**Is new file:** {is_new_file}")
    
    # Processing approach selection for PDFs
    if uploaded_file.type == "application/pdf":
        st.subheader("🎯 Choose Processing Approach")
        
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
        approach_name = st.session_state.selected_processing_approach.replace('_', ' ').title()
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"✅ Selected: {approach_name}")
        with col2:
            if st.button("🔄 Change", key="change_approach"):
                st.session_state.selected_processing_approach = None
                st.rerun()
    
    # FIXED BUTTON LOGIC - This is the corrected version
    st.subheader("🚀 Extract Button Logic")
    
    # Determine if button should show
    if uploaded_file.type != "application/pdf":
        # For non-PDF files, auto-select approach and always show button
        processing_approach = "single_image"
        show_button = True
        st.info("📷 Image file - button will always show")
    else:
        # For PDF files, check if user has selected an approach
        processing_approach = st.session_state.selected_processing_approach
        show_button = processing_approach is not None
        st.info(f"📄 PDF file - show_button: {show_button} (approach: {processing_approach})")
    
    # Debug information
    with st.expander("🔧 Debug Info", expanded=True):
        st.write(f"**Selected approach:** {st.session_state.selected_processing_approach}")
        st.write(f"**Processing approach:** {processing_approach}")
        st.write(f"**Show button:** {show_button}")
        st.write(f"**Processing complete:** {st.session_state.processing_complete}")
        
        if st.button("🔄 Reset Session State", key="reset"):
            for key in ['selected_processing_approach', 'processing_complete', 'uploaded_file_name', 'processing_approach']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # THE CORRECTED BUTTON LOGIC
    if show_button:
        # Button should appear here
        st.success("✅ EXTRACT BUTTON SHOULD APPEAR BELOW")
        
        # Check if button should be disabled
        button_disabled = (
            not is_new_file and 
            st.session_state.processing_complete and 
            st.session_state.processing_approach == str(processing_approach or "Unknown").replace('_', ' ').title()
        )
        
        button_label = "🚀 Extract Financial Data"
        if button_disabled:
            button_label = "✅ Already Processed"
        
        # THE ACTUAL BUTTON - NO PROBLEMATIC ELSE CLAUSE
        if st.button(button_label, type="primary", disabled=button_disabled, key="extract_btn"):
            st.session_state.uploaded_file_name = uploaded_file.name
            st.session_state.processing_complete = True
            st.session_state.processing_approach = str(processing_approach or "Unknown").replace('_', ' ').title()
            st.balloons()
            st.success("🎉 Processing would start here!")
            st.rerun()
        
        # NO ELSE CLAUSE HERE - This was the bug!
        
    else:
        # Only show this when no approach is selected for PDFs
        if uploaded_file.type == "application/pdf":
            st.warning("👆 Please select a processing approach above to continue.")
        else:
            st.error("❌ This should never happen for non-PDF files")

if __name__ == "__main__":
    test_button_logic() 