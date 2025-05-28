import streamlit as st

st.title("🔧 Session State Debug Test")

# Initialize session state
if 'selected_processing_approach' not in st.session_state:
    st.session_state.selected_processing_approach = None

st.write("## Current Session State")
st.write(f"**selected_processing_approach:** {st.session_state.selected_processing_approach}")

# Simulate the approach selection
st.write("## Approach Selection")
col1, col2 = st.columns(2)

with col1:
    if st.button("🌐 Use Whole Document", type="secondary", key="whole_doc_btn"):
        st.session_state.selected_processing_approach = "whole_document"
        st.write("✅ Set to whole_document")
        st.rerun()

with col2:
    if st.button("🗄️ Use Vector Database", type="secondary", key="vector_db_btn"):
        st.session_state.selected_processing_approach = "vector_database"
        st.write("✅ Set to vector_database")
        st.rerun()

# Show selected approach
if st.session_state.selected_processing_approach:
    approach_name = st.session_state.selected_processing_approach.replace('_', ' ').title()
    st.success(f"✅ Selected: {approach_name}")
    
    if st.button("🔄 Change", key="change_approach"):
        st.session_state.selected_processing_approach = None
        st.rerun()

# Simulate the button logic
st.write("## Button Logic Test")

# Simulate PDF file type
uploaded_file_type = "application/pdf"
st.write(f"**File type:** {uploaded_file_type}")

# Process button logic
if uploaded_file_type != "application/pdf":
    processing_approach = "single_image"
    show_button = True
    st.write("**Logic:** Non-PDF file → show_button = True")
else:
    processing_approach = st.session_state.selected_processing_approach
    show_button = processing_approach is not None
    st.write(f"**Logic:** PDF file → processing_approach = {processing_approach} → show_button = {show_button}")

st.write(f"**processing_approach:** {processing_approach}")
st.write(f"**show_button:** {show_button}")

# Show the result
if show_button:
    st.success("✅ BUTTON SHOULD APPEAR")
    if st.button("🚀 Extract Financial Data", type="primary"):
        st.success("Button clicked!")
else:
    st.warning("❌ BUTTON SHOULD NOT APPEAR")
    st.info("👆 Please select a processing approach above to continue.")

# Reset button
if st.button("🔄 Reset Session State"):
    st.session_state.selected_processing_approach = None
    st.success("Session state reset!")
    st.rerun() 