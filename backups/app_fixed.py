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
        pdf_processing_available = True
        pdf_library = "pymupdf"
    except ImportError:
        pdf_error_message = "Neither pdf2image (with Poppler) nor PyMuPDF available for PDF processing"

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Page configuration
st.set_page_config(
    page_title="Financial Statement Transcription Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .upload-section {
        border: 2px dashed #1f77b4;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    .results-section {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .confidence-high { color: #28a745; font-weight: bold; }
    .confidence-medium { color: #ffc107; font-weight: bold; }
    .confidence-low { color: #dc3545; font-weight: bold; }
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
            images = convert_from_bytes(pdf_file.getvalue(), dpi=200)
        elif pdf_library == "pymupdf":
            # Use PyMuPDF as fallback
            import fitz
            doc = fitz.open(stream=pdf_file.getvalue(), filetype="pdf")
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
    
    # Company Information
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Company", data.get("company_name", "Not found"))
    with col2:
        st.metric("Statement Type", data.get("statement_type", "Not identified"))
    with col3:
        st.metric("Period", data.get("period", "Not found"))
    
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
                                all_line_items.append({
                                    "Category": category.replace("_", " ").title(),
                                    "Subcategory": subcategory.replace("_", " ").title(),
                                    "Field": field.replace("_", " ").title(),
                                    "Value": info["value"],
                                    "Confidence": f"{info['confidence']:.1%}",
                                    "Confidence_Score": info["confidence"]
                                })
                                
                                # Display individual line item
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
                        all_line_items.append({
                            "Category": category.replace("_", " ").title(),
                            "Subcategory": "",
                            "Field": subcategory.replace("_", " ").title(),
                            "Value": subcategory_data["value"],
                            "Confidence": f"{subcategory_data['confidence']:.1%}",
                            "Confidence_Score": subcategory_data["confidence"]
                        })
                        
                        # Display individual line item
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
                    key="download_summary_csv"
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
    """Comprehensive financial data extraction agent that extracts ALL line items"""
    try:
        # Enhanced prompt for comprehensive line item extraction
        prompt = f"""
        You are a financial data extraction expert specializing in comprehensive line item analysis. 
        Analyze this {statement_type_hint} and extract ALL visible line items with their values.

        IMPORTANT: Focus on the specific statement type and extract ALL line items you can see, even if they don't fit the standard categories below.

        CURRENCY AND NUMBER HANDLING:
        - Handle Philippine Peso (₱) and other currency symbols (₱, $, €, £, ¥)
        - Parse parentheses as NEGATIVE numbers: ₱(26,278) = -26278
        - Handle comma-separated numbers: ₱249,788,478 = 249788478
        - Extract multi-year comparative data if present (e.g., 2024 and 2023 columns)
        - Remove currency symbols and return just the numeric values

        TERMINOLOGY RECOGNITION:
        - "Statements of Operations" = Income Statement
        - "Statement of Financial Position" = Balance Sheet  
        - "General & Admin Expenses" = Selling, General & Administrative
        - "Cost of Sales" = Cost of Revenue/Cost of Goods Sold
        - "Net Operating Income (Loss)" = Operating Income
        - Handle both IFRS and US GAAP terminology

        For BALANCE SHEET, extract:
        - Current Assets: Cash, accounts receivable, inventory, prepaid expenses, short-term investments, etc.
        - Non-Current Assets: Property/plant/equipment, intangible assets, long-term investments, etc.
        - Current Liabilities: Accounts payable, accrued expenses, short-term debt, current portion of long-term debt, etc.
        - Non-Current Liabilities: Long-term debt, deferred tax liabilities, pension obligations, etc.
        - Equity: Common stock, retained earnings, additional paid-in capital, accumulated other comprehensive income, etc.

        For INCOME STATEMENT (including "Statements of Operations"), extract:
        - Revenue: Total revenue, net sales, service revenue, product revenue, etc.
        - Cost of Revenue: Cost of goods sold, cost of services, cost of sales, etc.
        - Operating Expenses: Selling expenses, general & administrative, research & development, depreciation, marketing, etc.
        - Other Income/Expenses: Interest income, interest expense, foreign exchange gains/losses, other income, etc.
        - Tax and Final: Income tax expense, net income, earnings per share, comprehensive income, etc.

        For CASH FLOW STATEMENT, extract:
        - Operating Activities: Net income, depreciation, changes in working capital components, etc.
        - Investing Activities: Capital expenditures, acquisitions, asset sales, investment purchases/sales, etc.
        - Financing Activities: Debt issuance/repayment, equity transactions, dividend payments, etc.

        For EQUITY STATEMENT, extract:
        - Beginning balances for each equity component
        - Changes during the period (stock issuance, repurchases, dividends, etc.)
        - Ending balances for each equity component

        Return the data in this flexible JSON structure (only include sections relevant to the statement type):
        {{
            "statement_type": "Balance Sheet" or "Income Statement" or "Cash Flow Statement" or "Statement of Equity",
            "company_name": "extracted company name",
            "period": "extracted period/date",
            "currency": "extracted currency (PHP, USD, EUR, etc.)",
            "line_items": {{
                // For Balance Sheet
                "assets": {{
                    "current_assets": {{
                        "cash_and_cash_equivalents": {{"value": number, "confidence": 0.0-1.0}},
                        "accounts_receivable": {{"value": number, "confidence": 0.0-1.0}},
                        "inventory": {{"value": number, "confidence": 0.0-1.0}},
                        "prepaid_expenses": {{"value": number, "confidence": 0.0-1.0}},
                        "short_term_investments": {{"value": number, "confidence": 0.0-1.0}},
                        "other_current_assets": {{"value": number, "confidence": 0.0-1.0}},
                        "total_current_assets": {{"value": number, "confidence": 0.0-1.0}}
                    }},
                    "non_current_assets": {{
                        "property_plant_equipment": {{"value": number, "confidence": 0.0-1.0}},
                        "intangible_assets": {{"value": number, "confidence": 0.0-1.0}},
                        "long_term_investments": {{"value": number, "confidence": 0.0-1.0}},
                        "other_non_current_assets": {{"value": number, "confidence": 0.0-1.0}},
                        "total_non_current_assets": {{"value": number, "confidence": 0.0-1.0}}
                    }},
                    "total_assets": {{"value": number, "confidence": 0.0-1.0}}
                }},
                "liabilities": {{
                    "current_liabilities": {{
                        "accounts_payable": {{"value": number, "confidence": 0.0-1.0}},
                        "accrued_expenses": {{"value": number, "confidence": 0.0-1.0}},
                        "short_term_debt": {{"value": number, "confidence": 0.0-1.0}},
                        "current_portion_long_term_debt": {{"value": number, "confidence": 0.0-1.0}},
                        "other_current_liabilities": {{"value": number, "confidence": 0.0-1.0}},
                        "total_current_liabilities": {{"value": number, "confidence": 0.0-1.0}}
                    }},
                    "non_current_liabilities": {{
                        "long_term_debt": {{"value": number, "confidence": 0.0-1.0}},
                        "deferred_tax_liabilities": {{"value": number, "confidence": 0.0-1.0}},
                        "other_non_current_liabilities": {{"value": number, "confidence": 0.0-1.0}},
                        "total_non_current_liabilities": {{"value": number, "confidence": 0.0-1.0}}
                    }},
                    "total_liabilities": {{"value": number, "confidence": 0.0-1.0}}
                }},
                "equity": {{
                    "common_stock": {{"value": number, "confidence": 0.0-1.0}},
                    "retained_earnings": {{"value": number, "confidence": 0.0-1.0}},
                    "additional_paid_in_capital": {{"value": number, "confidence": 0.0-1.0}},
                    "accumulated_other_comprehensive_income": {{"value": number, "confidence": 0.0-1.0}},
                    "total_equity": {{"value": number, "confidence": 0.0-1.0}}
                }},
                
                // For Income Statement (including "Statements of Operations")
                "revenue": {{
                    "total_revenue": {{"value": number, "confidence": 0.0-1.0}},
                    "net_sales": {{"value": number, "confidence": 0.0-1.0}},
                    "service_revenue": {{"value": number, "confidence": 0.0-1.0}},
                    "product_revenue": {{"value": number, "confidence": 0.0-1.0}},
                    "other_revenue": {{"value": number, "confidence": 0.0-1.0}}
                }},
                "cost_of_revenue": {{
                    "cost_of_goods_sold": {{"value": number, "confidence": 0.0-1.0}},
                    "cost_of_services": {{"value": number, "confidence": 0.0-1.0}},
                    "cost_of_sales": {{"value": number, "confidence": 0.0-1.0}},
                    "total_cost_of_revenue": {{"value": number, "confidence": 0.0-1.0}},
                    "gross_profit": {{"value": number, "confidence": 0.0-1.0}}
                }},
                "operating_expenses": {{
                    "selling_general_administrative": {{"value": number, "confidence": 0.0-1.0}},
                    "general_admin_expenses": {{"value": number, "confidence": 0.0-1.0}},
                    "research_development": {{"value": number, "confidence": 0.0-1.0}},
                    "depreciation_amortization": {{"value": number, "confidence": 0.0-1.0}},
                    "marketing_expenses": {{"value": number, "confidence": 0.0-1.0}},
                    "other_operating_expenses": {{"value": number, "confidence": 0.0-1.0}},
                    "total_operating_expenses": {{"value": number, "confidence": 0.0-1.0}},
                    "operating_income": {{"value": number, "confidence": 0.0-1.0}},
                    "net_operating_income": {{"value": number, "confidence": 0.0-1.0}}
                }},
                "other_income_expenses": {{
                    "interest_income": {{"value": number, "confidence": 0.0-1.0}},
                    "interest_expense": {{"value": number, "confidence": 0.0-1.0}},
                    "other_income": {{"value": number, "confidence": 0.0-1.0}},
                    "other_expenses": {{"value": number, "confidence": 0.0-1.0}},
                    "foreign_exchange_gain_loss": {{"value": number, "confidence": 0.0-1.0}},
                    "income_before_taxes": {{"value": number, "confidence": 0.0-1.0}},
                    "net_income_before_tax": {{"value": number, "confidence": 0.0-1.0}},
                    "income_tax_expense": {{"value": number, "confidence": 0.0-1.0}},
                    "net_income": {{"value": number, "confidence": 0.0-1.0}},
                    "net_income_after_tax": {{"value": number, "confidence": 0.0-1.0}},
                    "earnings_per_share": {{"value": number, "confidence": 0.0-1.0}},
                    "other_comprehensive_income": {{"value": number, "confidence": 0.0-1.0}},
                    "total_comprehensive_income": {{"value": number, "confidence": 0.0-1.0}}
                }},
                
                // For Cash Flow Statement
                "cash_flows": {{
                    "operating_activities": {{
                        "net_income": {{"value": number, "confidence": 0.0-1.0}},
                        "depreciation_amortization": {{"value": number, "confidence": 0.0-1.0}},
                        "changes_in_working_capital": {{"value": number, "confidence": 0.0-1.0}},
                        "changes_in_accounts_receivable": {{"value": number, "confidence": 0.0-1.0}},
                        "changes_in_inventory": {{"value": number, "confidence": 0.0-1.0}},
                        "changes_in_accounts_payable": {{"value": number, "confidence": 0.0-1.0}},
                        "net_cash_from_operating": {{"value": number, "confidence": 0.0-1.0}}
                    }},
                    "investing_activities": {{
                        "capital_expenditures": {{"value": number, "confidence": 0.0-1.0}},
                        "acquisitions": {{"value": number, "confidence": 0.0-1.0}},
                        "asset_sales": {{"value": number, "confidence": 0.0-1.0}},
                        "investment_purchases": {{"value": number, "confidence": 0.0-1.0}},
                        "net_cash_from_investing": {{"value": number, "confidence": 0.0-1.0}}
                    }},
                    "financing_activities": {{
                        "debt_issuance": {{"value": number, "confidence": 0.0-1.0}},
                        "debt_repayment": {{"value": number, "confidence": 0.0-1.0}},
                        "dividend_payments": {{"value": number, "confidence": 0.0-1.0}},
                        "stock_repurchases": {{"value": number, "confidence": 0.0-1.0}},
                        "net_cash_from_financing": {{"value": number, "confidence": 0.0-1.0}}
                    }}
                }},
                
                // For Equity Statement
                "equity_changes": {{
                    "common_stock_changes": {{
                        "beginning_balance": {{"value": number, "confidence": 0.0-1.0}},
                        "stock_issuance": {{"value": number, "confidence": 0.0-1.0}},
                        "stock_repurchases": {{"value": number, "confidence": 0.0-1.0}},
                        "ending_balance": {{"value": number, "confidence": 0.0-1.0}}
                    }},
                    "retained_earnings_changes": {{
                        "beginning_balance": {{"value": number, "confidence": 0.0-1.0}},
                        "net_income": {{"value": number, "confidence": 0.0-1.0}},
                        "dividends_paid": {{"value": number, "confidence": 0.0-1.0}},
                        "ending_balance": {{"value": number, "confidence": 0.0-1.0}}
                    }}
                }}
            }},
            "summary_metrics": {{
                "total_assets": {{"value": number, "confidence": 0.0-1.0}},
                "total_liabilities": {{"value": number, "confidence": 0.0-1.0}},
                "total_equity": {{"value": number, "confidence": 0.0-1.0}},
                "total_revenue": {{"value": number, "confidence": 0.0-1.0}},
                "net_income": {{"value": number, "confidence": 0.0-1.0}},
                "operating_cash_flow": {{"value": number, "confidence": 0.0-1.0}}
            }},
            "notes": "any important observations, assumptions, or data quality issues"
        }}

        CRITICAL RULES:
        - Extract ALL visible line items, not just the ones in the template above
        - If you see line items that don't fit the categories, create new categories or add them to "other" fields
        - Only include sections relevant to the statement type (don't include cash flows for balance sheet)
        - If a line item is not present or not visible, set value to null and confidence to 0.0
        - Be conservative with confidence scores - use 0.9+ only for very clear, unambiguous values
        - Include currency amounts without symbols (just numbers) - convert ₱249,788,478 to 249788478
        - Handle parentheses as negative numbers: ₱(26,278) becomes -26278
        - If amounts are in thousands/millions, convert to actual values and note in the notes field
        - Pay special attention to subtotals and ensure they're captured separately from individual line items
        - For Income Statements: Focus heavily on revenue breakdown, expense categories, and profitability metrics
        - For Equity Statements: Focus on changes in each equity component during the period
        - Extract multi-year data if present (e.g., both 2024 and 2023 columns)
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
            max_tokens=4000  # Increased for comprehensive extraction
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
        st.error(f"Error in comprehensive extraction: {str(e)}")
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
    """Main application function"""
    
    # Initialize session state
    if 'extracted_data' not in st.session_state:
        st.session_state.extracted_data = None
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'uploaded_file_name' not in st.session_state:
        st.session_state.uploaded_file_name = None
    
    # Initialize database
    init_database()
    
    # Header
    st.markdown('<h1 class="main-header">📊 Financial Statement Transcription Tool</h1>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    **Upload your financial statement (PDF or image) and let AI extract the key financial data automatically.**
    
    ✨ **AI-Powered Vision Processing**: All documents are processed using advanced AI vision technology for maximum accuracy with scanned documents.
    
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
            st.info("🔍 Using comprehensive vector database approach")
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
            col1, col2, col3 = st.columns(3)
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
        else:
            # Original single result display
            df = display_extracted_data(st.session_state.extracted_data)
        
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
        
        # Display file info
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
        
        with col2:
            # Display uploaded image (if it's an image)
            if uploaded_file.type.startswith('image'):
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Financial Statement", use_column_width=True)
        
        # Process button - only show if new file or no previous results
        if is_new_file or not st.session_state.processing_complete:
            if st.button("🚀 Extract Financial Data", type="primary"):
                # Clear previous results for new file
                if is_new_file:
                    st.session_state.extracted_data = None
                    st.session_state.processing_complete = False
                
                start_time = datetime.now()
                
                with st.spinner("🤖 AI is analyzing your financial statement..."):
                    # Determine file type
                    if uploaded_file.type == "application/pdf":
                        if not pdf_processing_available:
                            st.error("❌ PDF processing is not available. Please install pdf2image for PDF support.")
                            return
                        file_type = "pdf"
                    elif uploaded_file.type in ["image/jpeg", "image/jpg"]:
                        file_type = "jpeg"
                    elif uploaded_file.type == "image/png":
                        file_type = "png"
                    else:
                        st.error("Unsupported file type. Please upload a PDF, JPG, or PNG file.")
                        return
                    
                    # Use faster processing for single images
                    if file_type in ["jpeg", "png"]:
                        extracted_data = extract_financial_data(uploaded_file, file_type)
                    else:
                        # For PDFs, use the comprehensive vector database approach
                        extracted_data = process_pdf_with_vector_db(uploaded_file, client)
                    
                    processing_time = (datetime.now() - start_time).total_seconds()
                    
                    if extracted_data:
                        # Store results in session state
                        st.session_state.extracted_data = extracted_data
                        st.session_state.processing_complete = True
                        st.session_state.uploaded_file_name = uploaded_file.name
                        
                        # Calculate confidence
                        if isinstance(extracted_data, dict) and "financial_data" in extracted_data:
                            financial_data = extracted_data.get("financial_data", {})
                            confidences = [info["confidence"] for info in financial_data.values() 
                                         if isinstance(info, dict) and info.get("confidence", 0) > 0]
                            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                        else:
                            avg_confidence = 0.8  # Default for other formats
                        
                        # Log processing
                        log_processing(uploaded_file.name, processing_time, avg_confidence, "success")
                        
                        st.success(f"✅ Data extracted successfully in {processing_time:.1f} seconds!")
                        st.rerun()  # Refresh to show results
                        
                    else:
                        log_processing(uploaded_file.name, processing_time, 0, "failed")
                        st.error("❌ Failed to extract data from the document. Please try with a clearer image or different document.")
        else:
            st.info("✅ This file has already been processed. Results are shown above.")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Financial Statement Transcription Tool MVP | Powered by OpenAI GPT-4 Vision</p>
        <p>⚠️ This is a prototype. Please verify all extracted data before use.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 
