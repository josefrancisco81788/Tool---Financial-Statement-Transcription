# 📊 Financial Statement Transcription Tool

An AI-powered tool for extracting and analyzing financial data from PDF documents and images using OpenAI's GPT-4 Vision API.

## 🌟 Features

### Core Functionality
- **Multi-format Support**: Process PDF files, PNG, JPG, and JPEG images
- **AI-Powered Extraction**: Uses OpenAI GPT-4 Vision for intelligent financial data recognition
- **Two Processing Approaches**: Choose between comprehensive whole-document analysis or intelligent page-by-page processing
- **Real-time Processing**: Live progress tracking with parallel processing capabilities

### Processing Approaches

#### 🌐 Whole Document Context
- **Best for**: Small to medium documents (≤30 pages)
- **Features**:
  - Processes entire document as context
  - Superior relationship detection between statements
  - Comprehensive cross-statement analysis
  - Maximum context understanding

#### 🗄️ Vector Database Analysis
- **Best for**: Large documents (>30 pages)
- **Features**:
  - Intelligent page classification with enhanced algorithms
  - Parallel processing with 10 workers
  - Enhanced number density scoring
  - Case-insensitive pattern matching
  - Semantic search capabilities with ChromaDB

### Advanced Features
- **Smart Document Analysis**: Automatic recommendation of optimal processing approach
- **Enhanced Classification**: Universal financial statement pattern recognition
- **Multi-year Data Support**: Handles comparative financial statements
- **Data Validation**: Cross-statement consistency checks
- **Export Options**: CSV export with detailed and summary formats
- **Session Management**: Persistent results with smart caching

## 🚀 Quick Start

### Access Methods

#### 🌐 Streamlit Web Interface
Use the interactive web interface for document upload and analysis.

#### 🔌 API Access
For programmatic access and integration, use our REST API:
- **API Documentation**: See [API_GUIDE.md](API_GUIDE.md)
- **Endpoints**: `/extract`, `/health`, `/docs`
- **Cloud Ready**: Deploy on Google Cloud Run

### Prerequisites
- Python 3.8+
- OpenAI API key
- Poppler (for PDF processing) or PyMuPDF as fallback

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd financial-statement-transcription
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env_example.txt .env
   # Edit .env and add your OpenAI API key
   ```

4. **Install PDF processing (choose one)**
   
   **Option A: Poppler (Recommended)**
   - Windows: Download from [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases/)
   - Add to PATH environment variable
   
   **Option B: PyMuPDF (Fallback)**
   ```bash
   pip install PyMuPDF
   ```

### Running the Application

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## 📖 Usage Guide

### Basic Workflow

1. **Upload Document**: Choose a PDF or image file containing financial statements
2. **Document Analysis**: The system analyzes document characteristics and provides recommendations
3. **Select Processing Approach**: Choose between Whole Document Context or Vector Database Analysis
4. **Extract Data**: Click "Extract Financial Data" to begin AI processing
5. **Review Results**: Examine extracted data with confidence scores
6. **Export Data**: Download results in CSV format

### Processing Approach Selection

The system automatically analyzes your document and provides recommendations:

- **Small documents (≤10 pages, ≤5MB)**: Whole Document Context recommended
- **Medium documents (≤30 pages, ≤15MB)**: Either approach works well
- **Large documents (>30 pages, >15MB)**: Vector Database Analysis recommended

### Understanding Results

#### Confidence Scores
- **90-100%**: Crystal clear, unambiguous values
- **70-90%**: Clear values with minor formatting complexity
- **50-70%**: Somewhat unclear but reasonable interpretation
- **30-50%**: Uncertain, multiple possible interpretations
- **10-30%**: Very uncertain or barely visible

#### Data Organization
Results are organized by financial statement type:
- **Balance Sheet**: Assets, Liabilities, Equity
- **Income Statement**: Revenues, Expenses, Profitability
- **Cash Flow Statement**: Operating, Investing, Financing Activities
- **Statement of Equity**: Changes in shareholders' equity

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
OPENAI_API_KEY=your_openai_api_key_here
USE_FINANCIAL_EMBEDDINGS=false  # Optional: Enable financial-specific embeddings
```

### Advanced Configuration

#### Rate Limiting
The application includes built-in rate limiting with exponential backoff:
- Maximum 3 retries per API call
- Base delay: 1 second
- Maximum delay: 60 seconds

#### Parallel Processing
- **Text Extraction**: 5 workers for PDF page processing
- **Classification**: 10 workers for enhanced page analysis
- **Data Extraction**: 5 workers for financial data extraction

## 🧪 Testing

### Unit Tests
Run the button logic tests:
```bash
python test_button_logic.py
```

### Isolated Testing
Test button functionality in isolation:
```bash
streamlit run test_button_isolated.py --server.port 8549
```

### Manual Testing
1. Upload a sample financial statement
2. Test both processing approaches
3. Verify data extraction accuracy
4. Check export functionality

