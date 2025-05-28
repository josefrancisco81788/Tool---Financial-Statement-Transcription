#!/usr/bin/env python3
"""
Debug script to test button logic
"""

import streamlit as st

st.title("🔧 Button Logic Debug")

# Initialize session state
if 'selected_processing_approach' not in st.session_state:
    st.session_state.selected_processing_approach = None

st.write("## Current Session State")
st.write(f"**selected_processing_approach:** {st.session_state.selected_processing_approach}")

# Mock file upload
st.write("## Mock File Upload")
uploaded_file_type = "application/pdf"
st.write(f"**File type:** {uploaded_file_type}")

# Processing approach selection
st.write("## Processing Approach Selection")

col1, col2 = st.columns(2)

with col1:
    if st.button("🌐 Use Whole Document", key="whole_doc"):
        st.session_state.selected_processing_approach = "whole_document"
        st.write("✅ Set to whole_document")
        st.rerun()

with col2:
    if st.button("🗄️ Use Vector Database", key="vector_db"):
        st.session_state.selected_processing_approach = "vector_database"
        st.write("✅ Set to vector_database")
        st.rerun()

# Show selected approach
if st.session_state.selected_processing_approach:
    st.success(f"✅ Selected: {st.session_state.selected_processing_approach}")

# Button logic test
st.write("## Button Logic Test")

# Replicate the exact logic from app.py
if uploaded_file_type != "application/pdf":
    processing_approach = "single_image"
    show_button = True
    st.info("📷 Non-PDF: show_button = True")
else:
    processing_approach = st.session_state.selected_processing_approach
    show_button = processing_approach is not None
    st.info(f"📄 PDF: processing_approach = {processing_approach}, show_button = {show_button}")

st.write(f"**processing_approach:** {processing_approach}")
st.write(f"**show_button:** {show_button}")

# Test the button display
if show_button:
    st.success("✅ BUTTON SHOULD APPEAR BELOW")
    
    if st.button("🚀 Extract Financial Data", type="primary", key="extract"):
        st.balloons()
        st.success("🎉 Button clicked!")
else:
    st.warning("❌ Button will NOT appear")
    if uploaded_file_type == "application/pdf":
        st.info("👆 Please select a processing approach above to continue.")

# Reset button
if st.button("🔄 Reset", key="reset"):
    st.session_state.selected_processing_approach = None
    st.rerun() 