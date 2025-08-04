import streamlit as st
from PIL import Image
import io

st.set_page_config(page_title="Button Test", layout="wide")

st.title("🔧 Minimal Button Logic Test")

# Initialize session state
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = None
if 'processing_approach' not in st.session_state:
    st.session_state.processing_approach = None
if 'selected_processing_approach' not in st.session_state:
    st.session_state.selected_processing_approach = None

st.write("## Session State Debug")
st.write(f"**selected_processing_approach:** {st.session_state.selected_processing_approach}")
st.write(f"**processing_complete:** {st.session_state.processing_complete}")
st.write(f"**uploaded_file_name:** {st.session_state.uploaded_file_name}")

# File upload
uploaded_file = st.file_uploader(
    "Choose a file",
    type=['pdf', 'png', 'jpg', 'jpeg'],
    help="Upload a PDF or image file"
)

if uploaded_file is not None:
    # Check if this is a new file
    is_new_file = st.session_state.uploaded_file_name != uploaded_file.name
    
    # Clear selected approach for new files
    if is_new_file:
        st.session_state.selected_processing_approach = None
    
    st.write(f"**File:** {uploaded_file.name}")
    st.write(f"**File type:** {uploaded_file.type}")
    st.write(f"**Is new file:** {is_new_file}")
    
    # Processing approach selection for PDFs
    processing_approach = None
    if uploaded_file.type == "application/pdf":
        st.subheader("🎯 Choose Processing Approach")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🌐 Whole Document Context")
            if st.button("🌐 Use Whole Document", type="secondary", key="whole_doc_btn"):
                st.session_state.selected_processing_approach = "whole_document"
                st.write("✅ Selected whole_document")
                st.rerun()
        
        with col2:
            st.markdown("### 🗄️ Vector Database Analysis")
            if st.button("🗄️ Use Vector Database", type="secondary", key="vector_db_btn"):
                st.session_state.selected_processing_approach = "vector_database"
                st.write("✅ Selected vector_database")
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
    
    # Process button logic
    st.write("## Button Logic Analysis")
    
    if uploaded_file.type != "application/pdf":
        # For non-PDF files, auto-select approach and always show button
        processing_approach = "single_image"
        show_button = True
        st.write("**Logic:** Non-PDF file → auto-select single_image → show_button = True")
    else:
        # For PDF files, check if user has selected an approach
        processing_approach = st.session_state.selected_processing_approach
        show_button = processing_approach is not None
        st.write(f"**Logic:** PDF file → processing_approach = {processing_approach} → show_button = {show_button}")
    
    st.write(f"**processing_approach:** {processing_approach}")
    st.write(f"**show_button:** {show_button}")
    
    # Show process button if approach is selected or it's a single image
    if show_button:
        st.success("✅ BUTTON LOGIC: Should show button")
        
        # Only disable if we already have results for this exact file and approach
        button_disabled = (
            not is_new_file and 
            st.session_state.processing_complete and 
            st.session_state.processing_approach == str(processing_approach or "Unknown").replace('_', ' ').title()
        )
        
        button_label = "🚀 Extract Financial Data"
        if button_disabled:
            button_label = "✅ Already Processed"
        
        st.write(f"**button_disabled:** {button_disabled}")
        st.write(f"**button_label:** {button_label}")
        
        if st.button(button_label, type="primary", disabled=button_disabled):
            st.success("🎉 Button was clicked!")
            # Simulate processing
            st.session_state.extracted_data = {"test": "data"}
            st.session_state.processing_complete = True
            st.session_state.uploaded_file_name = uploaded_file.name
            st.session_state.processing_approach = str(processing_approach or "Unknown").replace('_', ' ').title()
            st.rerun()
    
    else:
        st.warning("❌ BUTTON LOGIC: Should NOT show button")
        # Only show message when no approach is selected for PDFs
        if uploaded_file.type == "application/pdf":
            st.info("👆 Please select a processing approach above to continue.")
        else:
            st.error("❌ Unexpected state: Non-PDF file should always show button")

# Reset button
if st.button("🔄 Reset All Session State"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.success("All session state reset!")
    st.rerun() 