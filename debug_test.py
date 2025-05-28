import streamlit as st

st.title("Debug Test - Button Logic")

# Initialize session state
if 'selected_processing_approach' not in st.session_state:
    st.session_state.selected_processing_approach = None
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False

# Test file upload
uploaded_file = st.file_uploader("Test file upload", type=['pdf'])

if uploaded_file:
    st.write(f"File uploaded: {uploaded_file.name}")
    
    # Test approach selection
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Select Whole Document", key="whole_doc"):
            st.session_state.selected_processing_approach = "whole_document"
            st.rerun()
    
    with col2:
        if st.button("Select Vector DB", key="vector_db"):
            st.session_state.selected_processing_approach = "vector_database"
            st.rerun()
    
    # Show selected approach
    if st.session_state.selected_processing_approach:
        st.success(f"Selected: {st.session_state.selected_processing_approach}")
        
        # Test the button logic
        is_new_file = True  # Simulate new file
        processing_approach = st.session_state.selected_processing_approach
        show_button = processing_approach is not None
        
        st.write(f"Debug info:")
        st.write(f"- is_new_file: {is_new_file}")
        st.write(f"- processing_complete: {st.session_state.processing_complete}")
        st.write(f"- processing_approach: {processing_approach}")
        st.write(f"- show_button: {show_button}")
        
        if is_new_file or not st.session_state.processing_complete:
            if show_button:
                if st.button("🚀 Extract Financial Data", type="primary"):
                    st.success("Button clicked successfully!")
                    st.session_state.processing_complete = True
            else:
                st.error("show_button is False")
        else:
            st.info("Condition not met: not (is_new_file or not processing_complete)")
    else:
        st.info("No approach selected yet") 