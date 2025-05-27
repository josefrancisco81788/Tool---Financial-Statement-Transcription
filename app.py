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

def convert_pdf_to_images(pdf_file):
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
        
        # Extract text from each image using Vision API
        for page_num, image in enumerate(images):
            # Always use Vision API for text extraction
            st.write(f"🔍 **Processing Page {page_num + 1}** with AI...")
            page_text = extract_text_with_vision_api(image, page_num + 1)
            page_text_lower = page_text.lower()
            
            page_info.append({
                'page_num': page_num + 1,
                'text': page_text_lower,
                'image': image
            })
        
        st.success(f"✅ Successfully processed all {len(images)} pages with AI text extraction")
        return images, page_info
        
    except Exception as e:
        st.error(f"Error converting PDF: {str(e)}")
        if "poppler" in str(e).lower():
            st.error("💡 This looks like a Poppler installation issue. Please see the instructions above.")
        return None, None

def extract_text_with_vision_api(pil_image, page_num):
    """Extract text from image using OpenAI Vision API"""
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
        
        response = client.chat.completions.create(
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
            max_tokens=800  # Increased for better text extraction
        )
        
        extracted_text = response.choices[0].message.content or ""
        
        if extracted_text:
            # Show concise success message with preview
            preview = extracted_text[:150].replace('\n', ' ').strip()
            st.success(f"✅ Page {page_num}: Extracted {len(extracted_text)} characters")
            with st.expander(f"📄 Page {page_num} Text Preview", expanded=False):
                st.code(f"{preview}..." if len(extracted_text) > 150 else extracted_text)
        else:
            st.warning(f"⚠️ Page {page_num}: No text could be extracted")
        
        return extracted_text
        
    except Exception as e:
        st.error(f"❌ Page {page_num}: Error extracting text - {str(e)}")
        return ""

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
            response = client.chat.completions.create(
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

def classify_financial_statement_pages(page_info):
    """Classify pages to identify financial statement types"""
    financial_pages = []
    
    # Comprehensive keywords for different statement types (all lowercase for case-insensitive matching)
    
    # Income Statement Keywords (Enhanced with international and industry variations)
    income_keywords = [
        # US GAAP Standard
        'income statement', 'consolidated income statement', 'statement of income',
        # IFRS Standard
        'statement of profit and loss', 'statement of profit or loss', 
        'consolidated statement of profit and loss', 'consolidated statement of profit or loss',
        # Operations Terminology (KEY: This will catch "STATEMENTS OF OPERATIONS")
        'statement of operations', 'statements of operations', 'consolidated statement of operations',
        'operating statement', 'consolidated operating statement',
        # Other Variations
        'profit and loss statement', 'p&l statement', 'earnings statement',
        'statement of comprehensive income', 'consolidated statement of comprehensive income',
        # Abbreviated forms
        'profit & loss', 'p & l', 'statement of ops', 'profit and loss', 'p&l',
        # Additional comprehensive terms
        'consolidated statements of operations', 'statement of earnings',
        'consolidated statement of earnings', 'statement of profit', 'consolidated income',
        'statement of operation', 'consolidated statement operation'
    ]
    
    # Balance Sheet Keywords (Enhanced)
    balance_keywords = [
        # US GAAP Standard
        'balance sheet', 'consolidated balance sheet', 'balance sheets',
        # IFRS Standard  
        'statement of financial position', 'consolidated statement of financial position',
        'statements of financial position', 'consolidated statements of financial position',
        # Industry Variations
        'statement of assets and liabilities', 'statement of condition',
        'financial position statement', 'statement of net assets',
        # Common abbreviations and variations
        'statement of fin position', 'fin position statement', 'financial position',
        'consolidated balance sheets', 'statement of position'
    ]
    
    # Cash Flow Keywords (Enhanced)
    cashflow_keywords = [
        # Standard terms
        'cash flow statement', 'statement of cash flows', 'consolidated statement of cash flows',
        'cash flows statement', 'statement of cashflows', 'statements of cash flows',
        'consolidated statements of cash flows', 'cash flow statements',
        # Alternative terminology
        'statement of sources and uses of funds', 'funds flow statement',
        'statement of changes in cash position', 'consolidated cash flows',
        'cash flows', 'cashflows statement', 'statement of sources and uses'
    ]
    
    # Equity Statement Keywords (Enhanced)
    equity_keywords = [
        # Standard equity terms
        'statement of changes in equity', 'consolidated statement of changes in equity',
        'statements of changes in equity', 'consolidated statements of changes in equity',
        'statement of shareholders equity', 'statement of stockholders equity',
        'statement of changes in owners equity', 'equity statement',
        # Specialized contexts
        'statement of changes in net assets', 'statement of retained earnings',
        'changes in equity', 'shareholders equity statement', 'stockholders equity statement',
        'statement of changes in shareholders equity', 'statement of changes in stockholders equity',
        'changes in shareholders equity', 'changes in stockholders equity'
    ]
    
    # Additional keywords that might indicate financial statements but are less specific
    general_financial_keywords = [
        'consolidated', 'financial statements', 'audited', 'unaudited',
        'thousands', 'millions', 'fiscal year', 'year ended', 'current assets',
        'total liabilities', 'gross profit', 'cost of sales', 'revenue', 'net income',
        # Currency indicators
        'php', 'usd', 'eur', 'gbp', '₱', '$', '€', '£', 'peso', 'pesos'
    ]
    
    st.subheader("🔍 Page Classification Analysis")
    
    for page in page_info:
        page_text = page['text']  # Already lowercase from conversion
        page_num = page['page_num']
        
        st.markdown(f"### Page {page_num} Analysis")
        
        # Debug: Show text extraction details
        if len(page_text.strip()) == 0:
            st.error(f"❌ No text available for page {page_num} - classification will be unreliable")
            continue
        else:
            st.write(f"📄 **Text length:** {len(page_text)} characters")
            
            # Show first 300 characters of extracted text
            preview_text = page_text[:300].replace('\n', ' ').strip()
            if len(page_text) > 300:
                preview_text += "..."
            
            # Special check: Look for "operations" in the text
            if 'operations' in page_text:
                st.success(f"✅ Found 'operations' in page text!")
                # Show context around "operations"
                operations_index = page_text.find('operations')
                start_context = max(0, operations_index - 50)
                end_context = min(len(page_text), operations_index + 50)
                context = page_text[start_context:end_context]
                st.code(f"Context around 'operations': ...{context}...")
            
            with st.expander(f"📖 View extracted text from page {page_num}", expanded=False):
                st.code(preview_text)
        
        # Score each page for different statement types
        income_score = sum(1 for keyword in income_keywords if keyword in page_text)
        balance_score = sum(1 for keyword in balance_keywords if keyword in page_text)
        cashflow_score = sum(1 for keyword in cashflow_keywords if keyword in page_text)
        
        # Add bonus points for general financial keywords
        general_score = sum(1 for keyword in general_financial_keywords if keyword in page_text)
        
        # Enhanced debugging: Show what keywords were found with exact matches
        found_keywords = []
        found_income = [kw for kw in income_keywords if kw in page_text]
        found_balance = [kw for kw in balance_keywords if kw in page_text]
        found_cashflow = [kw for kw in cashflow_keywords if kw in page_text]
        found_general = [kw for kw in general_financial_keywords if kw in page_text]
        
        # Special check for "statement of operations" variations
        operations_variations = [
            'statement of operations', 'statements of operations', 
            'operations statement', 'statement operations'
        ]
        found_operations = [kw for kw in operations_variations if kw in page_text]
        
        if found_operations:
            st.info(f"🎯 **Special Detection:** Found 'Statement of Operations' variations: {found_operations}")
        
        if found_income:
            found_keywords.extend([f"**Income:** {kw}" for kw in found_income])
        if found_balance:
            found_keywords.extend([f"**Balance:** {kw}" for kw in found_balance])
        if found_cashflow:
            found_keywords.extend([f"**Cashflow:** {kw}" for kw in found_cashflow])
        if found_general:
            found_keywords.extend([f"**General:** {kw}" for kw in found_general[:3]])  # Limit to first 3
        
        if found_keywords:
            st.success(f"✅ **Found {len(found_keywords)} keyword matches:**")
            for keyword in found_keywords[:10]:  # Show max 10 keywords
                st.write(f"  • {keyword}")
            if len(found_keywords) > 10:
                st.write(f"  • ... and {len(found_keywords) - 10} more")
        else:
            st.warning(f"⚠️ **No financial keywords found on page {page_num}**")
        
        # Apply general score as a multiplier (but cap it)
        multiplier = min(1 + (general_score * 0.2), 2.0)  # Max 2x multiplier
        
        income_score = income_score * multiplier
        balance_score = balance_score * multiplier
        cashflow_score = cashflow_score * multiplier
        
        # Show scoring details
        st.write(f"📊 **Scores:** Income: {income_score:.1f}, Balance: {balance_score:.1f}, Cash Flow: {cashflow_score:.1f}")
        
        # Determine the most likely statement type
        max_score = max(income_score, balance_score, cashflow_score)
        
        # Even lower threshold and also check for any financial content
        if max_score >= 0.5 or general_score >= 3:  # Very low threshold
            if income_score == max_score:
                statement_type = "Income Statement"
            elif balance_score == max_score:
                statement_type = "Balance Sheet"
            else:
                statement_type = "Cash Flow Statement"
            
            st.success(f"🎯 **Classified as:** {statement_type} (confidence: {max_score:.1f})")
            
            financial_pages.append({
                'page_num': page_num,
                'statement_type': statement_type,
                'confidence': max_score,
                'image': page['image'],
                'scores': {
                    'income': income_score,
                    'balance': balance_score,
                    'cashflow': cashflow_score,
                    'general': general_score
                }
            })
        else:
            st.info(f"ℹ️ **Not classified as financial statement** (max score: {max_score:.1f})")
        
        st.markdown("---")
    
    # Sort by confidence and process top pages
    def get_confidence_score(page_dict):
        confidence = page_dict.get('confidence', 0)
        if isinstance(confidence, (int, float)):
            return float(confidence)
        return 0.0
    
    financial_pages.sort(key=get_confidence_score, reverse=True)
    
    return financial_pages

def extract_comprehensive_financial_data(base64_image, statement_type_hint, page_text=""):
    """Guided adaptive financial data extraction that balances structure with flexibility"""
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

        response = client.chat.completions.create(
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

        # Parse the JSON response
        content = response.choices[0].message.content
        
        if not content:
            return None
        
        # Extract JSON from the response
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            return None
            
        json_str = content[start_idx:end_idx]
        return json.loads(json_str)
        
    except Exception as e:
        st.error(f"Error in guided adaptive extraction: {str(e)}")
        return None

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
        
        # 1. SEMANTIC SEARCH: Query for financial statement types
        financial_queries = [
            "balance sheet statement of financial position assets liabilities equity",
            "income statement profit loss revenue expenses operations",
            "cash flow statement operating investing financing activities",
            "statement of equity retained earnings stockholders"
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
        
        # 2. KEYWORD ANALYSIS (Enhanced)
        financial_keywords = [
            'assets', 'liabilities', 'equity', 'revenue', 'expenses', 'net income',
            'cash flow', 'balance sheet', 'income statement', 'profit', 'loss',
            'financial position', 'operations', 'investing', 'financing',
            'current assets', 'non-current', 'stockholders', 'retained earnings',
            'total assets', 'total liabilities', 'gross profit', 'operating income',
            'statement of operations', 'statements of operations', 'consolidated'
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

def process_pdf_with_vector_db(uploaded_file, client):
    """Process PDF using comprehensive vector database approach for large documents"""
    try:
        st.info("🔍 Starting comprehensive PDF analysis with vector database...")
        
        # Initialize ChromaDB
        chroma_client = init_chromadb()
        if not chroma_client:
            st.error("Failed to initialize vector database")
            return None
        
        collection = create_or_get_collection(chroma_client)
        
        # Convert PDF to images and extract text from ALL pages
        images, page_info = convert_pdf_to_images(uploaded_file)
        if not images or not page_info:
            return None
        
        st.info(f"📊 Analyzing {len(page_info)} pages with semantic vector search...")
        
        # Analyze each page semantically to find financial content
        financial_pages = []
        for page in page_info:
            is_financial, confidence, statement_type = analyze_page_content_semantically(
                collection, page['text'], page['page_num']
            )
            
            if is_financial:
                financial_pages.append({
                    'page_num': page['page_num'],
                    'statement_type': statement_type,
                    'confidence': confidence,
                    'image': page['image'],
                    'text': page['text']
                })
        
        if not financial_pages:
            st.warning("⚠️ No financial statement pages detected. Processing first page as fallback.")
            financial_pages = [{
                'page_num': 1,
                'statement_type': 'Unknown',
                'confidence': 0.1,
                'image': images[0],
                'text': page_info[0]['text'] if page_info else ""
            }]
        
        # Sort by confidence and process top pages
        def get_confidence_score(page_dict):
            confidence = page_dict.get('confidence', 0)
            if isinstance(confidence, (int, float)):
                return float(confidence)
            return 0.0
        
        financial_pages.sort(key=get_confidence_score, reverse=True)
        
        st.success(f"✅ Found {len(financial_pages)} financial statement pages")
        
        # Process top 3 financial pages for comprehensive extraction
        max_pages_to_process = min(3, len(financial_pages))
        extracted_results = []
        
        for i in range(max_pages_to_process):
            page = financial_pages[i]
            st.info(f"🔍 Extracting data from page {page['page_num']} ({page['statement_type']})...")
            
            # Extract financial data from this page
            base64_image = encode_pil_image(page['image'])
            page_data = extract_comprehensive_financial_data(base64_image, page['statement_type'], str(page.get('text', '')))
            
            if page_data:
                page_data['page_number'] = page['page_num']
                page_data['confidence_score'] = page['confidence']
                extracted_results.append(page_data)
        
        if not extracted_results:
            st.error("❌ Failed to extract financial data from any pages")
            return None
        
        # If we have multiple pages, return them as a list
        # If only one page, return it directly
        if len(extracted_results) == 1:
            result = extracted_results[0]
            result['total_pages'] = len(images)
            result['financial_pages_found'] = len(financial_pages)
            return result
        else:
            # Return multiple pages with summary info
            for result in extracted_results:
                result['total_pages'] = len(images)
                result['financial_pages_found'] = len(financial_pages)
            return extracted_results
        
    except Exception as e:
        st.error(f"Error in vector database PDF processing: {str(e)}")
        return None

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

def main():
    # Initialize session state
    if 'extracted_data' not in st.session_state:
        st.session_state.extracted_data = None
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'uploaded_file_name' not in st.session_state:
        st.session_state.uploaded_file_name = None
    if 'ifrs_data' not in st.session_state:
        st.session_state.ifrs_data = None
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 Financial Statement Transcription Tool</h1>
        <p>Advanced AI-powered extraction of financial data from PDF documents</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Processing Method Selection
        st.subheader("Processing Method")
        processing_method = st.radio(
            "Choose extraction approach:",
            [
                "🚀 Whole-Document Context (Recommended)",
                "🔍 Vector Database Analysis (Legacy)"
            ],
            help="""
            **Whole-Document Context**: Fast, comprehensive extraction using entire document as context. Best for production use with thousands of documents.
            
            **Vector Database Analysis**: Page-by-page analysis with semantic search. More detailed but slower.
            """
        )
        
        # API Configuration
        st.subheader("API Settings")
        
        # Use environment variable from .env file (consistent with app initialization)
        api_key = st.text_input("OpenAI API Key", type="password", 
                               value=os.getenv("OPENAI_API_KEY", ""))
        
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            global client
            client = OpenAI(api_key=api_key)
        
        # Processing Options
        st.subheader("Options")
        show_debug = st.checkbox("Show debug information", value=False)
        auto_validate = st.checkbox("Auto-validate financial statements", value=True)
    
    # Main content area
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📁 Upload Document")
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type="pdf",
            help="Upload a financial statement PDF for analysis"
        )
        
        if uploaded_file is not None:
            st.session_state.uploaded_file_name = uploaded_file.name
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            
            # File information
            file_size = len(uploaded_file.getvalue()) / 1024 / 1024  # MB
            st.info(f"📄 File size: {file_size:.1f} MB")
            
            # Processing button
            if st.button("🚀 Extract Financial Data", type="primary"):
                if not api_key:
                    st.error("❌ Please provide an OpenAI API key in the sidebar")
                else:
                    with st.spinner("Processing document..."):
                        try:
                            if processing_method and "Whole-Document Context" in processing_method:
                                # Use new whole-document context approach
                                st.session_state.ifrs_data = process_pdf_with_whole_document_context(uploaded_file)
                                st.session_state.extracted_data = None  # Clear old data
                            else:
                                # Use legacy vector database approach
                                st.session_state.extracted_data = process_pdf_with_vector_db(uploaded_file, client)
                                st.session_state.ifrs_data = None  # Clear new data
                            
                            st.session_state.processing_complete = True
                            
                        except Exception as e:
                            st.error(f"❌ Error processing document: {str(e)}")
                            if show_debug:
                                st.exception(e)
    
    with col2:
        st.subheader("📊 Processing Status")
        
        if st.session_state.uploaded_file_name:
            st.info(f"📄 Current file: {st.session_state.uploaded_file_name}")
        
        if st.session_state.processing_complete:
            if processing_method and "Whole-Document Context" in processing_method and st.session_state.ifrs_data:
                st.success("✅ Whole-document context extraction completed!")
                
                # Show processing summary
                metadata = st.session_state.ifrs_data.get("extraction_metadata", {})
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    line_items = metadata.get("total_line_items_extracted", 0)
                    st.metric("Line Items", line_items)
                
                with col_b:
                    confidence = metadata.get("extraction_confidence", 0)
                    st.metric("Confidence", f"{confidence:.1%}")
                
                with col_c:
                    pages = st.session_state.ifrs_data.get("document_pages", 0)
                    st.metric("Pages", pages)
                
            elif st.session_state.extracted_data:
                st.success("✅ Vector database extraction completed!")
                
                # Show processing summary for legacy method
                total_results = len(st.session_state.extracted_data)
                st.metric("Pages Processed", total_results)
        else:
            st.info("👆 Upload a PDF file and click 'Extract Financial Data' to begin")
    
    # Clear results button
    if st.session_state.processing_complete:
        if st.button("🗑️ Clear Results"):
            st.session_state.extracted_data = None
            st.session_state.ifrs_data = None
            st.session_state.processing_complete = False
            st.session_state.uploaded_file_name = None
            st.rerun()
    
    # Display results
    if st.session_state.processing_complete:
        st.markdown("---")
        
        if st.session_state.ifrs_data:
            # Display IFRS structured results
            st.header("📈 Comprehensive Financial Statements")
            display_ifrs_financial_statements(st.session_state.ifrs_data)
            
        elif st.session_state.extracted_data:
            # Display legacy vector database results
            st.header("📈 Extracted Financial Data")
            
            # Separate data by statement type
            balance_sheet_data = []
            income_statement_data = []
            cash_flow_data = []
            other_data = []
            
            for result in st.session_state.extracted_data:
                statement_type = result.get('statement_type', '').lower()
                if 'balance' in statement_type:
                    balance_sheet_data.append(result)
                elif 'income' in statement_type or 'profit' in statement_type:
                    income_statement_data.append(result)
                elif 'cash' in statement_type:
                    cash_flow_data.append(result)
                else:
                    other_data.append(result)
            
            # Display each statement type
            if balance_sheet_data:
                st.subheader("🏦 Balance Sheet")
                for data in balance_sheet_data:
                    display_single_page_data(data)
            
            if income_statement_data:
                st.subheader("💰 Income Statement")
                for data in income_statement_data:
                    display_single_page_data(data)
            
            if cash_flow_data:
                st.subheader("💸 Cash Flow Statement")
                for data in cash_flow_data:
                    display_single_page_data(data)
            
            if other_data:
                st.subheader("📋 Other Financial Data")
                for data in other_data:
                    display_single_page_data(data)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>Financial Statement Transcription Tool | Powered by OpenAI GPT-4 Vision</p>
        <p>⚡ Now with Whole-Document Context Analysis for faster, more accurate extraction</p>
    </div>
    """, unsafe_allow_html=True)

def extract_full_document_text(uploaded_file):
    """Extract text from all pages of the document for whole-document context"""
    try:
        st.info("📄 Extracting text from entire document for comprehensive analysis...")
        
        # Convert PDF to images and extract text from ALL pages
        images, page_info = convert_pdf_to_images(uploaded_file)
        if not images or not page_info:
            return None, None
        
        # Combine all page text with page markers
        full_document_text = ""
        page_markers = []
        
        for page in page_info:
            page_num = page['page_num']
            page_text = page['text']
            
            # Add page marker
            page_marker = f"\n\n=== PAGE {page_num} ===\n"
            full_document_text += page_marker + page_text
            
            page_markers.append({
                'page_num': page_num,
                'start_pos': len(full_document_text) - len(page_text),
                'end_pos': len(full_document_text),
                'text_length': len(page_text)
            })
        
        st.success(f"✅ Extracted text from {len(page_info)} pages ({len(full_document_text)} characters total)")
        
        # Show document structure summary
        with st.expander("📊 Document Structure Summary", expanded=False):
            st.write(f"**Total Pages:** {len(page_info)}")
            st.write(f"**Total Characters:** {len(full_document_text):,}")
            st.write(f"**Average Characters per Page:** {len(full_document_text) // len(page_info):,}")
            
            # Show page breakdown
            for i, page in enumerate(page_info[:5]):  # Show first 5 pages
                st.write(f"- Page {page['page_num']}: {len(page['text'])} characters")
            if len(page_info) > 5:
                st.write(f"- ... and {len(page_info) - 5} more pages")
        
        return full_document_text, page_markers
        
    except Exception as e:
        st.error(f"Error extracting document text: {str(e)}")
        return None, None

def extract_comprehensive_financial_statements(full_document_text, page_markers):
    """Extract complete financial statements using whole-document context with IFRS template"""
    try:
        st.info("🧠 Analyzing entire document with AI for comprehensive financial statement extraction...")
        
        # Check document size for token limits
        estimated_tokens = len(full_document_text) // 4  # Rough estimate: 4 chars per token
        if estimated_tokens > 100000:  # Conservative limit for GPT-4
            st.warning(f"⚠️ Large document detected ({estimated_tokens:,} estimated tokens). Processing may take longer.")
        
        # Comprehensive IFRS-based template prompt
        prompt = f"""
        You are a professional financial analyst specializing in comprehensive financial statement extraction. 
        
        Analyze the ENTIRE document provided below and extract ALL financial data to create complete financial statements using IFRS standards.

        DOCUMENT ANALYSIS APPROACH:
        1. READ the entire document to understand the company and reporting structure
        2. IDENTIFY all financial statement sections (Balance Sheet, Income Statement, Cash Flow, Equity)
        3. EXTRACT all line items with their values across all years present
        4. ORGANIZE into the comprehensive IFRS template below
        5. CROSS-VALIDATE that data is consistent across statements

        CURRENCY AND NUMBER HANDLING:
        - Handle all currency symbols (₱, $, €, £, ¥, etc.)
        - Parse parentheses as NEGATIVE numbers: ₱(26,278) = -26278
        - Handle comma-separated numbers: ₱249,788,478 = 249788478
        - Remove currency symbols and return just numeric values
        - If no clear number found, set value to null and confidence to 0.1

        YEAR HANDLING (DYNAMIC):
        - Identify ALL years present in the document
        - Use relative positioning: base_year (most recent/leftmost), year_1, year_2, year_3
        - Record actual years found for reference
        - Only include year fields that have actual data

        COMPREHENSIVE IFRS TEMPLATE - Fill ALL sections found in the document:

        {{
            "company_name": "extracted company name",
            "reporting_period": "extracted reporting period",
            "currency": "extracted currency (PHP, USD, EUR, etc.)",
            "accounting_standards": "IFRS, US GAAP, or other standards mentioned",
            "years_detected": ["2024", "2023", "2022"],  // actual years found
            "base_year": "2024",  // most recent or leftmost year
            "year_ordering": "most_recent_first" or "chronological",
            
            "balance_sheet": {{
                "current_assets": {{
                    "cash_and_cash_equivalents": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number, "year_2": number}},
                    "trade_and_other_current_receivables": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "current_inventories": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "current_biological_assets": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "current_tax_assets": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "other_current_assets": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "total_current_assets": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}}
                }},
                "non_current_assets": {{
                    "property_plant_and_equipment": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "investment_property": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "goodwill": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "other_intangible_assets": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "investments_in_subsidiaries": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "investments_in_associates": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "non_current_biological_assets": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "deferred_tax_assets": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "other_non_current_assets": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "total_non_current_assets": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}}
                }},
                "total_assets": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                
                "current_liabilities": {{
                    "current_provisions_for_employee_benefits": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "other_current_provisions": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "trade_and_other_current_payables": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "current_tax_liabilities": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "other_current_financial_liabilities": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "other_current_liabilities": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "total_current_liabilities": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}}
                }},
                "non_current_liabilities": {{
                    "non_current_provisions_for_employee_benefits": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "other_non_current_provisions": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "deferred_tax_liabilities": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "other_non_current_financial_liabilities": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "other_non_current_liabilities": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "total_non_current_liabilities": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}}
                }},
                "total_liabilities": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                
                "equity": {{
                    "issued_share_capital": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "share_premium": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "treasury_shares": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "other_reserves": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "retained_earnings": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "non_controlling_interests": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "total_equity": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}}
                }}
            }},
            
            "income_statement": {{
                "revenue": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number, "year_2": number}},
                "cost_of_sales": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "gross_profit": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "other_income": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "distribution_costs": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "administrative_expenses": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "other_expenses": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "gains_losses_on_net_monetary_position": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "finance_income": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "finance_costs": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "share_of_profit_loss_of_associates": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "profit_loss_before_tax": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "income_tax_expense": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "profit_loss_from_continuing_operations": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "profit_loss_from_discontinued_operations": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "profit_loss": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "other_comprehensive_income": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "total_comprehensive_income": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}}
            }},
            
            "cash_flow_statement": {{
                "operating_activities": {{
                    "profit_loss_before_tax": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "depreciation_and_amortization": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "interest_expense": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "other_non_cash_expenses": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "changes_in_working_capital": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "income_taxes_paid": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "net_cash_from_operating_activities": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}}
                }},
                "investing_activities": {{
                    "acquisition_of_property_plant_equipment": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "proceeds_from_disposal_of_assets": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "acquisition_of_investments": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "net_cash_from_investing_activities": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}}
                }},
                "financing_activities": {{
                    "proceeds_from_borrowings": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "repayment_of_borrowings": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "principal_payments_on_lease_liabilities": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "interest_payments": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "dividends_paid": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                    "net_cash_from_financing_activities": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}}
                }},
                "net_increase_decrease_in_cash": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "cash_at_beginning_of_period": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "cash_at_end_of_period": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}}
            }},
            
            "statement_of_changes_in_equity": {{
                "beginning_balance_retained_earnings": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "profit_loss_for_period": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "other_comprehensive_income": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "dividends_declared": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "share_capital_changes": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}},
                "ending_balance_retained_earnings": {{"value": number, "confidence": 0.0-1.0, "base_year": number, "year_1": number}}
            }},
            
            "summary_metrics": {{
                "total_assets": {{"value": number, "confidence": 0.0-1.0}},
                "total_liabilities": {{"value": number, "confidence": 0.0-1.0}},
                "total_equity": {{"value": number, "confidence": 0.0-1.0}},
                "total_revenue": {{"value": number, "confidence": 0.0-1.0}},
                "gross_profit": {{"value": number, "confidence": 0.0-1.0}},
                "net_income": {{"value": number, "confidence": 0.0-1.0}},
                "operating_cash_flow": {{"value": number, "confidence": 0.0-1.0}}
            }},
            
            "validation_checks": {{
                "balance_sheet_balances": true/false,  // Assets = Liabilities + Equity
                "cash_flow_reconciles": true/false,    // Cash flow matches balance sheet cash changes
                "equity_statement_matches": true/false, // Equity changes match balance sheet
                "multi_year_consistency": true/false   // Year-over-year changes are reasonable
            }},
            
            "extraction_metadata": {{
                "total_line_items_extracted": number,
                "pages_with_financial_data": [page_numbers],
                "extraction_confidence": 0.0-1.0,
                "missing_critical_items": ["list of important items not found"],
                "notes": "observations about document structure, data quality, assumptions made"
            }}
        }}

        CRITICAL EXTRACTION GUIDELINES:

        1. **COMPREHENSIVE EXTRACTION**: Extract ALL financial line items found in the document
        2. **CROSS-REFERENCE**: Use the entire document context to find related information
        3. **VALIDATE**: Ensure mathematical consistency across statements
        4. **ADAPT**: If document uses different terminology, map to IFRS fields appropriately
        5. **MULTI-YEAR**: Extract all years of data available
        6. **CONFIDENCE**: Set appropriate confidence levels based on clarity of source data

        CONFIDENCE SCORING:
        - 0.9-1.0: Crystal clear, unambiguous values with clear labels
        - 0.7-0.9: Clear values with minor formatting complexity
        - 0.5-0.7: Somewhat unclear but reasonable interpretation
        - 0.3-0.5: Uncertain, multiple possible interpretations
        - 0.1-0.3: Very uncertain or barely visible

        VALIDATION REQUIREMENTS:
        - Balance Sheet must balance (Assets = Liabilities + Equity)
        - Cash flow statement ending cash should match balance sheet cash
        - Equity changes should be consistent between statements
        - Multi-year data should show reasonable progression

        DOCUMENT TO ANALYZE:
        {full_document_text}

        Extract comprehensive financial statements following the IFRS template above. Be thorough and accurate.
        """

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=4000
        )

        # Parse the JSON response
        content = response.choices[0].message.content
        
        if not content:
            return None
        
        # Extract JSON from the response
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            return None
            
        json_str = content[start_idx:end_idx]
        extracted_data = json.loads(json_str)
        
        # Add processing metadata
        extracted_data['processing_method'] = 'whole_document_context'
        extracted_data['document_pages'] = len(page_markers)
        extracted_data['document_size_chars'] = len(full_document_text)
        
        st.success("✅ Comprehensive financial statements extracted using whole-document context!")
        
        return extracted_data
        
    except Exception as e:
        st.error(f"Error in comprehensive extraction: {str(e)}")
        return None

def process_pdf_with_whole_document_context(uploaded_file):
    """Process PDF using whole-document context approach for comprehensive extraction"""
    try:
        st.info("🚀 Starting whole-document context analysis...")
        
        # Phase 1: Extract full document text
        full_document_text, page_markers = extract_full_document_text(uploaded_file)
        if not full_document_text:
            st.error("Failed to extract document text")
            return None
        
        # Phase 2: Comprehensive extraction using entire document context
        extracted_data = extract_comprehensive_financial_statements(full_document_text, page_markers)
        if not extracted_data:
            st.error("Failed to extract financial statements")
            return None
        
        # Phase 3: Display extraction summary
        st.success("🎯 Whole-document context extraction completed!")
        
        with st.expander("📊 Extraction Summary", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Company", extracted_data.get("company_name", "Not found"))
            with col2:
                st.metric("Currency", extracted_data.get("currency", "Not found"))
            with col3:
                years = extracted_data.get("years_detected", [])
                st.metric("Years", f"{len(years)} years" if years else "Not found")
            with col4:
                metadata = extracted_data.get("extraction_metadata", {})
                line_items = metadata.get("total_line_items_extracted", 0)
                st.metric("Line Items", line_items)
        
        return extracted_data
        
    except Exception as e:
        st.error(f"Error in whole-document processing: {str(e)}")
        return None

def display_ifrs_financial_statements(data):
    """Display comprehensive IFRS financial statements extracted using whole-document context"""
    if not data:
        return None
        
    st.markdown('<div class="results-section">', unsafe_allow_html=True)
    
    # Company Information Header
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Company", data.get("company_name", "Not found"))
    with col2:
        st.metric("Currency", data.get("currency", "Not found"))
    with col3:
        years = data.get("years_detected", [])
        st.metric("Years", f"{len(years)} years" if years else "Not found")
    with col4:
        standards = data.get("accounting_standards", "Not specified")
        st.metric("Standards", standards)
    
    # Show year mapping
    if years and len(years) > 1:
        base_year = data.get("base_year", "Unknown")
        st.info(f"📅 **Year Mapping:** Base Year = {base_year}, " + 
               ", ".join([f"Year {i} = {year}" for i, year in enumerate(years[1:], 1)]))
    
    st.markdown("---")
    
    # Summary Metrics
    st.subheader("📊 Key Financial Metrics")
    summary_metrics = data.get("summary_metrics", {})
    
    if summary_metrics:
        cols = st.columns(4)
        metrics = [
            ("Total Assets", "total_assets"),
            ("Total Revenue", "total_revenue"), 
            ("Net Income", "net_income"),
            ("Operating Cash Flow", "operating_cash_flow")
        ]
        
        for i, (label, key) in enumerate(metrics):
            if key in summary_metrics and summary_metrics[key].get("value") is not None:
                with cols[i % 4]:
                    value = summary_metrics[key]["value"]
                    confidence = summary_metrics[key].get("confidence", 0)
                    st.metric(
                        label,
                        f"{value:,.0f}",
                        help=f"Confidence: {confidence:.1%}"
                    )
    
    st.markdown("---")
    
    # Balance Sheet
    balance_sheet = data.get("balance_sheet", {})
    if balance_sheet:
        st.subheader("🏦 Balance Sheet")
        
        # Current Assets
        current_assets = balance_sheet.get("current_assets", {})
        if current_assets:
            st.markdown("### Current Assets")
            for field, info in current_assets.items():
                if isinstance(info, dict) and info.get("value") is not None:
                    display_financial_line_item(field, info, years)
        
        # Non-Current Assets  
        non_current_assets = balance_sheet.get("non_current_assets", {})
        if non_current_assets:
            st.markdown("### Non-Current Assets")
            for field, info in non_current_assets.items():
                if isinstance(info, dict) and info.get("value") is not None:
                    display_financial_line_item(field, info, years)
        
        # Total Assets
        total_assets = balance_sheet.get("total_assets", {})
        if total_assets and total_assets.get("value") is not None:
            st.markdown("### **Total Assets**")
            display_financial_line_item("total_assets", total_assets, years)
        
        # Current Liabilities
        current_liabilities = balance_sheet.get("current_liabilities", {})
        if current_liabilities:
            st.markdown("### Current Liabilities")
            for field, info in current_liabilities.items():
                if isinstance(info, dict) and info.get("value") is not None:
                    display_financial_line_item(field, info, years)
        
        # Non-Current Liabilities
        non_current_liabilities = balance_sheet.get("non_current_liabilities", {})
        if non_current_liabilities:
            st.markdown("### Non-Current Liabilities")
            for field, info in non_current_liabilities.items():
                if isinstance(info, dict) and info.get("value") is not None:
                    display_financial_line_item(field, info, years)
        
        # Total Liabilities
        total_liabilities = balance_sheet.get("total_liabilities", {})
        if total_liabilities and total_liabilities.get("value") is not None:
            st.markdown("### **Total Liabilities**")
            display_financial_line_item("total_liabilities", total_liabilities, years)
        
        # Equity
        equity = balance_sheet.get("equity", {})
        if equity:
            st.markdown("### Equity")
            for field, info in equity.items():
                if isinstance(info, dict) and info.get("value") is not None:
                    display_financial_line_item(field, info, years)
    
    st.markdown("---")
    
    # Income Statement
    income_statement = data.get("income_statement", {})
    if income_statement:
        st.subheader("💰 Income Statement")
        for field, info in income_statement.items():
            if isinstance(info, dict) and info.get("value") is not None:
                display_financial_line_item(field, info, years)
    
    st.markdown("---")
    
    # Cash Flow Statement
    cash_flow = data.get("cash_flow_statement", {})
    if cash_flow:
        st.subheader("💸 Cash Flow Statement")
        
        # Operating Activities
        operating = cash_flow.get("operating_activities", {})
        if operating:
            st.markdown("### Operating Activities")
            for field, info in operating.items():
                if isinstance(info, dict) and info.get("value") is not None:
                    display_financial_line_item(field, info, years)
        
        # Investing Activities
        investing = cash_flow.get("investing_activities", {})
        if investing:
            st.markdown("### Investing Activities")
            for field, info in investing.items():
                if isinstance(info, dict) and info.get("value") is not None:
                    display_financial_line_item(field, info, years)
        
        # Financing Activities
        financing = cash_flow.get("financing_activities", {})
        if financing:
            st.markdown("### Financing Activities")
            for field, info in financing.items():
                if isinstance(info, dict) and info.get("value") is not None:
                    display_financial_line_item(field, info, years)
        
        # Net Cash Changes
        for field in ["net_increase_decrease_in_cash", "cash_at_beginning_of_period", "cash_at_end_of_period"]:
            info = cash_flow.get(field, {})
            if isinstance(info, dict) and info.get("value") is not None:
                display_financial_line_item(field, info, years)
    
    st.markdown("---")
    
    # Statement of Changes in Equity
    equity_statement = data.get("statement_of_changes_in_equity", {})
    if equity_statement:
        st.subheader("🏛️ Statement of Changes in Equity")
        for field, info in equity_statement.items():
            if isinstance(info, dict) and info.get("value") is not None:
                display_financial_line_item(field, info, years)
    
    st.markdown("---")
    
    # Validation Results
    validation = data.get("validation_checks", {})
    if validation:
        st.subheader("✅ Validation Results")
        col1, col2, col3, col4 = st.columns(4)
        
        checks = [
            ("Balance Sheet Balances", "balance_sheet_balances"),
            ("Cash Flow Reconciles", "cash_flow_reconciles"),
            ("Equity Statement Matches", "equity_statement_matches"),
            ("Multi-Year Consistency", "multi_year_consistency")
        ]
        
        for i, (label, key) in enumerate(checks):
            with [col1, col2, col3, col4][i]:
                if key in validation:
                    status = "✅ Pass" if validation[key] else "❌ Fail"
                    st.metric(label, status)
    
    # Extraction Metadata
    metadata = data.get("extraction_metadata", {})
    if metadata:
        st.subheader("📈 Extraction Quality")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            line_items = metadata.get("total_line_items_extracted", 0)
            st.metric("Line Items Extracted", line_items)
        
        with col2:
            confidence = metadata.get("extraction_confidence", 0)
            st.metric("Overall Confidence", f"{confidence:.1%}")
        
        with col3:
            pages = metadata.get("pages_with_financial_data", [])
            st.metric("Financial Pages", len(pages) if pages else 0)
        
        # Missing items
        missing = metadata.get("missing_critical_items", [])
        if missing:
            st.warning(f"⚠️ **Missing Critical Items:** {', '.join(missing)}")
        
        # Notes
        notes = metadata.get("notes", "")
        if notes:
            st.info(f"📝 **Notes:** {notes}")
    
    # Export Options
    st.subheader("📤 Export Data")
    col1, col2 = st.columns(2)
    
    with col1:
        # Create comprehensive CSV
        csv_data = create_ifrs_csv_export(data)
        st.download_button(
            label="📄 Download Complete IFRS CSV",
            data=csv_data,
            file_name=f"ifrs_financial_statements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key=f"download_ifrs_csv_{abs(hash(str(data))) % 10000}"
        )
    
    with col2:
        # JSON export
        json_data = json.dumps(data, indent=2)
        st.download_button(
            label="📋 Download JSON Data",
            data=json_data,
            file_name=f"ifrs_financial_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            key=f"download_ifrs_json_{abs(hash(str(data))) % 10000}"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    return True

def display_financial_line_item(field_name, info, years):
    """Display a single financial line item with multi-year data"""
    # Prepare year data
    year_data = {}
    base_year = info.get("base_year")
    if base_year is not None:
        year_data[years[0] if years else "Base"] = base_year
    
    for i, year in enumerate(years[1:], 1):
        year_key = f"year_{i}"
        if year_key in info and info[year_key] is not None:
            year_data[year] = info[year_key]
    
    # Display line item
    if len(year_data) > 1:
        # Multi-year display
        st.write(f"**{field_name.replace('_', ' ').title()}**")
        year_cols = st.columns(min(len(year_data) + 1, 5))
        
        with year_cols[0]:
            confidence = info.get("confidence", 0)
            confidence_class = get_confidence_class(confidence)
            st.markdown(f'<span class="{confidence_class}">{confidence:.1%}</span>', 
                      unsafe_allow_html=True)
        
        for idx, (year, value) in enumerate(year_data.items(), 1):
            if idx < len(year_cols):
                with year_cols[idx]:
                    st.metric(str(year), f"{value:,.0f}" if value else "N/A")
    else:
        # Single year display
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"**{field_name.replace('_', ' ').title()}**")
        with col2:
            value = info.get("value", 0)
            st.write(f"{value:,.0f}" if value else "N/A")
        with col3:
            confidence = info.get("confidence", 0)
            confidence_class = get_confidence_class(confidence)
            st.markdown(f'<span class="{confidence_class}">{confidence:.1%}</span>', 
                      unsafe_allow_html=True)

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

# Update the main function to include whole-document context option
# ... existing code ...

if __name__ == "__main__":
    main() 