## 📁 Project Structure

```
financial-statement-transcription/
├── app.py                      # Main Streamlit application
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (create from env_example.txt)
├── render.yaml               # Deployment configuration
├── financial_statements.db   # SQLite database (ephemeral)
├── chroma_db/                # Vector database storage
├── backups/                  # Backup versions of the application
│   ├── app_backup.py         # Previous working version
│   ├── app_backup_before_fix.py # Version before fixes
│   ├── app_fixed.py          # Fixed version reference
│   └── app_button_fix.py     # Button fix version
├── tests/                    # Test and debug files
│   ├── test_button_logic.py  # Unit tests
│   ├── test_button_isolated.py # Isolated button test
│   ├── minimal_button_test.py # Minimal test case
│   ├── debug_button.py       # Button debugging
│   ├── debug_session_state.py # Session state debugging
│   ├── debug_test.py         # General debugging
│   ├── fix_button.py         # Button fix logic
│   ├── fix_button_clean.py   # Clean button fix
│   ├── fix_button_final.py   # Final button fix
│   └── fix_keys.py           # Key fix logic
├── scripts/                  # Utility and startup scripts
│   ├── start.ps1            # PowerShell startup script
│   ├── start.bat            # Windows batch startup
│   ├── start.sh             # Linux/Mac startup script
│   └── start-auto.ps1       # Automated startup script
└── docs/                    # Documentation files
    ├── README.md            # This file
    ├── MVP_PRD.md           # Minimum Viable Product requirements
    ├── Full_Version_PRD.md  # Full product requirements
    ├── troubleshoot_guide.md # Troubleshooting guide
    └── env_example.txt      # Environment template
```

## 🔍 Troubleshooting

### Common Issues

#### PDF Processing Not Available
**Error**: "PDF processing not available"
**Solution**: 
1. Install Poppler and add to PATH
2. Or install PyMuPDF: `pip install PyMuPDF`
3. Restart the application

#### Button Not Appearing
**Symptoms**: Extract button doesn't show after selecting approach
**Solutions**:
1. Check the Debug Info section
2. Use "Reset Session State" button
3. Refresh the page
4. Try the isolated test: `streamlit run tests/test_button_isolated.py`

#### API Rate Limits
**Error**: "Rate limit exceeded"
**Solution**: Wait a few minutes before retrying. The application includes automatic retry with exponential backoff.

#### Memory Issues with Large PDFs
**Symptoms**: Application crashes or becomes unresponsive
**Solutions**:
1. Use Vector Database approach for large documents
2. Reduce PDF file size
3. Process fewer pages at once

### Debug Mode
Enable debug information by expanding the "🔧 Debug Info" section when the Extract button appears.

### Running Tests
The project includes various test and debug files in the `tests/` directory:

```bash
# Run isolated button test
streamlit run tests/test_button_isolated.py

# Run button logic test
streamlit run tests/test_button_logic.py

# Run minimal test case
streamlit run tests/minimal_button_test.py
```

These tests can help isolate and debug specific issues with the application.

## 🚀 Deployment

### Local Development
```bash
streamlit run app.py --server.port 8501
```

### Startup Scripts
The `scripts/` directory contains platform-specific startup scripts:

- **Windows**: Use `scripts/start.bat` or `scripts/start.ps1`
- **Linux/Mac**: Use `scripts/start.sh`
- **Automated**: Use `scripts/start-auto.ps1` for automated startup

These scripts handle environment setup and application startup automatically.

### Production Deployment
The application includes configuration for deployment on Render.com:
- See `render.yaml` for deployment settings
- Use `start.sh` for startup configuration
- Environment variables configured through Render dashboard

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Poppler for PDF processing
RUN apt-get update && apt-get install -y poppler-utils

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## 📊 Performance

### Processing Times (Approximate)
- **Small PDF (5-10 pages)**: 30-60 seconds
- **Medium PDF (20-30 pages)**: 2-5 minutes
- **Large PDF (50+ pages)**: 5-15 minutes (Vector Database approach)

### Accuracy
- **High-quality scanned documents**: 85-95% accuracy
- **Native PDF text**: 90-98% accuracy
- **Poor quality images**: 60-80% accuracy

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add docstrings to new functions
- Include unit tests for new features
- Update README for significant changes

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Getting Help
1. Check the troubleshooting guide
2. Run the unit tests to identify issues
3. Use the isolated test for button problems
4. Check the debug information in the app

### Known Limitations
- Requires OpenAI API key (paid service)
- PDF processing requires additional dependencies
- Large documents may take significant processing time
- Accuracy depends on document quality

### Future Enhancements
- Support for additional file formats
- Enhanced financial statement templates
- Batch processing capabilities
- Advanced data validation rules
- Integration with accounting software

---

**Built with ❤️ using Streamlit and OpenAI GPT-4 Vision** 