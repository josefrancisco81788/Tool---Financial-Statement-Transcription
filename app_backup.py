import streamlit as st
import pandas as pd
import json
import base64
from PIL import Image
import io
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv
from openai import OpenAI
import time
import chromadb
from chromadb.config import Settings
import numpy as np
import fitz  # PyMuPDF
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import random
import re


# Rate limiting and retry utilities
def exponential_backoff_retry(func, max_retries=3, base_delay=1, max_delay=60):
    """Implement exponential backoff for API calls with rate limiting"""
    for attempt in range(max_retries):
        try:
            result = func()
            if result is None:
                raise Exception("API returned None response")
            return result
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if it's a rate limit error
            if '429' in error_str or 'rate limit' in error_str or 'too many requests' in error_str:
                if attempt < max_retries - 1:
                    # Calculate delay with jitter
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    st.warning(f"⏳ Rate limit hit. Waiting {delay:.1f} seconds before retry {attempt + 2}/{max_retries}...")
                    time.sleep(delay)
                    continue
                else:
                    st.error("❌ Rate limit exceeded. Please wait a few minutes before trying again.")
                    raise e
            else:
                # Non-rate-limit error, don't retry
                raise e
    
    # If we get here, all retries failed
    raise Exception("All retry attempts failed")

def analyze_document_characteristics(uploaded_file):
    """Analyze document to recommend optimal processing approach"""
    try:
        # Get file size in MB
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        
        # Get page count
        pdf_document = fitz.Document(stream=uploaded_file.getvalue(), filetype="pdf")
        page_count = len(pdf_document)
        pdf_document.close()
        
        # Determine recommended approach
        if page_count <= 10 and file_size_mb <= 5:
            recommendation = "whole_document"
            reason = f"Small document ({page_count} pages, {file_size_mb:.1f}MB) - Whole Document Context recommended for comprehensive analysis"
            confidence = "high"
        elif page_count <= 30 and file_size_mb <= 15:
            recommendation = "user_choice"
            reason = f"Medium document ({page_count} pages, {file_size_mb:.1f}MB) - Either approach should work well"
            confidence = "medium"
        else:
            recommendation = "vector_database"
            reason = f"Large document ({page_count} pages, {file_size_mb:.1f}MB) - Vector Database recommended for reliability and speed"
            confidence = "high"
        
        return {
            "page_count": page_count,
            "file_size_mb": file_size_mb,
            "recommendation": recommendation,
            "reason": reason,
            "confidence": confidence
        }
    except Exception as e:
        st.warning(f"Could not analyze document characteristics: {str(e)}")
        return {
            "page_count": "unknown",
            "file_size_mb": "unknown", 
            "recommendation": "user_choice",
            "reason": "Unable to analyze document - please choose based on your preference",
            "confidence": "low"
        }


# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="Financial Statement Transcription Tool",
    page_icon="📊",
    layout="wide"
)

# Try to import PDF processing libraries with better error handling
pdf_processing_available = False
pdf_library = None
pdf_error_message = None

# Test pdf2image with actual Poppler availability
try:
    from pdf2image import convert_from_bytes
    # Test if Poppler is actually available by trying a minimal conversion
    import tempfile
    import os
    
    # Create a minimal valid PDF for testing
    minimal_pdf = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000074 00000 n 
