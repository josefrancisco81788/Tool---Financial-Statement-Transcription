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

def extract_financial_data(image_file, file_type):
    """Extract financial data using OpenAI GPT-4 Vision"""
    try:
        base64_image = encode_image(image_file)
        
        prompt = """
        You are a financial data extraction expert. Analyze this financial statement image and extract the following key information:

        Please return the data in JSON format with the following structure:
        {
            "statement_type": "Income Statement" or "Balance Sheet" or "Cash Flow Statement",
            "company_name": "extracted company name",
            "period": "extracted period/date",
            "currency": "extracted currency",
            "financial_data": {
                "revenue": {"value": number, "confidence": 0.0-1.0},
                "total_expenses": {"value": number, "confidence": 0.0-1.0},
                "net_income": {"value": number, "confidence": 0.0-1.0},
                "total_assets": {"value": number, "confidence": 0.0-1.0},
                "total_liabilities": {"value": number, "confidence": 0.0-1.0},
                "equity": {"value": number, "confidence": 0.0-1.0},
                "cash_and_equivalents": {"value": number, "confidence": 0.0-1.0}
            },
            "notes": "any important observations or limitations"
        }

        Rules:
        - Extract only numerical values (no currency symbols)
        - If a field is not found, set value to null and confidence to 0.0
        - Confidence should reflect how certain you are about the extracted value
        - Be conservative with confidence scores
        """

        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{file_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )

        # Parse the JSON response
        content = response.choices[0].message.content
        
        # Check if content is None
        if not content:
            raise ValueError("Empty response from OpenAI API")
        
        # Extract JSON from the response (in case there's additional text)
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            raise ValueError("No valid JSON found in response")
            
        json_str = content[start_idx:end_idx]
        
        return json.loads(json_str)
        
    except Exception as e:
        st.error(f"Error extracting data: {str(e)}")
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
    
    # Financial Data
    st.subheader("📊 Extracted Financial Data")
    
    financial_data = data.get("financial_data", {})
    
    # Create editable dataframe
    df_data = []
    for field, info in financial_data.items():
        if info["value"] is not None:
            df_data.append({
                "Field": field.replace("_", " ").title(),
                "Value": info["value"],
                "Confidence": f"{info['confidence']:.1%}",
                "Confidence_Score": info["confidence"]
            })
    
    if df_data:
        df = pd.DataFrame(df_data)
        
        # Display with confidence color coding
        for idx, row in df.iterrows():
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(row["Field"])
            with col2:
                # Make value editable
                new_value = st.number_input(
                    f"Value for {row['Field']}", 
                    value=float(row["Value"]),
                    key=f"edit_{idx}",
                    format="%.2f"
                )
                df.loc[idx, "Value"] = new_value
            with col3:
                confidence_class = get_confidence_class(row["Confidence_Score"])
                st.markdown(f'<span class="{confidence_class}">{row["Confidence"]}</span>', 
                          unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Notes
        if data.get("notes"):
            st.subheader("📝 Notes")
            st.info(data["notes"])
        
        # Export options
        st.subheader("📤 Export Data")
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV Export
            csv = df[["Field", "Value", "Confidence"]].to_csv(index=False)
            st.download_button(
                label="📄 Download as CSV",
                data=csv,
                file_name=f"financial_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Copy to clipboard (JSON format)
            json_data = df[["Field", "Value"]].set_index("Field").to_dict()["Value"]
            st.code(json.dumps(json_data, indent=2), language="json")
        
        st.markdown('</div>', unsafe_allow_html=True)
        return df
    else:
        st.warning("No financial data could be extracted from the document.")
        return None

def main():
    """Main application function"""
    
    # Initialize database
    init_database()
    
    # Header
    st.markdown('<h1 class="main-header">📊 Financial Statement Transcription Tool</h1>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    **Upload your financial statement (PDF or image) and let AI extract the key financial data automatically.**
    
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
        
        st.markdown("---")
        
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
    
    # File upload section
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Choose a financial statement file",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        help="Upload a PDF or image file containing a financial statement"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file is not None:
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
        
        # Process button
        if st.button("🚀 Extract Financial Data", type="primary"):
            start_time = datetime.now()
            
            with st.spinner("🤖 AI is analyzing your financial statement..."):
                # Determine file type for API
                file_type = uploaded_file.type.split('/')[-1]
                if file_type == 'jpeg':
                    file_type = 'jpg'
                
                # Extract data
                extracted_data = extract_financial_data(uploaded_file, file_type)
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                if extracted_data:
                    # Calculate average confidence as accuracy score
                    financial_data = extracted_data.get("financial_data", {})
                    confidences = [info["confidence"] for info in financial_data.values() 
                                 if info["confidence"] > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                    
                    # Log processing
                    log_processing(uploaded_file.name, processing_time, avg_confidence, "success")
                    
                    # Display results
                    st.success(f"✅ Data extracted successfully in {processing_time:.1f} seconds!")
                    df = display_extracted_data(extracted_data)
                    
                    # Show processing stats
                    st.info(f"⏱️ Processing time: {processing_time:.1f} seconds | "
                           f"📊 Average confidence: {avg_confidence:.1%}")
                    
                else:
                    log_processing(uploaded_file.name, processing_time, 0, "failed")
                    st.error("❌ Failed to extract data from the document. Please try with a clearer image or different document.")

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