0000000120 00000 n 
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
0
%%EOF"""
    
    # Try to convert the test PDF
    test_images = convert_from_bytes(minimal_pdf, dpi=72)
    if test_images:
        pdf_processing_available = True
        pdf_library = "pdf2image"
    else:
        raise Exception("pdf2image conversion failed")
        
except Exception as e:
    # pdf2image failed, try PyMuPDF
    try:
        import fitz  # PyMuPDF
        # Test if fitz.open works properly
        test_doc = fitz.Document()  # Create empty document to test
        test_doc.close()
        pdf_processing_available = True
        pdf_library = "pymupdf"
    except (ImportError, AttributeError) as pymupdf_error:
        pdf_error_message = f"Neither pdf2image (with Poppler) nor PyMuPDF available for PDF processing. pdf2image error: {str(e)}, PyMuPDF error: {str(pymupdf_error)}"

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .results-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #007bff;
    }
    .confidence-high { color: #28a745; font-weight: bold; }
    .confidence-medium { color: #ffc107; font-weight: bold; }
    .confidence-low { color: #dc3545; font-weight: bold; }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def init_database():
    """Initialize SQLite database for logging
    
    Note: In cloud deployments (like Render), this database is ephemeral
    and will be reset on each deployment. For production use, consider
    switching to a persistent database like PostgreSQL.
    """
    try:
        conn = sqlite3.connect('financial_statements.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                processing_time REAL,
                accuracy_score REAL,
                timestamp DATETIME,
                status TEXT
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        # Handle database initialization errors gracefully
        st.warning(f"Database initialization warning: {str(e)}")
        pass

def encode_image(image_file):
    """Encode image to base64 for OpenAI API"""
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

def convert_pdf_to_images(pdf_file, enable_parallel=True):
    """Convert PDF to images and extract text using Vision API"""
    if not pdf_processing_available:
        error_msg = pdf_error_message or "PDF processing not available"
        st.error(f"❌ {error_msg}")
        
        # Show installation instructions
        with st.expander("📋 How to fix PDF processing", expanded=True):
            st.markdown("""
            **Option 1: Install Poppler for pdf2image (Recommended)**
            
            On Windows:
            1. Download Poppler from: https://github.com/oschwartz10612/poppler-windows/releases/
            2. Extract to `C:\\poppler-xx.xx.x`
            3. Add `C:\\poppler-xx.xx.x\\Library\\bin` to your PATH environment variable
            4. Restart your terminal/IDE
            
            **Option 2: Install PyMuPDF as fallback**
            ```bash
            pip install PyMuPDF
            ```
            
            **Option 3: Convert PDF to images manually**
            - Use any PDF to image converter
            - Upload the resulting images instead
            """)
        return None, None
        
    try:
        if pdf_library == "pdf2image":
            # Use pdf2image
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(pdf_file.getvalue(), dpi=200)
        elif pdf_library == "pymupdf":
            # Use PyMuPDF as fallback
            import fitz
            doc = fitz.Document(stream=pdf_file.getvalue(), filetype="pdf")
            images = []
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(200/72, 200/72))  # 200 DPI
                img_data = pix.tobytes("png")
                images.append(Image.open(io.BytesIO(img_data)))
            doc.close()
        else:
            st.error("❌ No PDF processing library available")
            return None, None
        
        page_info = []
        
        st.info(f"📄 Converting {len(images)} page(s) to images and extracting text with AI...")
        
        # Parallel text extraction with 5 workers
        def extract_text_for_page(page_data):
            """Extract text from a single page - designed for parallel execution"""
            page_num, image = page_data
            try:
                page_text = extract_text_with_vision_api(image, page_num + 1)
                return {
                    'page_num': page_num + 1,
                    'text': page_text.lower(),
                    'image': image,
                    'success': True,
                    'error': None
                }
            except Exception as e:
                return {
                    'page_num': page_num + 1,
                    'text': '',
                    'image': image,
                    'success': False,
                    'error': str(e)
                }
        
        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        completed_count = 0
        total_pages = len(images)
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all pages for processing
            page_data_list = [(page_num, image) for page_num, image in enumerate(images)]
            future_to_page = {executor.submit(extract_text_for_page, page_data): page_data[0] 
                             for page_data in page_data_list}
            
            # Collect results as they complete
            results = {}
            failed_pages = []
            
            for future in as_completed(future_to_page):
                page_num = future_to_page[future]
                try:
                    result = future.result()
                    results[result['page_num']] = result
                    
                    if result['success']:
                        completed_count += 1
                        progress = completed_count / total_pages
                        progress_bar.progress(progress)
                        status_text.text(f"✅ Completed page {result['page_num']}/{total_pages} ({completed_count} successful)")
                    else:
                        failed_pages.append(result['page_num'])
                        st.warning(f"⚠️ Failed to extract text from page {result['page_num']}: {result['error']}")
                        
                except Exception as e:
                    failed_pages.append(page_num + 1)
                    st.error(f"❌ Unexpected error processing page {page_num + 1}: {str(e)}")
        
        # Sort results by page number and create page_info list
        for page_num in sorted(results.keys()):
            result = results[page_num]
            if result['success']:
                page_info.append({
                    'page_num': result['page_num'],
                    'text': result['text'],
                    'image': result['image']
                })
        
        # Final status update
        progress_bar.progress(1.0)
        if failed_pages:
            st.warning(f"⚠️ Processing completed with {len(failed_pages)} failed pages: {failed_pages}")
            st.info(f"✅ Successfully processed {len(page_info)}/{total_pages} pages with parallel AI text extraction")
        else:
            st.success(f"✅ Successfully processed all {len(page_info)} pages with parallel AI text extraction")
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        return images, page_info
        
    except Exception as e:
        st.error(f"Error converting PDF: {str(e)}")
        if "poppler" in str(e).lower():
            st.error("💡 This looks like a Poppler installation issue. Please see the instructions above.")
        return None, None

def extract_text_with_vision_api(pil_image, page_num):
    """Extract text from image using OpenAI Vision API - thread-safe version"""
    try:
        # Encode image
        base64_image = encode_pil_image(pil_image)
        
        # Optimized prompt for text extraction and classification
        prompt = """
        Extract all visible text from this financial document page. Focus on:
        - Headings and titles
        - Financial statement names (Balance Sheet, Income Statement, Cash Flow, etc.)
        - Key financial terms and line items
        - Company names and dates
        
        Return only the extracted text, preserving the general structure but without special formatting.
        """
        
        response = exponential_backoff_retry(
            lambda: client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4000
            )
        )
        
        extracted_text = response.choices[0].message.content or ""
        
        # Return just the text - progress tracking handled by caller
        return extracted_text
        
    except Exception as e:
        # Re-raise exception to be handled by parallel coordinator
        raise Exception(f"Error extracting text from page {page_num}: {str(e)}")

def encode_pil_image(pil_image):
    """Encode PIL Image to base64 for OpenAI API"""
    buffer = io.BytesIO()
    pil_image.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def extract_financial_data(image_file, file_type):
    """Extract financial data using OpenAI GPT-4 Vision with vector database enhancement"""
    try:
        # Handle PDF files with vector database approach
        if file_type == 'pdf':
            st.info("🔍 Processing PDF with AI-powered semantic analysis...")
            return process_pdf_with_vector_db(image_file, client)
        
        # Handle single image files
        else:
            st.info("🔍 Analyzing image with AI...")
            base64_image = encode_image(image_file)
            
            # Extract financial data from single image
            response = exponential_backoff_retry(
                lambda: client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """Extract financial data from this image. Return the data in JSON format with:
                                    {
                                        "statement_type": "type of financial statement",
                                        "period": "period covered",
                                        "currency": "currency used",
                                        "line_items": [
                                            {"item": "line item name", "value": "numerical value", "category": "category"}
                                        ]
                                    }"""
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=4000
                )
            )
            
            return response.choices[0].message.content
            
    except Exception as e:
        st.error(f"Error extracting financial data: {str(e)}")
        return None

def log_processing(filename, processing_time, accuracy_score, status):
    """Log processing results to database"""
    try:
        conn = sqlite3.connect('financial_statements.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO processing_log (filename, processing_time, accuracy_score, timestamp, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (filename, processing_time, accuracy_score, datetime.now(), status))
        conn.commit()
        conn.close()
    except Exception as e:
        # Fail silently if database logging fails (important for cloud deployments)
        pass

def get_confidence_class(confidence):
    """Get CSS class based on confidence score"""
    if confidence >= 0.8:
        return "confidence-high"
    elif confidence >= 0.5:
        return "confidence-medium"
    else:
        return "confidence-low"

def display_extracted_data(data):
    """Display extracted financial data in a user-friendly format"""
    if not data:
        return None
    
    # Handle multiple page results
    if isinstance(data, list):
        st.subheader("📊 Multi-Page Financial Analysis Results")
        
        # Create tabs for each page
        tab_names = [f"Page {result.get('page_number', 'N/A')}: {result.get('statement_type', 'Unknown')}" 
                    for result in data]
        tabs = st.tabs(tab_names)
        
        all_dfs = []
        for i, (tab, result) in enumerate(zip(tabs, data)):
            with tab:
                st.markdown(f"**Page {result.get('page_number', 'N/A')}** - {result.get('statement_type', 'Unknown')}")
                df = display_single_page_data(result)
                if df is not None:
                    all_dfs.append(df)
        
        # Combined export option
        if all_dfs:
            st.markdown("---")
            st.subheader("📤 Export All Pages")
            combined_df = pd.concat(all_dfs, ignore_index=True)
            csv = combined_df.to_csv(index=False)
            st.download_button(
                label="📄 Download All Pages as CSV",
                data=csv,
                file_name=f"financial_data_all_pages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_all_pages_csv"
            )
        
        return all_dfs
    else:
        # Handle single page result
        return display_single_page_data(data)

def display_single_page_data(data):
    """Display comprehensive extracted financial data for a single page"""
    if not data:
        return None
        
    st.markdown('<div class="results-section">', unsafe_allow_html=True)
    
    # Company Information with Year Information
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Company", data.get("company_name", "Not found"))
    with col2:
        st.metric("Statement Type", data.get("statement_type", "Not identified"))
    with col3:
        st.metric("Period", data.get("period", "Not found"))
    with col4:
        # Show year information
        years_detected = data.get("years_detected", [])
        base_year = data.get("base_year", "Unknown")
        if years_detected:
            year_info = f"Base: {base_year}"
            if len(years_detected) > 1:
                year_info += f" (+{len(years_detected)-1} more)"
            st.metric("Years", year_info)
        else:
            st.metric("Years", "Not detected")
    
    # Show detailed year mapping if available
    if years_detected and len(years_detected) > 1:
        st.info(f"📅 **Year Mapping:** Base Year = {base_year}, " + 
               ", ".join([f"Year {i} = {year}" for i, year in enumerate(years_detected[1:], 1)]))
    
    st.markdown("---")
    
    # Summary Metrics (Key totals for quick overview)
    st.subheader("📊 Summary Metrics")
    summary_metrics = data.get("summary_metrics", {})
    
    if summary_metrics:
        cols = st.columns(3)
        metric_count = 0
        for field, info in summary_metrics.items():
            if info and info.get("value") is not None:
                col_idx = metric_count % 3
                with cols[col_idx]:
                    confidence_class = get_confidence_class(info.get("confidence", 0))
                    st.metric(
                        field.replace("_", " ").title(),
                        f"{info['value']:,.0f}",
                        help=f"Confidence: {info.get('confidence', 0):.1%}"
                    )
                metric_count += 1
    
    st.markdown("---")
    
    # Detailed Line Items
    st.subheader("📋 Detailed Line Items")
    
    line_items = data.get("line_items", {})
    all_line_items = []
    
    # Get years for column headers
    years_detected = data.get("years_detected", [])
    base_year = data.get("base_year", "Base")
    
    # Process each category of line items
    for category, category_data in line_items.items():
        if not category_data:
            continue
            
        st.markdown(f"### {category.replace('_', ' ').title()}")
        
        # Handle nested structure (like current_assets, non_current_assets)
        if isinstance(category_data, dict):
            for subcategory, subcategory_data in category_data.items():
                if isinstance(subcategory_data, dict):
                    # This is a subcategory (like current_assets)
                    if any(item.get("value") is not None for item in subcategory_data.values() if isinstance(item, dict)):
                        st.markdown(f"**{subcategory.replace('_', ' ').title()}**")
                        
                        for field, info in subcategory_data.items():
                            if isinstance(info, dict) and info.get("value") is not None:
                                # Prepare year data for display
                                year_data = {}
                                if "base_year" in info and info["base_year"] is not None:
                                    year_data[base_year] = info["base_year"]
                                for i, year in enumerate(years_detected[1:], 1):
                                    year_key = f"year_{i}"
                                    if year_key in info and info[year_key] is not None:
                                        year_data[year] = info[year_key]
                                
                                all_line_items.append({
                                    "Category": category.replace("_", " ").title(),
                                    "Subcategory": subcategory.replace("_", " ").title(),
                                    "Field": field.replace("_", " ").title(),
                                    "Value": info["value"],
                                    "Confidence": f"{info['confidence']:.1%}",
                                    "Confidence_Score": info["confidence"],
                                    "Year_Data": year_data
                                })
                                
                                # Display individual line item with multi-year data
                                if len(year_data) > 1:
                                    # Multi-year display
                                    st.write(f"  • **{field.replace('_', ' ').title()}**")
                                    year_cols = st.columns(min(len(year_data) + 1, 5))  # Limit to 5 columns
                                    
                                    with year_cols[0]:
                                        confidence_class = get_confidence_class(info["confidence"])
                                        st.markdown(f'<span class="{confidence_class}">{info["confidence"]:.1%}</span>', 
                                                  unsafe_allow_html=True)
                                    
                                    for idx, (year, value) in enumerate(year_data.items(), 1):
                                        if idx < len(year_cols):
                                            with year_cols[idx]:
                                                st.metric(str(year), f"{value:,.0f}" if value else "N/A")
                                else:
                                    # Single year display
                                    col1, col2, col3 = st.columns([3, 2, 1])
                                    with col1:
                                        item_name = field.replace('_', ' ').title()
                                        # Show data source for equity items
                                        if info.get("source") == "Statement of Equity":
                                            st.write(f"  • {item_name} 🔗")
                                            st.caption("   ↳ Enhanced from Statement of Equity")
                                        else:
                                            st.write(f"  • {item_name}")
                                    with col2:
                                        new_value = st.number_input(
                                            f"Value", 
                                            value=float(info["value"]),
                                            key=f"edit_{category}_{subcategory}_{field}_{id(data)}",
                                            format="%.2f",
                                            label_visibility="collapsed"
                                        )
                                    with col3:
                                        confidence_class = get_confidence_class(info["confidence"])
                                        st.markdown(f'<span class="{confidence_class}">{info["confidence"]:.1%}</span>', 
                                                  unsafe_allow_html=True)
                else:
                    # This is a direct field (like total_assets)
                    if isinstance(subcategory_data, dict) and subcategory_data.get("value") is not None:
                        # Prepare year data for display
                        year_data = {}
                        if "base_year" in subcategory_data and subcategory_data["base_year"] is not None:
                            year_data[base_year] = subcategory_data["base_year"]
                        for i, year in enumerate(years_detected[1:], 1):
                            year_key = f"year_{i}"
                            if year_key in subcategory_data and subcategory_data[year_key] is not None:
                                year_data[year] = subcategory_data[year_key]
                        
                        all_line_items.append({
                            "Category": category.replace("_", " ").title(),
                            "Subcategory": "",
                            "Field": subcategory.replace("_", " ").title(),
                            "Value": subcategory_data["value"],
                            "Confidence": f"{subcategory_data['confidence']:.1%}",
                            "Confidence_Score": subcategory_data["confidence"],
                            "Year_Data": year_data
                        })
                        
                        # Display individual line item
                        if len(year_data) > 1:
                            # Multi-year display
                            st.write(f"**{subcategory.replace('_', ' ').title()}**")
                            year_cols = st.columns(min(len(year_data) + 1, 5))  # Limit to 5 columns
                            
                            with year_cols[0]:
                                confidence_class = get_confidence_class(subcategory_data["confidence"])
                                st.markdown(f'<span class="{confidence_class}">{subcategory_data["confidence"]:.1%}</span>', 
                                          unsafe_allow_html=True)
                            
                            for idx, (year, value) in enumerate(year_data.items(), 1):
                                if idx < len(year_cols):
                                    with year_cols[idx]:
                                        st.metric(str(year), f"{value:,.0f}" if value else "N/A")
                        else:
                            # Single year display
                            col1, col2, col3 = st.columns([3, 2, 1])
                            with col1:
                                st.write(f"**{subcategory.replace('_', ' ').title()}**")
                            with col2:
                                new_value = st.number_input(
                                    f"Value", 
                                    value=float(subcategory_data["value"]),
                                    key=f"edit_{category}_{subcategory}_{id(data)}",
                                    format="%.2f",
                                    label_visibility="collapsed"
                                )
                            with col3:
                                confidence_class = get_confidence_class(subcategory_data["confidence"])
                                st.markdown(f'<span class="{confidence_class}">{subcategory_data["confidence"]:.1%}</span>', 
                                          unsafe_allow_html=True)
        
        st.markdown("---")
    
    # Create comprehensive dataframe for export
    if all_line_items:
        df = pd.DataFrame(all_line_items)
        
        # Notes
        if data.get("notes"):
            st.subheader("📝 Notes")
            st.info(data["notes"])
        
        # Export options
        st.subheader("📤 Export Data")
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV Export
            detailed_csv = df.to_csv(index=False)
            st.download_button(
                label="📄 Download Detailed CSV",
                data=detailed_csv,
                file_name=f"financial_data_detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key=f"download_detailed_csv_{abs(hash(str(data))) % 10000}"
            )
        
        with col2:
            # Summary CSV (just key metrics)
            if summary_metrics:
                summary_df = pd.DataFrame([
                    {"Metric": k.replace("_", " ").title(), "Value": v.get("value", 0), "Confidence": f"{v.get('confidence', 0):.1%}"}
                    for k, v in summary_metrics.items() if v and v.get("value") is not None
                ])
                summary_csv = summary_df.to_csv(index=False)
                st.download_button(
                    label="📈 Download Summary CSV",
                    data=summary_csv,
                    file_name=f"financial_data_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key=f"download_summary_csv_{abs(hash(str(data))) % 10000}"
                )
        
        # Show data quality metrics
        st.subheader("📈 Data Quality")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_fields = len(all_line_items)
            st.metric("Total Line Items", total_fields)
        
        with col2:
            high_confidence = len([item for item in all_line_items if item["Confidence_Score"] >= 0.8])
            st.metric("High Confidence Items", f"{high_confidence}/{total_fields}")
        
        with col3:
            avg_confidence = sum(item["Confidence_Score"] for item in all_line_items) / len(all_line_items)
            st.metric("Average Confidence", f"{avg_confidence:.1%}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        return df
    else:
        st.warning("No financial line items could be extracted from this page.")
        return None

def classify_financial_statement_pages(page_info, enable_parallel=True):
    """Enhanced classification with universal patterns, number density scoring, and case-insensitive matching"""
    st.subheader("🎯 Enhanced Financial Statement Detection")
    st.info("🔍 **Enhanced Detection**: Using universal patterns + **high-weight number density analysis** for superior accuracy")
    
    financial_pages = []
    
    # Enhanced universal patterns (case-insensitive)
    statement_patterns = {
        'Balance Sheet': [
            r'statement of financial position',
            r'balance sheet',
            r'statement of position',
            r'financial position'
        ],
        'Income Statement': [
            r'statement of comprehensive income',
            r'income statement',
            r'profit and loss',
            r'statement of operations',
            r'statement of earnings',
            r'comprehensive income'
        ],
        'Cash Flow Statement': [
            r'statement of cash flows',
            r'cash flow statement',
            r'statement of cash flow',
            r'cash flows'
        ],
        'Statement of Equity': [
            r'statement of changes in equity',
            r'statement of equity',
            r'changes in equity',
            r'equity statement',
            r'statement of stockholders.? equity'
        ]
    }
    
    # Enhanced line item patterns (case-insensitive)
    line_item_patterns = {
        'Balance Sheet': [
            r'current assets', r'non.?current assets', r'total assets',
            r'current liabilities', r'non.?current liabilities', r'total liabilities',
            r'shareholders.? equity', r'retained earnings', r'share capital',
            r'cash and cash equivalents', r'accounts receivable', r'inventory',
            r'property.? plant.? equipment', r'accounts payable', r'long.?term debt'
        ],
        'Income Statement': [
            r'revenue', r'net sales', r'gross profit', r'operating income',
            r'net income', r'earnings per share', r'cost of goods sold',
            r'operating expenses', r'interest expense', r'income tax',
            r'other comprehensive income', r'basic earnings per share'
        ],
        'Cash Flow Statement': [
            r'cash flows from operating activities', r'cash flows from investing activities',
            r'cash flows from financing activities', r'net increase.? in cash',
            r'depreciation and amortization', r'changes in working capital',
            r'capital expenditures', r'dividends paid', r'proceeds from borrowings'
        ],
        'Statement of Equity': [
            r'beginning balance', r'ending balance', r'comprehensive income',
            r'dividends declared', r'share issuance', r'treasury shares',
            r'appropriated', r'unappropriated', r'retained earnings'
        ]
    }
    
    # Supporting indicators (case-insensitive)
    supporting_indicators = [
        r'with comparative figures', r'see notes to', r'notes to financial statements',
        r'audited', r'unaudited', r'management.?s discussion',
        r'for the year ended', r'as of', r'december 31', r'march 31',
        r'amounts in', r'thousands', r'millions', r'philippine peso',
        r'us dollars', r'consolidated', r'parent company'
    ]
    
    def classify_single_page(page_data):
        """Classify a single page - designed for parallel execution"""
        page, page_index, total_pages = page_data
        try:
            page_num = page['page_num']
            page_text = page['text'].lower()  # Convert to lowercase for case-insensitive matching
            
            # Calculate number density score
            number_density_score, number_density, financial_numbers = calculate_number_density_score(page['text'])
            financial_numbers_count = len(financial_numbers)
            sample_numbers = financial_numbers[:5]  # Get first 5 for display
            
            # Score each statement type
            statement_scores = {}
            all_matches = {}
            
            for stmt_type, patterns in statement_patterns.items():
                score = 0
                matches_found = []
                
                # Statement title patterns (high weight)
                for pattern in patterns:
                    matches = re.findall(pattern, page_text, re.IGNORECASE)
                    if matches:
                        score += 5.0 * len(matches)
                        matches_found.extend([f"Title: '{match}'" for match in matches])
                
                # Line item patterns (medium weight)
                for pattern in line_item_patterns[stmt_type]:
                    matches = re.findall(pattern, page_text, re.IGNORECASE)
                    if matches:
                        score += 2.0 * len(matches)
                        matches_found.extend([f"Line: '{match}'" for match in matches])
                
                # Supporting indicators (low weight)
                for pattern in supporting_indicators:
                    matches = re.findall(pattern, page_text, re.IGNORECASE)
                    if matches:
                        score += 1.0 * len(matches)
                        matches_found.extend([f"Support: '{match}'" for match in matches])
                
                # Add number density score (enhanced weight)
                score += number_density_score
                
                statement_scores[stmt_type] = score
                all_matches[stmt_type] = matches_found
            
            # Determine classification - find the highest scoring statement type
            max_score = max(statement_scores.values())
            
            # ENHANCED THRESHOLD - Adjusted for higher number density weights
            if max_score >= 3.0:
                # Find which statement type has the highest score
                statement_type = max(statement_scores.keys(), key=lambda k: statement_scores[k])
                
                return {
                    'page_num': page_num,
                    'statement_type': statement_type,
                    'confidence': max_score,
                    'number_density': number_density,
                    'financial_numbers_count': financial_numbers_count,
                    'number_density_score': number_density_score,
                    'image': page['image'],
                    'text': page['text'],  # Keep original text for processing
                    'classified': True,
                    'statement_scores': statement_scores,
                    'matches': all_matches,
                    'sample_numbers': sample_numbers,
                    'index': page_index
                }
            else:
                return {
                    'page_num': page_num,
                    'classified': False,
                    'max_score': max_score,
                    'number_density': number_density,
                    'financial_numbers_count': financial_numbers_count,
                    'number_density_score': number_density_score,
                    'statement_scores': statement_scores,
                    'matches': all_matches,
                    'sample_numbers': sample_numbers,
                    'index': page_index
                }
                
        except Exception as e:
            return {
                'page_num': page.get('page_num', page_index + 1),
                'classified': False,
                'error': str(e),
                'index': page_index
            }
    
    if enable_parallel and len(page_info) > 3:
        # Use parallel processing for classification
        st.info(f"🚀 Starting parallel classification with 10 workers for {len(page_info)} pages...")
        
        classification_progress = st.progress(0)
        classification_status = st.empty()
        
        # Use ThreadPoolExecutor for parallel classification
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Prepare page data with indices
            page_data_list = [(page, i, len(page_info)) for i, page in enumerate(page_info)]
            
            # Submit all pages for classification
            future_to_page = {executor.submit(classify_single_page, page_data): page_data[1] 
                             for page_data in page_data_list}
            
            # Collect results as they complete
            results = {}
            classified_count = 0
            
            for future in as_completed(future_to_page):
                page_index = future_to_page[future]
                try:
                    result = future.result()
                    results[result['index']] = result
                    
                    if result.get('classified', False):
                        classified_count += 1
                    
                    progress = len(results) / len(page_info)
                    classification_progress.progress(progress)
                    classification_status.text(f"📊 Classified page {result['page_num']} ({classified_count} financial pages found, {len(results)}/{len(page_info)} completed)")
                    
                except Exception as e:
                    st.error(f"❌ Error classifying page {page_index + 1}: {str(e)}")
        
        # Sort results by original page order and process
        for page_index in sorted(results.keys()):
            result = results[page_index]
            
            if result.get('error'):
                st.error(f"❌ Error processing page {result['page_num']}: {result['error']}")
                continue
            
            page_num = result['page_num']
            
            # Show detailed analysis in expander
            with st.expander(f"📄 Page {page_num} Analysis", expanded=False):
                st.write(f"**Text length**: {len(result.get('text', ''))} characters")
                
                # Display number density analysis
                number_density = result.get('number_density', 0)
                financial_numbers_count = result.get('financial_numbers_count', 0)
                number_density_score = result.get('number_density_score', 0)
                sample_numbers = result.get('sample_numbers', [])
                
                density_color = "🟢" if number_density >= 40 else "🟡" if number_density >= 25 else "🔴"
                st.write(f"**Number Density**: {density_color} {number_density:.1f}% ({financial_numbers_count} numbers) → Score: {number_density_score:+.1f}")
                
                if sample_numbers:
                    st.write(f"**Sample Numbers**: {', '.join(sample_numbers)}")
                
                # Show statement scores
                statement_scores = result.get('statement_scores', {})
                matches = result.get('matches', {})
                
                for stmt_type, score in statement_scores.items():
                    if score > 0:
                        st.write(f"**{stmt_type}**: {score:.1f} points")
                        stmt_matches = matches.get(stmt_type, [])
                        if stmt_matches:
                            st.write(f"  • Matches: {', '.join(stmt_matches[:3])}")
                            if len(stmt_matches) > 3:
                                st.write(f"  • ... and {len(stmt_matches) - 3} more")
            
            if result.get('classified', False):
                st.success(f"🎯 **Page {page_num} Classified as:** {result['statement_type']} (score: {result['confidence']:.1f})")
                financial_pages.append(result)
            else:
                max_score = result.get('max_score', 0)
                st.info(f"📄 **Page {page_num} Not classified** as financial statement (max score: {max_score:.1f})")
        
        # Clear progress indicators
        classification_progress.progress(1.0)
        classification_progress.empty()
        classification_status.empty()
        
        st.success(f"🎯 **Parallel Classification Complete**: {classified_count}/{len(page_info)} pages classified as financial statements")
        
    else:
        # Sequential processing for small documents or when parallel is disabled
        st.info("📊 Processing pages sequentially...")
        
        for page in page_info:
            page_num = page['page_num']
            page_text = page['text'].lower()  # Convert to lowercase for case-insensitive matching
            
            with st.expander(f"📄 Page {page_num} Analysis", expanded=False):
                st.write(f"**Text length**: {len(page_text)} characters")
                
                # Calculate number density score
                number_density_score, number_density, financial_numbers = calculate_number_density_score(page['text'])
                financial_numbers_count = len(financial_numbers)
                sample_numbers = financial_numbers[:5]  # Get first 5 for display
                
                # Display number density analysis
                density_color = "🟢" if number_density >= 40 else "🟡" if number_density >= 25 else "🔴"
                st.write(f"**Number Density**: {density_color} {number_density:.1f}% ({financial_numbers_count} numbers) → Score: {number_density_score:+.1f}")
                
                if sample_numbers:
                    st.write(f"**Sample Numbers**: {', '.join(sample_numbers)}")
                
                # Score each statement type
                statement_scores = {}
                
                for stmt_type, patterns in statement_patterns.items():
                    score = 0
                    matches_found = []
                    
                    # Statement title patterns (high weight)
                    for pattern in patterns:
                        matches = re.findall(pattern, page_text, re.IGNORECASE)
                        if matches:
                            score += 5.0 * len(matches)
                            matches_found.extend([f"Title: '{match}'" for match in matches])
                    
                    # Line item patterns (medium weight)
                    for pattern in line_item_patterns[stmt_type]:
                        matches = re.findall(pattern, page_text, re.IGNORECASE)
                        if matches:
                            score += 2.0 * len(matches)
                            matches_found.extend([f"Line: '{match}'" for match in matches])
                    
                    # Supporting indicators (low weight)
                    for pattern in supporting_indicators:
                        matches = re.findall(pattern, page_text, re.IGNORECASE)
                        if matches:
                            score += 1.0 * len(matches)
                            matches_found.extend([f"Support: '{match}'" for match in matches])
                    
                    # Add number density score (enhanced weight)
                    score += number_density_score
                    
                    statement_scores[stmt_type] = score
                    
                    if score > 0:
                        st.write(f"**{stmt_type}**: {score:.1f} points")
                        if matches_found:
                            st.write(f"  • Matches: {', '.join(matches_found[:3])}")
                            if len(matches_found) > 3:
                                st.write(f"  • ... and {len(matches_found) - 3} more")
            
            # Determine classification - find the highest scoring statement type
            max_score = max(statement_scores.values())
            
            # ENHANCED THRESHOLD - Adjusted for higher number density weights
            if max_score >= 3.0:
                # Find which statement type has the highest score
                statement_type = max(statement_scores.keys(), key=lambda k: statement_scores[k])
                
                st.success(f"🎯 **Classified as:** {statement_type} (score: {max_score:.1f})")
                
                financial_pages.append({
                    'page_num': page_num,
                    'statement_type': statement_type,
                    'confidence': max_score,
                    'number_density': number_density,
                    'financial_numbers_count': financial_numbers_count,
                    'number_density_score': number_density_score,
                    'image': page['image'],
                    'text': page['text']  # Keep original text for processing
                })
            else:
                st.info(f"📄 **Not classified** as financial statement (max score: {max_score:.1f})")
    
    # Show final ranking with enhanced details
    if financial_pages:
        st.subheader("🏆 Final Page Rankings - Enhanced Scoring System")
        st.info("📊 **New Scoring**: Number density now weighted 3x higher (up to ±6 points) for better discrimination")
        ranking_data = []
        for i, page in enumerate(financial_pages[:15], 1):  # Show top 15
            score = page.get('confidence', 0)
            stmt_type = page.get('statement_type', 'Unknown')
            page_num = page.get('page_num', 'Unknown')
            number_density = page.get('number_density', 0)
            numbers_count = page.get('financial_numbers_count', 0)
            density_score = page.get('number_density_score', 0)
            
            # Create density indicator
            if number_density >= 40:
                density_indicator = f"🟢 {number_density:.1f}%"
            elif number_density >= 25:
                density_indicator = f"🟡 {number_density:.1f}%"
            else:
                density_indicator = f"🔴 {number_density:.1f}%"
            
            ranking_data.append({
                "Rank": i,
                "Page": page_num,
                "Statement Type": stmt_type,
                "Total Score": f"{score:.1f}",
                "Number Density": density_indicator,
                "Numbers Found": numbers_count,
                "Density Score": f"{density_score:+.1f}"
            })
        
        ranking_df = pd.DataFrame(ranking_data)
        st.dataframe(ranking_df, use_container_width=True)
        
        # Show statistics
        avg_density = sum(page.get('number_density', 0) for page in financial_pages) / len(financial_pages)
        high_density_pages = sum(1 for page in financial_pages if page.get('number_density', 0) >= 40)
        
        st.info(f"📈 **Statistics**: {len(financial_pages)} pages classified | Average density: {avg_density:.1f}% | High-density pages: {high_density_pages}")
    
    return financial_pages

def calculate_number_density_score(page_text):
    """Calculate enhanced number density score for financial statement detection with higher weights"""
    # Smart financial number detection
    # Matches: currency amounts, large numbers (3+ digits), percentages, formatted numbers
    financial_number_patterns = [
        r'[\$₱€£¥¢][\d,]+\.?\d*',  # Currency amounts: $1,000.00, ₱500,000
        r'\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b',  # Comma-separated numbers: 1,000,000.50
        r'\b\d{4,}(?:\.\d+)?\b',  # Large numbers without commas: 50000, 1000000.5
        r'\(\d{1,3}(?:,\d{3})+(?:\.\d+)?\)',  # Negative numbers in parentheses: (1,000.00)
        r'\(\d{4,}(?:\.\d+)?\)',  # Negative large numbers: (50000)
        r'\b\d+\.?\d*%\b',  # Percentages: 15.5%, 20%
    ]
    
    # Find all financial numbers
    financial_numbers = []
    for pattern in financial_number_patterns:
        matches = re.findall(pattern, page_text)
        financial_numbers.extend(matches)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_financial_numbers = []
    for num in financial_numbers:
        if num not in seen:
            seen.add(num)
            unique_financial_numbers.append(num)
    
    # Calculate density metrics
    total_chars = len(page_text)
    total_words = len(page_text.split())
    number_count = len(unique_financial_numbers)
    
    # Calculate number density as percentage
    if total_words > 0:
        number_density_pct = (number_count / total_words) * 100
    else:
        number_density_pct = 0
    
    # ENHANCED SCORING SYSTEM - Much higher weights for better discrimination
    if number_density_pct >= 30:      # Very high density - extremely strong financial statement signal
        density_score = 6.0
    elif number_density_pct >= 20:    # High density - very strong signal
        density_score = 4.0
    elif number_density_pct >= 15:    # Medium-high density - strong signal
        density_score = 2.5
    elif number_density_pct >= 10:    # Medium density - moderate signal
        density_score = 1.5
    elif number_density_pct >= 7:     # Low-medium density - slight positive
        density_score = 0.5
    elif number_density_pct >= 5:     # Low density - neutral
        density_score = 0.0
    elif number_density_pct >= 3:     # Very low density - slight negative
        density_score = -1.0
    else:                             # Extremely low density - strong negative (narrative text)
        density_score = -3.0
    
    return density_score, number_density_pct, unique_financial_numbers

def extract_comprehensive_financial_data(base64_image, statement_type_hint, page_text=""):
    """Guided adaptive financial data extraction that balances structure with flexibility - thread-safe version"""
    content = ""  # Initialize content variable
    try:
        # Revised prompt with clear guidance but flexible implementation
        prompt = f"""
        You are a financial data extraction expert. Analyze this {statement_type_hint} and extract ALL visible financial line items.

        CORE EXTRACTION RULE: Extract every line that has both a LABEL and a NUMERICAL VALUE.

        STEP-BY-STEP PROCESS:
        1. SCAN the entire document for lines with labels and numbers
        2. IDENTIFY the document's own section headers and organization
        3. EXTRACT using the exact terminology from the document
        4. ORGANIZE into logical categories based on the document's structure
        5. FORMAT using the JSON structure below

        CURRENCY AND NUMBER HANDLING:
        - Handle all currency symbols (₱, $, €, £, ¥, etc.)
        - Parse parentheses as NEGATIVE numbers: ₱(26,278) = -26278
        - Handle comma-separated numbers: ₱249,788,478 = 249788478
        - Remove currency symbols and return just numeric values
        - If no clear number, set value to null and confidence to 0.1

        YEAR HANDLING (RELATIVE APPROACH):
        - Identify ALL years present in columns
        - Use relative positioning: base_year (leftmost/primary), year_1, year_2, year_3
        - Record actual years found for reference
        - Only include year fields that have actual data

        REQUIRED JSON STRUCTURE (adapt field names to match document):
        {{
            "statement_type": "exact statement title from document",
            "company_name": "extracted company name",
            "period": "extracted period/date", 
            "currency": "extracted currency (PHP, USD, etc.)",
            "years_detected": ["2024", "2023", "2022"],  // actual years found
            "base_year": "2024",  // leftmost/primary year
            "year_ordering": "most_recent_first" or "chronological",
            
            "line_items": {{
                // ADAPT these category names to match the document's structure
                // Examples for different statement types:
                
                // FOR BALANCE SHEETS - use document's section names:
                "current_assets": {{
                    "cash_and_equivalents": {{"value": 1000000, "confidence": 0.95, "base_year": 1000000, "year_1": 950000}},
                    "accounts_receivable": {{"value": 500000, "confidence": 0.90, "base_year": 500000, "year_1": 480000}},
                    "inventory": {{"value": 300000, "confidence": 0.85, "base_year": 300000, "year_1": 290000}}
                }},
                "non_current_assets": {{
                    "property_plant_equipment": {{"value": 2000000, "confidence": 0.92, "base_year": 2000000, "year_1": 1900000}}
                }},
                "current_liabilities": {{
                    "accounts_payable": {{"value": 400000, "confidence": 0.88, "base_year": 400000, "year_1": 380000}}
                }},
                "equity": {{
                    "share_capital": {{"value": 1000000, "confidence": 0.95, "base_year": 1000000, "year_1": 1000000}},
                    "retained_earnings": {{"value": 800000, "confidence": 0.90, "base_year": 800000, "year_1": 750000}}
                }},
                
                // FOR INCOME STATEMENTS - use document's section names:
                "revenues": {{
                    "net_sales": {{"value": 5000000, "confidence": 0.95, "base_year": 5000000, "year_1": 4800000}},
                    "other_income": {{"value": 100000, "confidence": 0.80, "base_year": 100000, "year_1": 95000}}
                }},
                "cost_of_sales": {{
                    "cost_of_goods_sold": {{"value": 3000000, "confidence": 0.92, "base_year": 3000000, "year_1": 2900000}}
                }},
                "operating_expenses": {{
                    "selling_expenses": {{"value": 500000, "confidence": 0.88, "base_year": 500000, "year_1": 480000}},
                    "administrative_expenses": {{"value": 300000, "confidence": 0.85, "base_year": 300000, "year_1": 290000}}
                }},
                
                // FOR CASH FLOW STATEMENTS - use document's section names:
                "operating_activities": {{
                    "net_income": {{"value": 1200000, "confidence": 0.95, "base_year": 1200000, "year_1": 1100000}},
                    "depreciation": {{"value": 200000, "confidence": 0.90, "base_year": 200000, "year_1": 190000}}
                }},
                "investing_activities": {{
                    "capital_expenditures": {{"value": -500000, "confidence": 0.88, "base_year": -500000, "year_1": -450000}}
                }},
                "financing_activities": {{
                    "dividends_paid": {{"value": -100000, "confidence": 0.85, "base_year": -100000, "year_1": -95000}}
                }}
            }},
            
            "summary_metrics": {{
                // Key totals for quick overview
                "total_assets": {{"value": 3000000, "confidence": 0.95}},
                "total_liabilities": {{"value": 1200000, "confidence": 0.90}},
                "total_equity": {{"value": 1800000, "confidence": 0.92}},
                "total_revenue": {{"value": 5100000, "confidence": 0.95}},
                "net_income": {{"value": 1200000, "confidence": 0.93}},
                "operating_cash_flow": {{"value": 1400000, "confidence": 0.88}}
            }},
            
            "document_structure": {{
                "main_sections": ["Assets", "Liabilities", "Equity"],  // actual section headers found
                "line_item_count": 15,  // total line items extracted
                "has_multi_year_data": true,
                "special_notes": "any unique aspects of this document"
            }},
            
            "notes": "observations about document structure, data quality, assumptions made"
        }}

        CRITICAL EXTRACTION GUIDELINES:

        1. **EXTRACT EVERYTHING**: Every line with a label and number should be captured
        2. **USE EXACT NAMES**: Convert document terminology to snake_case for JSON keys
           - "Cash and Cash Equivalents" → "cash_and_cash_equivalents"
           - "Accounts Receivable - Net" → "accounts_receivable_net"
           - "Property, Plant & Equipment" → "property_plant_equipment"
        
        3. **ADAPT CATEGORIES**: Use the document's own section organization
           - If document has "Current Assets" and "Non-Current Assets", use those
           - If document has "Operating Revenue" and "Non-Operating Revenue", use those
           - Don't force items into predefined categories if they don't fit
        
        4. **HANDLE TOTALS**: Always extract subtotals and grand totals
           - "Total Current Assets", "Total Assets", "Total Revenue", etc.
        
        5. **CONFIDENCE SCORING**:
           - 0.9-1.0: Crystal clear, unambiguous values
           - 0.7-0.9: Clear values with minor formatting complexity  
           - 0.5-0.7: Somewhat unclear but reasonable interpretation
           - 0.3-0.5: Uncertain, multiple possible interpretations
           - 0.1-0.3: Very uncertain or barely visible

        6. **MULTI-YEAR DATA**: If multiple years are present:
           - Identify the base year (usually leftmost or most recent)
           - Extract data for year_1, year_2, year_3 as available
           - Only include year fields that have actual data

        7. **FALLBACK APPROACH**: If document structure is unusual:
           - Create a "miscellaneous" or "other_items" category
           - Still extract all visible line items
           - Note the unusual structure in the "notes" field

        EXAMPLES OF ADAPTIVE EXTRACTION:

        Document shows: "Cash and Bank Deposits    ₱1,000,000    ₱950,000"
        Extract as: "cash_and_bank_deposits": {{"value": 1000000, "confidence": 0.95, "base_year": 1000000, "year_1": 950000}}

        Document shows: "Total Stockholders' Equity    $5,000,000"  
        Extract as: "total_stockholders_equity": {{"value": 5000000, "confidence": 0.95, "base_year": 5000000}}

        Document shows: "Cost of Sales    (2,000,000)"
        Extract as: "cost_of_sales": {{"value": -2000000, "confidence": 0.95, "base_year": -2000000}}

        REMEMBER: Your goal is to capture ALL financial data visible in the document while preserving the document's own terminology and organization. Be thorough but accurate.
        """

        response = exponential_backoff_retry(
            lambda: client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4000
            )
        )

        # Parse the JSON response
        content = response.choices[0].message.content or ""
        
        if not content:
            raise Exception("Empty response from AI model")
        
        # Extract JSON from the response
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            raise Exception("No valid JSON found in AI response")
            
        json_str = content[start_idx:end_idx]
        extracted_data = json.loads(json_str)
        
        # Add processing metadata
        extracted_data['processing_method'] = 'vector_database_analysis'
        
        return extracted_data
        
    except json.JSONDecodeError as e:
        raise Exception(f"JSON parsing error: {str(e)}")
        
    except Exception as e:
        raise Exception(f"Error in comprehensive extraction: {str(e)}")

# Initialize ChromaDB client
@st.cache_resource
def init_chromadb():
    """Initialize ChromaDB client with persistent storage"""
    try:
        # Option for financial-specific embeddings (can be enabled later)
        use_financial_embeddings = os.getenv("USE_FINANCIAL_EMBEDDINGS", "false").lower() == "true"
        
        if use_financial_embeddings:
            # Financial-specific embedding options:
            # 1. FinBERT-based embeddings
            # 2. Financial sentence transformers
            # 3. Custom financial domain models
            
            try:
                from sentence_transformers import SentenceTransformer
                
                # Example: Use a financial domain model
                # financial_model = SentenceTransformer('ProsusAI/finbert')
                # OR: financial_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2-financial')
                
                st.info("🏦 Using financial-specific embeddings for enhanced accuracy")
                # Would need to configure ChromaDB with custom embedding function
                # embedding_function = SentenceTransformerEmbeddingFunction(model_name='ProsusAI/finbert')
                
            except ImportError:
                st.warning("⚠️ Financial embeddings requested but sentence-transformers not available. Using default embeddings.")
                use_financial_embeddings = False
        
        # Create a persistent client
        client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        if use_financial_embeddings:
            st.sidebar.success("🏦 Financial embeddings enabled")
        else:
            st.sidebar.info("🔤 Using general-purpose embeddings")
            
        return client
    except Exception as e:
        st.error(f"Failed to initialize ChromaDB: {e}")
        return None

def create_or_get_collection(client, collection_name="financial_statements"):
    """Create or get a ChromaDB collection"""
    try:
        # Try to get existing collection
        collection = client.get_collection(name=collection_name)
    except:
        # Create new collection if it doesn't exist
        collection = client.create_collection(
            name=collection_name,
            metadata={"description": "Financial statement pages and content"}
        )
    return collection

def analyze_page_content_semantically(collection, page_text, page_num, threshold=0.15):
    """Use vector database to semantically analyze if a page contains actual financial statement content"""
    if not page_text or len(page_text.strip()) < 20:
        st.warning(f"Page {page_num}: Insufficient text content ({len(page_text)} chars)")
        return False, 0.0, "Insufficient text content"
    
    # Debug: Show what text we're working with
    st.write(f"**Page {page_num} Debug Info:**")
    st.write(f"- Text length: {len(page_text)} characters")
    st.write(f"- First 200 chars: {page_text[:200]}...")
    
    try:
        # Enhanced approach: Use both semantic search AND keyword analysis
        
        # 1. SEMANTIC SEARCH: Query for financial statement types with comprehensive terminology
        financial_queries = [
            # Balance Sheet - comprehensive IFRS and US GAAP terms
            "balance sheet statements financial position consolidated assets liabilities equity current non-current",
            
            # Income Statement - ALL variations including "Statement of Operations"
            "income statement statements operations consolidated profit loss revenue expenses comprehensive earnings operating",
            
            # Cash Flow - comprehensive terms including plural forms
            "cash flow statement statements flows consolidated operating investing financing activities sources uses funds",
            
            # Equity - comprehensive terms for equity statements
            "statement equity changes shareholders stockholders retained earnings consolidated net assets owners"
        ]
        
        semantic_scores = []
        statement_types = ["Balance Sheet", "Income Statement", "Cash Flow Statement", "Statement of Equity"]
        
        for query, stmt_type in zip(financial_queries, statement_types):
            try:
                # Query the vector database for semantic similarity
                results = collection.query(
                    query_texts=[query],
                    n_results=min(5, collection.count()),  # Get top 5 similar documents
                    include=['documents', 'distances', 'metadatas']
                )
                
                # Check if current page content is similar to financial statements
                if results['documents'] and results['distances']:
                    # Find the best similarity score for this query
                    min_distance = min(results['distances'][0]) if results['distances'][0] else 1.0
                    similarity_score = 1.0 - min_distance  # Convert distance to similarity
                    semantic_scores.append((stmt_type, similarity_score))
                    
                    st.write(f"- {stmt_type} semantic similarity: {similarity_score:.3f}")
                else:
                    semantic_scores.append((stmt_type, 0.0))
                    
            except Exception as e:
                st.warning(f"Semantic search failed for {stmt_type}: {e}")
                semantic_scores.append((stmt_type, 0.0))
        
        # 2. KEYWORD ANALYSIS (Enhanced with comprehensive terminology)
        financial_keywords = [
            # Core financial terms
            'assets', 'liabilities', 'equity', 'revenue', 'expenses', 'net income',
            'cash flow', 'balance sheet', 'income statement', 'profit', 'loss',
            'financial position', 'operations', 'investing', 'financing',
            'current assets', 'non-current', 'stockholders', 'retained earnings',
            'total assets', 'total liabilities', 'gross profit', 'operating income',
            'consolidated',
            
            # Income Statement variations (KEY: Statement of Operations)
            'statement of operations', 'statements of operations', 
            'consolidated statement of operations', 'consolidated statements of operations',
            'statement of comprehensive income', 'profit and loss statement',
            'earnings statement', 'statement of earnings',
            
            # Balance Sheet variations
            'statement of financial position', 'statements of financial position',
            'consolidated statement of financial position', 'consolidated statements of financial position',
            'balance sheets', 'consolidated balance sheet', 'consolidated balance sheets',
            
            # Cash Flow variations
            'statement of cash flows', 'statements of cash flows',
            'consolidated statement of cash flows', 'consolidated statements of cash flows',
            'cash flows statement', 'cashflows', 'sources and uses',
            
            # Equity variations
            'statement of changes in equity', 'statements of changes in equity',
            'consolidated statement of changes in equity', 'shareholders equity',
            'stockholders equity', 'changes in equity', 'owners equity'
        ]
        
        page_text_lower = page_text.lower()
        
        # Count keyword matches with weights
        keyword_matches = []
        for keyword in financial_keywords:
            if keyword in page_text_lower:
                keyword_matches.append(keyword)
        
        
        st.write(f"- Found keywords: {keyword_matches[:5]}{'...' if len(keyword_matches) > 5 else ''}")
        
        # 3. NUMERICAL ANALYSIS
        import re
        numbers = re.findall(r'\$?[\d,]+\.?\d*', page_text)
        financial_numbers = [n for n in numbers if len(n.replace(',', '').replace('$', '').replace('.', '')) >= 3]
        
        st.write(f"- Found {len(financial_numbers)} financial numbers: {financial_numbers[:3]}{'...' if len(financial_numbers) > 3 else ''}")
        
        # 4. COMBINED SCORING
        # Semantic score (weighted heavily)
        best_semantic = max(semantic_scores, key=lambda x: x[1]) if semantic_scores else ("Unknown", 0.0)
        semantic_score = best_semantic[1] * 0.6  # 60% weight
        
        # Keyword score
        keyword_score = (len(keyword_matches) / len(financial_keywords)) * 0.3  # 30% weight
        
        # Number score
        number_score = min(len(financial_numbers) / 10, 0.1)  # 10% weight, capped
        
        # Final confidence
        confidence = semantic_score + keyword_score + number_score
        
        st.write(f"- Semantic score: {semantic_score:.3f}, Keyword score: {keyword_score:.3f}, Number score: {number_score:.3f}")
        st.write(f"- **Total confidence: {confidence:.3f}**")
        
        # Determine if this looks like a financial statement
        is_financial = confidence > threshold
        
        # Determine statement type (prefer semantic result if confident)
        if best_semantic[1] > 0.3:  # High semantic confidence
            statement_type = best_semantic[0]
        else:
            # Fall back to keyword-based detection
            if any(term in page_text_lower for term in ['balance sheet', 'financial position', 'statement of financial position']):
                statement_type = "Balance Sheet"
            elif any(term in page_text_lower for term in ['income statement', 'statement of operations', 'statements of operations', 'profit and loss']):
                statement_type = "Income Statement"
            elif any(term in page_text_lower for term in ['cash flow', 'statement of cash flows']):
                statement_type = "Cash Flow Statement"
            elif any(term in page_text_lower for term in ['equity', 'retained earnings', 'stockholders']):
                statement_type = "Statement of Equity"
            elif is_financial:
                statement_type = "Financial Statement"
            else:
                statement_type = "Unknown"
        
        st.write(f"- **Result: {'✅ FINANCIAL' if is_financial else '❌ NOT FINANCIAL'}** ({statement_type}, confidence: {confidence:.3f})")
        
        # Add this page to the collection for future comparisons
        try:
            collection.add(
                documents=[page_text[:1000]],  # Limit text length
                metadatas=[{
                    "page_number": page_num,
                    "content_type": "financial_page" if is_financial else "other_page",
                    "statement_type": statement_type,
                    "confidence": confidence,
                    "semantic_score": semantic_score,
                    "keyword_score": keyword_score
                }],
                ids=[f"page_{page_num}_{int(time.time())}"]
            )
        except Exception as add_error:
            st.warning(f"Could not add page to vector database: {add_error}")
        
        return is_financial, confidence, statement_type
        
    except Exception as e:
        st.error(f"Error in semantic analysis: {e}")
        # Fallback to keyword-only analysis
        page_text_lower = page_text.lower()
        keyword_matches = [kw for kw in ['balance sheet', 'income statement', 'cash flow'] if kw in page_text_lower]
        confidence = len(keyword_matches) * 0.3
        is_financial = confidence > threshold
        return is_financial, confidence, "Unknown"

def process_pdf_with_vector_db(uploaded_file, client, enable_parallel=True):
    """Process PDF using comprehensive vector database approach for large documents"""
    try:
        st.info("🔍 Starting comprehensive PDF analysis with enhanced classification...")
        
        # Convert PDF to images and extract text from ALL pages
        images, page_info = convert_pdf_to_images(uploaded_file, enable_parallel)
        if not images or not page_info:
            return None

        st.info(f"📊 Analyzing {len(page_info)} pages with enhanced classification system...")
        
        # Use the NEW enhanced classification system instead of old semantic search
        financial_pages = classify_financial_statement_pages(page_info, enable_parallel)
        
        if not financial_pages:
            st.warning("⚠️ No financial statement pages detected. Processing first page as fallback.")
            financial_pages = [{
                'page_num': 1,
                'statement_type': 'Unknown',
                'confidence': 0.1,
                'image': images[0],
                'text': page_info[0]['text'] if page_info else "",
                'number_density': 0,
                'financial_numbers_count': 0,
                'number_density_score': 0
            }]

        # Sort by confidence and select top pages for processing
        def get_confidence_score(page_dict):
            confidence = page_dict.get('confidence', 0)
            if isinstance(confidence, (int, float)):
                return float(confidence)
            return 0.0

        financial_pages.sort(key=get_confidence_score, reverse=True)

        # Select top 10 pages for processing (optimization)
        max_pages_to_process = min(10, len(financial_pages))
        selected_pages = financial_pages[:max_pages_to_process]

        st.success(f"✅ Found {len(financial_pages)} financial statement pages using enhanced classification")

        # Show preview of selected pages before processing
        with st.expander(f"📋 Preview: Top {max_pages_to_process} Pages Selected for Processing", expanded=True):
            st.info(f"🚀 **Optimization**: Processing top {max_pages_to_process} highest-scoring pages instead of all {len(financial_pages)} pages for faster extraction.")
            
            preview_data = []
            for i, page in enumerate(selected_pages):
                preview_data.append({
                    "Rank": str(i + 1),
                    "Page": str(page['page_num']),
                    "Statement Type": page['statement_type'],
                    "Confidence": f"{page['confidence']:.3f}",
                    "Status": "✅ Will Process"
                })
            
            # Show skipped pages if any
            skipped_pages = financial_pages[max_pages_to_process:]
            for page in skipped_pages[:5]:  # Show first 5 skipped pages
                preview_data.append({
                    "Rank": "-",
                    "Page": str(page['page_num']),
                    "Statement Type": page['statement_type'],
                    "Confidence": f"{page['confidence']:.3f}",
                    "Status": "⏭️ Skipped"
                })
            
            if len(skipped_pages) > 5:
                preview_data.append({
                    "Rank": "-",
                    "Page": "More pages...",
                    "Statement Type": f"({len(skipped_pages) - 5} more)",
                    "Confidence": "...",
                    "Status": "⏭️ Skipped"
                })
            
            preview_df = pd.DataFrame(preview_data)
            st.dataframe(preview_df, use_container_width=True)
            
            # Show processing time estimate
            estimated_time = max_pages_to_process * 0.5  # Rough estimate: 30 seconds per page
            st.info(f"⏱️ **Estimated processing time**: ~{estimated_time:.1f} minutes (vs ~{len(financial_pages) * 0.5:.1f} minutes for all pages)")

        # Process selected pages for comprehensive extraction
        st.info("🚀 Starting parallel financial data extraction with 5 workers...")

        def extract_financial_data_for_page(page_data):
            """Extract financial data from a single page - designed for parallel execution"""
            page, page_index, total_pages = page_data
            try:
                # Enhanced debugging information
                page_num = page['page_num']
                page_text_length = len(page.get('text', ''))
                statement_type = page.get('statement_type', 'Unknown')
                confidence = page.get('confidence', 0)
                
                # Debug: Log what we're processing
                debug_info = {
                    'page_num': page_num,
                    'statement_type': statement_type,
                    'confidence': confidence,
                    'text_length': page_text_length,
                    'has_image': 'image' in page and page['image'] is not None,
                    'has_text': page_text_length > 0
                }
                
                # Validate inputs before processing
                if not page.get('image'):
                    return {
                        'page_num': str(page_num),
                        'data': None,
                        'success': False,
                        'error': 'No image data available',
                        'debug_info': debug_info,
                        'index': page_index
                    }
                
                if page_text_length < 10:
                    return {
                        'page_num': str(page_num),
                        'data': None,
                        'success': False,
                        'error': f'Insufficient text content ({page_text_length} chars)',
                        'debug_info': debug_info,
                        'index': page_index
                    }
                
                # Encode image for API call
                base64_image = encode_pil_image(page['image'])
                if not base64_image:
                    return {
                        'page_num': str(page_num),
                        'data': None,
                        'success': False,
                        'error': 'Failed to encode image',
                        'debug_info': debug_info,
                        'index': page_index
                    }
                
                # Make the API call with enhanced error handling
                page_result = extract_comprehensive_financial_data(
                    base64_image, 
                    statement_type, 
                    str(page.get('text', ''))
                )
                
                if page_result:
                    # Add metadata to successful result
                    page_result['page_number'] = str(page_num)
                    page_result['confidence_score'] = confidence
                    page_result['processing_debug'] = debug_info
                    
                    return {
                        'page_num': str(page_num),
                        'data': page_result,
                        'success': True,
                        'error': None,
                        'debug_info': debug_info,
                        'index': page_index
                    }
                else:
                    return {
                        'page_num': str(page_num),
                        'data': None,
                        'success': False,
                        'error': 'LLM returned empty/null result',
                        'debug_info': debug_info,
                        'index': page_index
                    }
                    
            except Exception as e:
                # Enhanced error reporting
                error_details = {
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'page_info': {
                        'page_num': page.get('page_num', 'Unknown'),
                        'has_image': 'image' in page,
                        'has_text': len(page.get('text', '')) > 0,
                        'text_preview': page.get('text', '')[:100] + '...' if len(page.get('text', '')) > 100 else page.get('text', '')
                    }
                }
                
                return {
                    'page_num': str(page.get('page_num', page_index + 1)),
                    'data': None,
                    'success': False,
                    'error': f"{type(e).__name__}: {str(e)}",
                    'error_details': error_details,
                    'index': page_index
                }
        
        # Create progress tracking
        extraction_progress = st.progress(0)
        extraction_status = st.empty()
        completed_count = 0
        total_pages = len(selected_pages)
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all pages for processing
            future_to_page = {executor.submit(extract_financial_data_for_page, page_data): page_data[0] 
                             for page_data in enumerate(selected_pages)}
            
            # Collect results as they complete
            results = {}
            failed_pages = []
            
            for future in as_completed(future_to_page):
                page_num = future_to_page[future]
                try:
                    result = future.result()
                    results[result['page_num']] = result
                    
                    if result['success']:
                        completed_count += 1
                        progress = completed_count / total_pages
                        extraction_progress.progress(progress)
                        extraction_status.text(f"✅ Completed page {result['page_num']}/{total_pages} ({completed_count} successful)")
                    else:
                        failed_pages.append(result['page_num'])
                        st.warning(f"⚠️ Failed to extract data from page {result['page_num']}: {result['error']}")
                        
                except Exception as e:
                    failed_pages.append(page_num + 1)
                    st.error(f"❌ Unexpected error processing page {page_num + 1}: {str(e)}")
        
        # Sort results by page number and create page_info list
        for page_num in sorted(results.keys()):
            result = results[page_num]
            if result['success']:
                page_info.append({
                    'page_num': result['page_num'],
                    'text': result['text'],
                    'image': result['image']
                })
        
        # Final status update
        extraction_progress.progress(1.0)
        if failed_pages:
            st.warning(f"⚠️ Processing completed with {len(failed_pages)} failed pages: {failed_pages}")
            st.info(f"✅ Successfully processed {len(page_info)}/{total_pages} pages with parallel AI text extraction")
        else:
            st.success(f"✅ Successfully processed all {len(page_info)} pages with parallel AI text extraction")
        
        # Clear progress indicators
        extraction_progress.empty()
        extraction_status.empty()
        
        return images, page_info
        
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        if "poppler" in str(e).lower():
            st.error("💡 This looks like a Poppler installation issue. Please see the instructions above.")
        return None, None

def create_ifrs_csv_export(data):
    """Create comprehensive CSV export for IFRS financial statements"""
    rows = []
    
    # Helper function to add rows
    def add_section_rows(section_name, section_data, parent_category=""):
        if not isinstance(section_data, dict):
            return
            
        for field, info in section_data.items():
            if isinstance(info, dict):
                if "value" in info:
                    # This is a line item
                    row = {
                        "Statement": section_name,
                        "Category": parent_category,
                        "Line_Item": field.replace("_", " ").title(),
                        "Value": info.get("value", ""),
                        "Confidence": f"{info.get('confidence', 0):.1%}",
                        "Base_Year": info.get("base_year", ""),
                        "Year_1": info.get("year_1", ""),
                        "Year_2": info.get("year_2", ""),
                        "Year_3": info.get("year_3", "")
                    }
                    rows.append(row)
                else:
                    # This is a subcategory
                    add_section_rows(section_name, info, field.replace("_", " ").title())
    
    # Process each statement
    statements = [
        ("Balance Sheet", "balance_sheet"),
        ("Income Statement", "income_statement"), 
        ("Cash Flow Statement", "cash_flow_statement"),
        ("Statement of Changes in Equity", "statement_of_changes_in_equity")
    ]
    
    for statement_name, statement_key in statements:
        statement_data = data.get(statement_key, {})
        add_section_rows(statement_name, statement_data)
    
    # Convert to DataFrame and CSV
    if rows:
        df = pd.DataFrame(rows)
        return df.to_csv(index=False)
    else:
        return "No data available for export"

def consolidate_financial_data(extracted_results):
    """
    Use LLM to intelligently consolidate multiple financial statement extractions
    into a single, comprehensive, and accurate financial statement.
    """
    if not extracted_results or len(extracted_results) <= 1:
        return extracted_results[0] if extracted_results else None
    
    try:
        st.info(f"🧠 Consolidating data from {len(extracted_results)} pages using AI analysis...")
        
        # Prepare the consolidation prompt
        consolidation_prompt = f"""
        You are a financial analysis expert tasked with consolidating multiple financial statement extractions into a single, accurate, and comprehensive financial statement.

        I have extracted financial data from {len(extracted_results)} different pages of a financial document. Your job is to:

        1. **REMOVE DUPLICATES**: Identify and eliminate duplicate line items across pages
        2. **RESOLVE CONFLICTS**: When the same line item appears with different values, choose the most reliable one
        3. **CROSS-VALIDATE**: Use relationships between statements to verify accuracy (e.g., balance sheet should balance)
        4. **FILL GAPS**: Use context from other pages to complete missing information
        5. **ORGANIZE**: Create a clean, well-structured consolidated financial statement

        **CONSOLIDATION RULES:**

        **Duplicate Resolution:**
        - If same line item appears multiple times with same value → keep one instance
        - If same line item appears with different values → choose highest confidence score
        - If confidence scores are equal → choose the most complete/detailed entry
        - Always preserve the source page information in notes

        **Cross-Statement Validation:**
        - Balance Sheet: Assets = Liabilities + Equity
        - Income Statement: Revenue - Expenses = Net Income
        - Cash Flow: Operating + Investing + Financing = Net Change in Cash
        - Verify Net Income consistency between Income Statement and Cash Flow

        **Data Quality Priorities:**
        1. Completeness (more line items = better)
        2. Confidence scores (higher = better)
        3. Consistency with other statements
        4. Proper categorization and structure

        **INPUT DATA:**
        {json.dumps(extracted_results, indent=2)}

        **REQUIRED OUTPUT FORMAT:**
        Return a single JSON object with the same structure as the individual extractions, but consolidated and validated:

        {{
            "statement_type": "Consolidated Financial Statements",
            "company_name": "extracted company name",
            "period": "extracted period/date",
            "currency": "extracted currency",
            "years_detected": ["list of all years found"],
            "base_year": "primary year",
            "year_ordering": "most_recent_first or chronological",
            
            "line_items": {{
                // Consolidated line items organized by statement type
                "balance_sheet": {{
                    "current_assets": {{ ... }},
                    "non_current_assets": {{ ... }},
                    "current_liabilities": {{ ... }},
                    "non_current_liabilities": {{ ... }},
                    "equity": {{ ... }}
                }},
                "income_statement": {{
                    "revenues": {{ ... }},
                    "cost_of_sales": {{ ... }},
                    "operating_expenses": {{ ... }},
                    "other_income_expenses": {{ ... }}
                }},
                "cash_flow_statement": {{
                    "operating_activities": {{ ... }},
                    "investing_activities": {{ ... }},
                    "financing_activities": {{ ... }}
                }}
            }},
            
            "summary_metrics": {{
                "total_assets": {{"value": X, "confidence": Y}},
                "total_liabilities": {{"value": X, "confidence": Y}},
                "total_equity": {{"value": X, "confidence": Y}},
                "total_revenue": {{"value": X, "confidence": Y}},
                "net_income": {{"value": X, "confidence": Y}},
                "operating_cash_flow": {{"value": X, "confidence": Y}}
            }},
            
            "consolidation_info": {{
                "source_pages": [list of page numbers processed],
                "duplicates_removed": number,
                "conflicts_resolved": number,
                "data_quality_score": 0.0-1.0,
                "validation_results": {{
                    "balance_sheet_balances": true/false,
                    "income_statement_consistent": true/false,
                    "cash_flow_consistent": true/false
                }},
                "consolidation_notes": "detailed notes about the consolidation process"
            }},
            
            "notes": "overall observations about the consolidated financial statements"
        }}

        **CRITICAL INSTRUCTIONS:**
        - Preserve all unique financial line items found across all pages
        - Maintain proper financial statement structure and relationships
        - Include detailed consolidation_info for transparency
        - If validation fails, note the issues but still provide best consolidated result
        - Use the highest confidence scores and most complete data available
        """

        # Make API call to consolidate the data
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = exponential_backoff_retry(
            lambda: client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial data consolidation expert. Analyze multiple financial statement extractions and create a single, accurate, consolidated financial statement."
                    },
                    {
                        "role": "user", 
                        "content": consolidation_prompt
                    }
                ],
                temperature=0.1,
                max_tokens=4000
            )
        )
        
        # Parse the response
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from API")
        content = content.strip()
        
        # Extract JSON from the response
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            json_content = content[json_start:json_end].strip()
        elif content.startswith("{"):
            json_content = content
        else:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_content = json_match.group()
            else:
                raise ValueError("No valid JSON found in response")
        
        consolidated_data = json.loads(json_content)
        
        # Add metadata about the consolidation process
        consolidated_data['consolidation_metadata'] = {
            'source_extractions': len(extracted_results),
            'consolidation_timestamp': datetime.now().isoformat(),
            'consolidation_method': 'LLM_GPT4'
        }
        
        st.success(f"✅ Successfully consolidated data from {len(extracted_results)} pages")
        
        # Show consolidation summary
        if 'consolidation_info' in consolidated_data:
            info = consolidated_data['consolidation_info']
            with st.expander("📋 Consolidation Summary", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Source Pages", len(info.get('source_pages', [])))
                with col2:
                    st.metric("Duplicates Removed", info.get('duplicates_removed', 0))
                with col3:
                    st.metric("Conflicts Resolved", info.get('conflicts_resolved', 0))
                
                if 'data_quality_score' in info:
                    st.metric("Data Quality Score", f"{info['data_quality_score']:.2f}")
                
                if 'validation_results' in info:
                    validation = info['validation_results']
                    st.write("**Validation Results:**")
                    for check, result in validation.items():
                        status = "✅" if result else "⚠️"
                        st.write(f"{status} {check.replace('_', ' ').title()}: {result}")
                
                if 'consolidation_notes' in info:
                    st.write("**Consolidation Notes:**")
                    st.write(info['consolidation_notes'])
        
        return consolidated_data
        
    except Exception as e:
        st.error(f"❌ Consolidation failed: {str(e)}")
        st.warning("📄 Falling back to individual page results")
        return extracted_results

# Update the main function to include whole-document context option
# ... existing code ...

def merge_equity_into_balance_sheet(balance_sheet_data, equity_statement_data):
    """
    Merge Statement of Equity data into Balance Sheet equity section.
    Only includes ending balances that belong in a balance sheet, not movements.
    """
    if not balance_sheet_data or not equity_statement_data:
        return balance_sheet_data
    
    # Get the equity section from balance sheet
    bs_equity = balance_sheet_data.get("line_items", {}).get("equity", {})
    
    # Get equity data from statement of equity
    equity_line_items = equity_statement_data.get("line_items", {}).get("equity", {})
    
    # Map Statement of Equity ending balances to Balance Sheet equity fields
    equity_mapping = {
        # Statement of Equity field -> Balance Sheet field
        "share_capital": "share_capital",
        "capital_stock": "share_capital", 
        "common_stock": "share_capital",
        "preferred_stock": "preferred_stock",
        "retained_earnings": "retained_earnings",
        "accumulated_other_comprehensive_income": "accumulated_other_comprehensive_income",
        "additional_paid_in_capital": "additional_paid_in_capital",
        "treasury_stock": "treasury_stock",
        "total_equity": "total_equity",
        "total_shareholders_equity": "total_equity"
    }
    
    # Merge equity data, prioritizing Statement of Equity values for better accuracy
    merged_equity = bs_equity.copy()
    
    for equity_field, equity_data in equity_line_items.items():
        if isinstance(equity_data, dict) and equity_data.get("value") is not None:
            # Map to balance sheet field name
            bs_field = equity_mapping.get(equity_field, equity_field)
            
            # Only include if it's a balance sheet appropriate field (ending balances)
            # Exclude movement fields like dividends_paid, stock_issuance, etc.
            excluded_fields = [
                "dividends_paid", "dividend_payments", "cash_dividends",
                "stock_issuance", "share_issuance", "stock_repurchase",
                "beginning_balance", "ending_balance", "net_income_for_period",
                "comprehensive_income", "foreign_currency_translation"
            ]
            
            if equity_field not in excluded_fields and not any(excluded in equity_field for excluded in ["beginning_", "change_", "movement_", "_during_"]):
                # Use Statement of Equity data if it has higher confidence or if Balance Sheet doesn't have it
                if (bs_field not in merged_equity or 
                    not merged_equity[bs_field] or 
                    merged_equity[bs_field].get("confidence", 0) < equity_data.get("confidence", 0)):
                    
                    merged_equity[bs_field] = {
                        "value": equity_data["value"],
                        "confidence": equity_data["confidence"],
                        "source": "Statement of Equity"  # Track data source
                    }
    
    # Update the balance sheet data
    if "line_items" not in balance_sheet_data:
        balance_sheet_data["line_items"] = {}
    balance_sheet_data["line_items"]["equity"] = merged_equity
    
    return balance_sheet_data

def process_pdf_with_whole_document_context(uploaded_file, client):
    """Process PDF using whole document context approach for comprehensive analysis"""
    try:
        st.info("🌐 Starting Whole Document Context analysis...")
        
        # Convert PDF to images and extract text from ALL pages
        images, page_info = convert_pdf_to_images(uploaded_file, enable_parallel=True)
        if not images or not page_info:
            return None

        st.info(f"📄 Extracted text from {len(page_info)} pages. Building comprehensive document context...")
        
        # Combine all page texts into a single comprehensive context
        full_document_text = ""
        page_summaries = []
        
        for i, page in enumerate(page_info):
            page_num = page['page_num']
            page_text = page['text']
            
            # Add page separator and content
            full_document_text += f"\n\n=== PAGE {page_num} ===\n{page_text}"
            
            # Create page summary for context
            page_summary = f"Page {page_num}: {len(page_text)} chars"
            if len(page_text) > 100:
                preview = page_text[:100].replace('\n', ' ').strip()
                page_summary += f" - Preview: {preview}..."
            page_summaries.append(page_summary)
        
        # Show document structure
        with st.expander("📋 Document Structure Analysis", expanded=False):
            st.write(f"**Total Pages:** {len(page_info)}")
            st.write(f"**Total Text Length:** {len(full_document_text):,} characters")
            st.write("**Page Breakdown:**")
            for summary in page_summaries[:10]:  # Show first 10 pages
                st.write(f"  • {summary}")
            if len(page_summaries) > 10:
                st.write(f"  • ... and {len(page_summaries) - 10} more pages")
        
        # Prepare comprehensive extraction prompt
        st.info("🧠 Analyzing entire document with comprehensive AI context...")
        
        comprehensive_prompt = f"""
        You are a financial analysis expert. I'm providing you with the COMPLETE text content of a financial document containing {len(page_info)} pages. 

        Your task is to perform a COMPREHENSIVE analysis of ALL financial statements present in this document and extract a complete, consolidated financial picture.

        DOCUMENT CONTENT:
        {full_document_text}

        COMPREHENSIVE ANALYSIS INSTRUCTIONS:

        1. **DOCUMENT OVERVIEW**: 
           - Identify the company name, reporting period, and currency
           - Determine what types of financial statements are present
           - Note the document structure and organization

        2. **CROSS-STATEMENT ANALYSIS**:
           - Look for relationships between statements (e.g., net income in both income statement and cash flow)
           - Identify any reconciling items or adjustments
           - Note any segment reporting or subsidiary information

        3. **COMPLETE DATA EXTRACTION**:
           - Extract ALL financial line items from ALL statements
           - Preserve multi-year comparative data where present
           - Include notes and supplementary information where relevant

        4. **VALIDATION AND CONSISTENCY**:
           - Verify that balance sheet balances (Assets = Liabilities + Equity)
           - Check consistency of net income across statements
           - Note any discrepancies or unusual items

        REQUIRED JSON OUTPUT FORMAT:
        {{
            "processing_method": "whole_document_context",
            "document_analysis": {{
                "total_pages": {len(page_info)},
                "company_name": "extracted company name",
                "reporting_period": "extracted period",
                "currency": "extracted currency",
                "statements_present": ["list of statement types found"],
                "document_structure": "description of how document is organized",
                "multi_year_data": true/false,
                "years_covered": ["list of years if multi-year"]
            }},
            
            "consolidated_financial_data": {{
                "balance_sheet": {{
                    "current_assets": {{
                        "cash_and_equivalents": {{"value": X, "confidence": 0.95, "source_pages": [1,2], "base_year": X, "year_1": Y}},
                        "accounts_receivable": {{"value": X, "confidence": 0.90, "source_pages": [1], "base_year": X, "year_1": Y}},
                        "inventory": {{"value": X, "confidence": 0.85, "source_pages": [1], "base_year": X, "year_1": Y}},
                        "total_current_assets": {{"value": X, "confidence": 0.95, "source_pages": [1], "base_year": X, "year_1": Y}}
                    }},
                    "non_current_assets": {{
                        "property_plant_equipment": {{"value": X, "confidence": 0.92, "source_pages": [1], "base_year": X, "year_1": Y}},
                        "intangible_assets": {{"value": X, "confidence": 0.88, "source_pages": [1], "base_year": X, "year_1": Y}},
                        "total_non_current_assets": {{"value": X, "confidence": 0.95, "source_pages": [1], "base_year": X, "year_1": Y}}
                    }},
                    "current_liabilities": {{
                        "accounts_payable": {{"value": X, "confidence": 0.88, "source_pages": [1], "base_year": X, "year_1": Y}},
                        "short_term_debt": {{"value": X, "confidence": 0.90, "source_pages": [1], "base_year": X, "year_1": Y}},
                        "total_current_liabilities": {{"value": X, "confidence": 0.95, "source_pages": [1], "base_year": X, "year_1": Y}}
                    }},
                    "non_current_liabilities": {{
                        "long_term_debt": {{"value": X, "confidence": 0.92, "source_pages": [1], "base_year": X, "year_1": Y}},
                        "total_non_current_liabilities": {{"value": X, "confidence": 0.95, "source_pages": [1], "base_year": X, "year_1": Y}}
                    }},
                    "equity": {{
                        "share_capital": {{"value": X, "confidence": 0.95, "source_pages": [1], "base_year": X, "year_1": Y}},
                        "retained_earnings": {{"value": X, "confidence": 0.90, "source_pages": [1], "base_year": X, "year_1": Y}},
                        "total_equity": {{"value": X, "confidence": 0.95, "source_pages": [1], "base_year": X, "year_1": Y}}
                    }},
                    "totals": {{
                        "total_assets": {{"value": X, "confidence": 0.98, "source_pages": [1], "base_year": X, "year_1": Y}},
                        "total_liabilities_and_equity": {{"value": X, "confidence": 0.98, "source_pages": [1], "base_year": X, "year_1": Y}}
                    }}
                }},
                
                "income_statement": {{
                    "revenues": {{
                        "net_sales": {{"value": X, "confidence": 0.95, "source_pages": [2], "base_year": X, "year_1": Y}},
                        "other_income": {{"value": X, "confidence": 0.80, "source_pages": [2], "base_year": X, "year_1": Y}},
                        "total_revenue": {{"value": X, "confidence": 0.95, "source_pages": [2], "base_year": X, "year_1": Y}}
                    }},
                    "cost_of_sales": {{
                        "cost_of_goods_sold": {{"value": X, "confidence": 0.92, "source_pages": [2], "base_year": X, "year_1": Y}}
                    }},
                    "operating_expenses": {{
                        "selling_expenses": {{"value": X, "confidence": 0.88, "source_pages": [2], "base_year": X, "year_1": Y}},
                        "administrative_expenses": {{"value": X, "confidence": 0.85, "source_pages": [2], "base_year": X, "year_1": Y}},
                        "total_operating_expenses": {{"value": X, "confidence": 0.90, "source_pages": [2], "base_year": X, "year_1": Y}}
                    }},
                    "profitability": {{
                        "gross_profit": {{"value": X, "confidence": 0.95, "source_pages": [2], "base_year": X, "year_1": Y}},
                        "operating_income": {{"value": X, "confidence": 0.93, "source_pages": [2], "base_year": X, "year_1": Y}},
                        "net_income": {{"value": X, "confidence": 0.95, "source_pages": [2], "base_year": X, "year_1": Y}}
                    }}
                }},
                
                "cash_flow_statement": {{
                    "operating_activities": {{
                        "net_income": {{"value": X, "confidence": 0.95, "source_pages": [3], "base_year": X, "year_1": Y}},
                        "depreciation": {{"value": X, "confidence": 0.90, "source_pages": [3], "base_year": X, "year_1": Y}},
                        "working_capital_changes": {{"value": X, "confidence": 0.85, "source_pages": [3], "base_year": X, "year_1": Y}},
                        "net_cash_from_operations": {{"value": X, "confidence": 0.95, "source_pages": [3], "base_year": X, "year_1": Y}}
                    }},
                    "investing_activities": {{
                        "capital_expenditures": {{"value": X, "confidence": 0.88, "source_pages": [3], "base_year": X, "year_1": Y}},
                        "net_cash_from_investing": {{"value": X, "confidence": 0.90, "source_pages": [3], "base_year": X, "year_1": Y}}
                    }},
                    "financing_activities": {{
                        "dividends_paid": {{"value": X, "confidence": 0.85, "source_pages": [3], "base_year": X, "year_1": Y}},
                        "debt_proceeds": {{"value": X, "confidence": 0.88, "source_pages": [3], "base_year": X, "year_1": Y}},
                        "net_cash_from_financing": {{"value": X, "confidence": 0.90, "source_pages": [3], "base_year": X, "year_1": Y}}
                    }}
                }}
            }},
            
            "summary_metrics": {{
                "total_assets": {{"value": X, "confidence": 0.95}},
                "total_revenue": {{"value": X, "confidence": 0.95}},
                "net_income": {{"value": X, "confidence": 0.95}},
                "operating_cash_flow": {{"value": X, "confidence": 0.88}},
                "total_equity": {{"value": X, "confidence": 0.92}}
            }},
            
            "validation_results": {{
                "balance_sheet_balances": true/false,
                "net_income_consistency": true/false,
                "cross_statement_checks": ["list of validation results"],
                "data_quality_score": 0.0-1.0,
                "completeness_score": 0.0-1.0
            }},
            
            "comprehensive_analysis": {{
                "key_insights": ["list of key financial insights"],
                "unusual_items": ["list of any unusual or noteworthy items"],
                "data_gaps": ["list of any missing or unclear data"],
                "recommendations": ["recommendations for data verification"]
            }},
            
            "notes": "comprehensive observations about the financial statements and analysis process"
        }}

        CRITICAL INSTRUCTIONS:
        - Use the ENTIRE document context to make informed decisions
        - Cross-reference information between pages and statements
        - Provide source page numbers for traceability
        - Include confidence scores based on clarity and consistency
        - Validate relationships between statements
        - Extract ALL available financial data, not just key items
        - Handle multi-year data appropriately
        - Note any discrepancies or unusual items
        """

        # Make the comprehensive API call
        response = exponential_backoff_retry(
            lambda: client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a comprehensive financial analysis expert. Analyze the entire document context to extract complete, validated financial data with cross-statement verification."
                    },
                    {
                        "role": "user",
                        "content": comprehensive_prompt
                    }
                ],
                temperature=0.1,
                max_tokens=4000
            )
        )

        # Parse the response
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from API")
        content = content.strip()

        # Extract JSON from the response
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            json_content = content[json_start:json_end].strip()
        elif content.startswith("{"):
            json_content = content
        else:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_content = json_match.group()
            else:
                raise ValueError("No valid JSON found in response")

        extracted_data = json.loads(json_content)

        # Transform the data to match the expected format for display
        if 'consolidated_financial_data' in extracted_data:
            # Create a unified result that matches the display format
            unified_result = {
                "statement_type": "Comprehensive Financial Statements",
                "company_name": extracted_data.get("document_analysis", {}).get("company_name", "Unknown"),
                "period": extracted_data.get("document_analysis", {}).get("reporting_period", "Unknown"),
                "currency": extracted_data.get("document_analysis", {}).get("currency", "Unknown"),
                "years_detected": extracted_data.get("document_analysis", {}).get("years_covered", []),
                "base_year": extracted_data.get("document_analysis", {}).get("years_covered", ["Unknown"])[0] if extracted_data.get("document_analysis", {}).get("years_covered") else "Unknown",
                "processing_method": "whole_document_context",
                "line_items": extracted_data["consolidated_financial_data"],
                "summary_metrics": extracted_data.get("summary_metrics", {}),
                "validation_results": extracted_data.get("validation_results", {}),
                "comprehensive_analysis": extracted_data.get("comprehensive_analysis", {}),
                "document_analysis": extracted_data.get("document_analysis", {}),
                "notes": extracted_data.get("notes", "")
            }

            st.success(f"✅ Comprehensive analysis complete! Processed {len(page_info)} pages with full document context.")
            
            # Show analysis summary
            with st.expander("📊 Comprehensive Analysis Summary", expanded=True):
                doc_analysis = extracted_data.get("document_analysis", {})
                validation = extracted_data.get("validation_results", {})
                insights = extracted_data.get("comprehensive_analysis", {})
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Statements Found", len(doc_analysis.get("statements_present", [])))
                    st.write("**Statements:**")
                    for stmt in doc_analysis.get("statements_present", []):
                        st.write(f"  • {stmt}")
                
                with col2:
                    st.metric("Data Quality", f"{validation.get('data_quality_score', 0):.1%}")
                    st.metric("Completeness", f"{validation.get('completeness_score', 0):.1%}")
                
                with col3:
                    balance_check = "✅" if validation.get('balance_sheet_balances', False) else "⚠️"
                    income_check = "✅" if validation.get('net_income_consistency', False) else "⚠️"
                    st.write(f"**Balance Sheet:** {balance_check}")
                    st.write(f"**Income Consistency:** {income_check}")
                
                if insights.get("key_insights"):
                    st.write("**Key Insights:**")
                    for insight in insights["key_insights"][:3]:
                        st.write(f"  • {insight}")

            return unified_result
        else:
            st.warning("⚠️ Unexpected response format from comprehensive analysis")
            return extracted_data

    except Exception as e:
        st.error(f"❌ Error in whole document context processing: {str(e)}")
        return None

def main():
    """Main application function with enhanced processing approaches"""
    
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
    
    # Initialize database
    init_database()
    
    # Header
    st.markdown('<h1 class="main-header">📊 Financial Statement Transcription Tool</h1>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    **Upload your financial statement (PDF or image) and let AI extract the key financial data automatically.**
    
    ✨ **Enhanced AI Processing**: Choose between comprehensive whole-document analysis or intelligent page-by-page vector database approach.
    
    Supported formats: PDF, JPG, PNG | Max file size: 10MB
    """)
    
    # Sidebar for settings and info
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # API Key check
        if not os.getenv("OPENAI_API_KEY"):
            st.error("⚠️ OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
            st.stop()
        else:
            st.success("✅ OpenAI API key configured")
        
        # PDF Processing status
        st.subheader("📄 PDF Processing")
        if pdf_processing_available:
            st.success(f"✅ PDF support via {pdf_library}")
            st.info("🔍 Enhanced classification with parallel processing")
        else:
            st.error("❌ PDF processing unavailable")
            if pdf_error_message:
                st.caption(pdf_error_message)
            with st.expander("🔧 Fix PDF Processing"):
                st.markdown("""
                **Quick Fix Options:**
                
                1. **Install Poppler (Windows):**
                   - Download from [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases/)
                   - Add to PATH environment variable
                
                2. **Install PyMuPDF:**
                   ```bash
                   pip install PyMuPDF
                   ```
                
                3. **Use images instead:**
                   - Convert PDF to PNG/JPG first
                   - Upload image files directly
                """)
        
        # Vector Database status
        st.subheader("🗄️ Vector Database")
        try:
            chroma_client = init_chromadb()
            if chroma_client:
                st.success("✅ ChromaDB initialized")
                st.caption("Semantic search enabled for large documents")
            else:
                st.error("❌ ChromaDB initialization failed")
        except Exception as e:
            st.error("❌ ChromaDB unavailable")
            st.caption(f"Error: {str(e)[:50]}...")
        
        st.markdown("---")
        
        # Add clear results button
        if st.session_state.processing_complete:
            if st.button("🗑️ Clear Results", type="secondary"):
                st.session_state.extracted_data = None
                st.session_state.processing_complete = False
                st.session_state.uploaded_file_name = None
                st.session_state.processing_approach = None
                st.rerun()
        
        st.header("📈 Usage Statistics")
        # Get basic stats from database
        try:
            conn = sqlite3.connect('financial_statements.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM processing_log")
            total_processed = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(accuracy_score) FROM processing_log WHERE accuracy_score IS NOT NULL")
            avg_accuracy = cursor.fetchone()[0]
            
            conn.close()
            
            st.metric("Documents Processed", total_processed)
            if avg_accuracy:
                st.metric("Average Confidence", f"{avg_accuracy:.1%}")
        except Exception as e:
            # Handle database errors gracefully (important for cloud deployments)
            st.metric("Documents Processed", "N/A")
            st.caption("📝 Statistics unavailable (ephemeral storage)")
    
    # Show existing results if available
    if st.session_state.processing_complete and st.session_state.extracted_data:
        st.success(f"✅ Results for: {st.session_state.uploaded_file_name}")
        
        # Add a small summary box
        with st.container():
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Status", "✅ Complete")
            with col2:
                if isinstance(st.session_state.extracted_data, dict):
                    statement_type = st.session_state.extracted_data.get("statement_type", "Unknown")
                    st.metric("Statement Type", statement_type)
                else:
                    st.metric("Statement Type", "Multiple")
            with col3:
                filename = st.session_state.uploaded_file_name or "unknown.file"
                st.metric("File", filename.split('.')[-1].upper())
            with col4:
                approach = st.session_state.processing_approach or "Unknown"
                st.metric("Approach", approach)
        
        # Display the preserved results
        if st.session_state.extracted_data:
            st.success("✅ Financial data extracted successfully!")
            
            # Organize results by statement type for unified display
            balance_sheet_data = None
            income_statement_data = None
            equity_statement_data = None
            cash_flow_data = None
            other_statements = []
            
            # Categorize extracted data by statement type
            if isinstance(st.session_state.extracted_data, list):
                for result in st.session_state.extracted_data:
                    statement_type = result.get("statement_type", "").lower()
                    if any(bs_term in statement_type for bs_term in ["balance sheet", "financial position", "assets and liabilities"]):
                        balance_sheet_data = result
                    elif any(is_term in statement_type for is_term in ["income", "profit", "loss", "operations", "earnings"]):
                        income_statement_data = result
                    elif any(eq_term in statement_type for eq_term in ["equity", "shareholders", "stockholders", "changes in equity"]):
                        equity_statement_data = result
                    elif any(cf_term in statement_type for cf_term in ["cash flow", "cashflow"]):
                        cash_flow_data = result
                    else:
                        other_statements.append(result)
            else:
                # Single result - categorize it
                statement_type = st.session_state.extracted_data.get("statement_type", "").lower()
                if any(bs_term in statement_type for bs_term in ["balance sheet", "financial position", "assets and liabilities"]):
                    balance_sheet_data = st.session_state.extracted_data
                elif any(is_term in statement_type for is_term in ["income", "profit", "loss", "operations", "earnings"]):
                    income_statement_data = st.session_state.extracted_data
                elif any(eq_term in statement_type for eq_term in ["equity", "shareholders", "stockholders", "changes in equity"]):
                    equity_statement_data = st.session_state.extracted_data
                elif any(cf_term in statement_type for cf_term in ["cash flow", "cashflow"]):
                    cash_flow_data = st.session_state.extracted_data
                else:
                    other_statements.append(st.session_state.extracted_data)
            
            # Implement unified equity display: merge Statement of Equity into Balance Sheet
            if balance_sheet_data and equity_statement_data:
                st.info("🔗 Merging Statement of Equity data into Balance Sheet equity section for unified display")
                balance_sheet_data = merge_equity_into_balance_sheet(balance_sheet_data, equity_statement_data)
            
            # Display organized results
            displayed_statements = []
            
            # 1. Balance Sheet (with enhanced equity from Statement of Equity)
            if balance_sheet_data:
                st.markdown("## 📊 Balance Sheet")
                if equity_statement_data:
                    st.caption("✨ Enhanced with Statement of Equity data")
                df_bs = display_extracted_data(balance_sheet_data)
                displayed_statements.append(("Balance Sheet", df_bs))
            
            # 2. Income Statement  
            if income_statement_data:
                st.markdown("## 💰 Income Statement")
                df_is = display_extracted_data(income_statement_data)
                displayed_statements.append(("Income Statement", df_is))
            
            # 3. Statement of Equity (shown separately for transparency)
            if equity_statement_data:
                st.markdown("## 🏛️ Statement of Changes in Equity")
                st.caption("📝 Showing equity movements and changes (ending balances merged into Balance Sheet above)")
                df_eq = display_extracted_data(equity_statement_data)
                displayed_statements.append(("Statement of Equity", df_eq))
            
            # 4. Cash Flow Statement
            if cash_flow_data:
                st.markdown("## 💸 Cash Flow Statement")
                df_cf = display_extracted_data(cash_flow_data)
                displayed_statements.append(("Cash Flow Statement", df_cf))
            
            # 5. Other statements
            for i, other_data in enumerate(other_statements):
                st.markdown(f"## 📄 {other_data.get('statement_type', f'Other Statement {i+1}')}")
                df_other = display_extracted_data(other_data)
                displayed_statements.append((other_data.get('statement_type', f'Other Statement {i+1}'), df_other))
            
            # Combined export for all statements
            if len(displayed_statements) > 1:
                st.markdown("---")
                st.subheader("📤 Export All Statements")
                
                all_dfs = []
                for statement_name, df in displayed_statements:
                    if df is not None:
                        df_copy = df.copy()
                        df_copy['Statement_Type'] = statement_name
                        all_dfs.append(df_copy)
                
                if all_dfs:
                    combined_df = pd.concat(all_dfs, ignore_index=True)
                    csv = combined_df.to_csv(index=False)
                    st.download_button(
                        label="📄 Download All Statements as CSV",
                        data=csv,
                        file_name=f"complete_financial_statements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key="download_all_statements_csv"
                    )
        
        st.info("💡 Upload a new file below to process another document, or use 'Clear Results' in the sidebar.")
        st.markdown("---")
    
    # File upload section
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Choose a financial statement file",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        help="Upload a PDF or image file containing a financial statement"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file is not None:
        # Check if this is a new file
        is_new_file = st.session_state.uploaded_file_name != uploaded_file.name
        
        # Clear selected approach for new files
        if is_new_file:
            st.session_state.selected_processing_approach = None
        
        # Display file info and document analysis
        file_details = {
            "Filename": uploaded_file.name,
            "File size": f"{uploaded_file.size / 1024:.1f} KB",
            "File type": uploaded_file.type
        }
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("📄 File Information")
            for key, value in file_details.items():
                st.write(f"**{key}:** {value}")
            
            # Document analysis for PDFs
            if uploaded_file.type == "application/pdf":
                with st.spinner("🔍 Analyzing document..."):
                    doc_analysis = analyze_document_characteristics(uploaded_file)
                    
                st.subheader("📊 Document Analysis")
                st.write(f"**Pages:** {doc_analysis['page_count']}")
                st.write(f"**Size:** {doc_analysis['file_size_mb']:.1f} MB")
                
                # Show recommendation with confidence
                recommendation = doc_analysis['recommendation']
                confidence = doc_analysis['confidence']
                reason = doc_analysis['reason']
                
                if confidence == "high":
                    st.success(f"**Recommended:** {str(recommendation).replace('_', ' ').title()}")
                elif confidence == "medium":
                    st.info(f"**Suggested:** {str(recommendation).replace('_', ' ').title()}")
                else:
                    st.warning(f"**Option:** {str(recommendation).replace('_', ' ').title()}")
                
                st.caption(reason)
        
        with col2:
            # Display uploaded image (if it's an image)
            if uploaded_file.type.startswith('image'):
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Financial Statement", use_column_width=True)
            elif uploaded_file.type == "application/pdf":
                st.info("📄 PDF uploaded - preview will be available after processing")
        
        # Processing approach selection for PDFs
        processing_approach = None
        if uploaded_file.type == "application/pdf" and pdf_processing_available:
            st.subheader("🎯 Choose Processing Approach")
            
            doc_analysis = analyze_document_characteristics(uploaded_file)
            recommendation = doc_analysis.get('recommendation', 'user_choice')
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🌐 Whole Document Context")
                st.markdown("""
                **Best for:**
                - Small to medium documents (≤30 pages)
                - Comprehensive cross-statement analysis
                - Maximum context understanding
                
                **Features:**
                - Processes entire document as context
                - Superior relationship detection
                - Comprehensive data extraction
                """)
                
                # Show recommendation indicator but don't affect button functionality
                if recommendation == "whole_document":
                    st.info("🎯 Recommended for this document")
                
                if st.button("🌐 Use Whole Document", type="secondary", key="whole_doc_btn"):
                    st.session_state.selected_processing_approach = "whole_document"
                    st.rerun()
            
            with col2:
                st.markdown("### 🗄️ Vector Database Analysis")
                st.markdown("""
                **Best for:**
                - Large documents (>30 pages)
                - Fast, targeted extraction
                - Enhanced page classification
                
                **Features:**
                - Intelligent page classification
                - Parallel processing (10 workers)
                - Enhanced number density scoring
                - Case-insensitive pattern matching
                """)
                
                # Show recommendation indicator but don't affect button functionality
                if recommendation == "vector_database":
                    st.info("🎯 Recommended for this document")
                
                if st.button("🗄️ Use Vector Database", type="secondary", key="vector_db_btn"):
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
        
        # Process button - show when approach is selected (for PDFs) or for non-PDF files
        if uploaded_file.type != "application/pdf":
            # For non-PDF files, auto-select approach and always show button
            processing_approach = "single_image"
            show_button = True
        else:
            # For PDF files, check if user has selected an approach
            processing_approach = st.session_state.selected_processing_approach
            show_button = processing_approach is not None
        
        # Show process button if approach is selected or it's a single image
        if show_button:
            # Only disable if we already have results for this exact file and approach
            button_disabled = (
                not is_new_file and 
                st.session_state.processing_complete and 
                st.session_state.processing_approach == str(processing_approach or "Unknown").replace('_', ' ').title()
            )
            
            button_label = "🚀 Extract Financial Data"
            if button_disabled:
                button_label = "✅ Already Processed"
            
            # Debug info
            with st.expander("🔧 Debug Info", expanded=False):
                st.write(f"**File:** {uploaded_file.name}")
                st.write(f"**Is new file:** {is_new_file}")
                st.write(f"**Processing complete:** {st.session_state.processing_complete}")
                st.write(f"**Selected approach:** {st.session_state.selected_processing_approach}")
                st.write(f"**Processing approach:** {processing_approach}")
                st.write(f"**Show button:** {show_button}")
                st.write(f"**Button disabled:** {button_disabled}")
                
                # Reset session state button for debugging
                if st.button("🔄 Reset Session State", key="reset_session"):
                    st.session_state.extracted_data = None
                    st.session_state.processing_complete = False
                    st.session_state.uploaded_file_name = None
                    st.session_state.processing_approach = None
                    st.session_state.selected_processing_approach = None
                    st.success("Session state reset!")
                    st.rerun()
            
            if st.button(button_label, type="primary", disabled=button_disabled):
                # Clear previous results for new file or new approach
                if is_new_file or st.session_state.processing_approach != str(processing_approach or "Unknown").replace('_', ' ').title():
                    st.session_state.extracted_data = None
                    st.session_state.processing_complete = False
                    
                    start_time = datetime.now()
                    
                    with st.spinner("🤖 AI is analyzing your financial statement..."):
                        # Determine file type and processing approach
                        if uploaded_file.type == "application/pdf":
                            if not pdf_processing_available:
                                st.error("❌ PDF processing is not available. Please install pdf2image for PDF support.")
                                return
                            
                            if processing_approach == "whole_document":
                                # Use whole document context approach
                                st.info("🌐 Using Whole Document Context approach...")
                                extracted_data = process_pdf_with_whole_document_context(uploaded_file, client)
                            else:
                                # Use vector database approach
                                st.info("🗄️ Using Vector Database approach...")
                                extracted_data = process_pdf_with_vector_db(uploaded_file, client)
                        
                        elif uploaded_file.type in ["image/jpeg", "image/jpg"]:
                            processing_approach = "single_image"
                            extracted_data = extract_financial_data(uploaded_file, "jpeg")
                        elif uploaded_file.type == "image/png":
                            processing_approach = "single_image"
                            extracted_data = extract_financial_data(uploaded_file, "png")
                        else:
                            st.error("Unsupported file type. Please upload a PDF, JPG, or PNG file.")
                            return
                        
                        processing_time = (datetime.now() - start_time).total_seconds()
                        
                        if extracted_data:
                            # Store results in session state
                            st.session_state.extracted_data = extracted_data
                            st.session_state.processing_complete = True
                            st.session_state.uploaded_file_name = uploaded_file.name
                            st.session_state.processing_approach = str(processing_approach or "Unknown").replace('_', ' ').title()
                            
                            # Calculate confidence
                            if isinstance(extracted_data, list):
                                # Multiple pages
                                all_confidences = []
                                for page_data in extracted_data:
                                    if isinstance(page_data, dict):
                                        line_items = page_data.get("line_items", {})
                                        for category in line_items.values():
                                            if isinstance(category, dict):
                                                for item in category.values():
                                                    if isinstance(item, dict) and "confidence" in item:
                                                        all_confidences.append(item["confidence"])
                                avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.8
                            else:
                                # Single result
                                avg_confidence = 0.8  # Default confidence
                            
                            # Log processing
                            log_processing(uploaded_file.name, processing_time, avg_confidence, "success")
                            
                            st.success(f"✅ Data extracted successfully in {processing_time:.1f} seconds using {str(processing_approach or 'Unknown').replace('_', ' ').title()} approach!")
                            st.rerun()  # Refresh to show results
                            
                        else:
                            log_processing(uploaded_file.name, processing_time, 0, "failed")
                            st.error("❌ Failed to extract data from the document. Please try with a clearer image or different document.")
            else:
                st.info("👆 Please select a processing approach above to continue.")
        else:
            # For PDFs, show message to select approach; for other cases, this shouldn't happen
            if uploaded_file.type == "application/pdf":
                st.info("👆 Please select a processing approach above to continue.")
            else:
                st.error("❌ Unexpected state: Non-PDF file should always show button")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Financial Statement Transcription Tool | Powered by OpenAI GPT-4 Vision</p>
        <p>⚠️ Enhanced with parallel processing and intelligent classification. Please verify all extracted data before use.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 
