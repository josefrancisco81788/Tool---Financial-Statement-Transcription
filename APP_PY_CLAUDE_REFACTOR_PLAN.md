# Plan: Refactor app.py to Support Claude via FinancialDataExtractor

## Overview
Refactor `app.py` to use `FinancialDataExtractor` and `PDFProcessor` instead of direct OpenAI API calls, making it provider-agnostic and supporting Claude when `AI_PROVIDER=anthropic` is set.

## Current State Analysis

### Direct OpenAI Calls in app.py
1. **Line 176**: Global `client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))`
2. **Line 398-416**: `extract_text_with_vision_api()` - extracts text from images
3. **Line 448-478**: `extract_financial_data()` - single image extraction
4. **Line 1525-1543**: `extract_comprehensive_financial_data()` - comprehensive extraction
5. **Line 2310-2328**: `consolidate_financial_data()` - text-only consolidation call
6. **Line 2681-2696**: `process_pdf_with_whole_document_context()` - text-only comprehensive analysis

### Functions That Need Refactoring
- `extract_text_with_vision_api()` - currently uses `client.chat.completions.create()`
- `extract_financial_data()` - currently uses `client.chat.completions.create()` for single images
- `extract_comprehensive_financial_data()` - currently uses `client.chat.completions.create()`
- `process_pdf_with_vector_db()` - currently takes `client` parameter, calls `extract_text_with_vision_api()` and `extract_comprehensive_financial_data()`
- `process_pdf_with_whole_document_context()` - currently uses `client.chat.completions.create()` for text-only analysis
- `consolidate_financial_data()` - currently creates new OpenAI client and makes text-only API call
- `convert_pdf_to_images()` - currently calls `extract_text_with_vision_api()` which uses OpenAI

## Implementation Plan

### Phase 1: Update Imports and Initialize Extractors

**File: `app.py`**

1. **Add imports** (after line 16):
```python
from core.extractor import FinancialDataExtractor
from core.pdf_processor import PDFProcessor
```

2. **Add provider validation** (before client initialization, around line 172):
```python
# Validate provider configuration
if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
    st.error("❌ No API key found. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY in your .env file")
    st.stop()

provider = os.getenv("AI_PROVIDER", "anthropic").lower()
if provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
    st.error("❌ AI_PROVIDER=anthropic but ANTHROPIC_API_KEY not found")
    st.stop()
elif provider == "openai" and not os.getenv("OPENAI_API_KEY"):
    st.error("❌ AI_PROVIDER=openai but OPENAI_API_KEY not found")
    st.stop()
```

3. **Replace client initialization** (line 175-176):
```python
# OLD:
# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# NEW:
# Initialize financial data extractor and PDF processor (provider-agnostic)
extractor = FinancialDataExtractor()
pdf_processor = PDFProcessor(extractor)
```

### Phase 2: Add Helper Method for Text-Only API Calls

**File: `core/extractor.py`**

Add a new method after `_call_anthropic_api()` (around line 426):

```python
def _call_text_only_api(self, prompt: str, system_message: str = None, temperature: float = 0.1, max_tokens: int = 4000) -> str:
    """
    Make a text-only API call (no images) - provider-agnostic.
    
    Args:
        prompt: User prompt text
        system_message: Optional system message
        temperature: Temperature setting (default: 0.1)
        max_tokens: Maximum tokens (default: 4000)
        
    Returns:
        Response text from AI model
    """
    def api_call():
        if self.provider == "openai":
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            response = self.openai_client.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        elif self.provider == "anthropic":
            messages = []
            if system_message:
                messages.append({"role": "user", "content": f"{system_message}\n\n{prompt}"})
            else:
                messages.append({"role": "user", "content": prompt})
            
            response = self.anthropic_client.messages.create(
                model=self.config.ANTHROPIC_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.content[0].text if isinstance(response.content, list) else response.content
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    return self.exponential_backoff_retry(api_call)
```

### Phase 3: Replace extract_text_with_vision_api()

**File: `app.py`**

Replace function starting at line 380:

```python
def extract_text_with_vision_api(pil_image, page_num):
    """Extract text from image using AI Vision API - provider-agnostic"""
    try:
        # Encode image
        base64_image = encode_pil_image(pil_image)
        
        # Use PDFProcessor's text extraction method (which uses extractor)
        text = pdf_processor._extract_text_with_vision_api(pil_image, page_num)
        return text
        
    except Exception as e:
        raise Exception(f"Error extracting text from page {page_num}: {str(e)}")
```

### Phase 4: Replace extract_financial_data() for Single Images

**File: `app.py`**

Replace function starting at line 434:

```python
def extract_financial_data(image_file, file_type):
    """Extract financial data using AI Vision - provider-agnostic"""
    try:
        # Handle PDF files with vector database approach
        if file_type == 'pdf':
            st.info("🔍 Processing PDF with AI-powered semantic analysis...")
            return process_pdf_with_vector_db(image_file, enable_parallel=True)
        
        # Handle single image files
        else:
            st.info("🔍 Analyzing image with AI...")
            base64_image = encode_image(image_file)
            
            # Use extractor's comprehensive extraction method
            extracted_data = extractor.extract_comprehensive_financial_data(
                base64_image=base64_image,
                statement_type_hint="financial statement",
                page_text=""
            )
            
            # Return as string (for compatibility with existing code)
            return json.dumps(extracted_data, indent=2)
            
    except Exception as e:
        st.error(f"Error extracting financial data: {str(e)}")
        return None
```

### Phase 5: Replace process_pdf_with_vector_db()

**File: `app.py`**

Replace function signature and implementation starting at line 1807:

**Important**: The current function contains Streamlit UI elements (st.info, st.success, progress bars, etc.) that must be preserved. The PDFProcessor method doesn't include UI elements, so we wrap it with Streamlit feedback.

```python
def process_pdf_with_vector_db(uploaded_file, enable_parallel=True):
    """
    Process PDF using comprehensive vector database approach for large documents.
    Now uses PDFProcessor which is provider-agnostic.
    """
    try:
        st.info("🔍 Processing PDF with AI-powered semantic analysis...")
        
        # Use PDFProcessor's method (already provider-agnostic)
        # Note: This replaces the old implementation but preserves Streamlit UI feedback
        extracted_data = pdf_processor.process_pdf_with_vector_db(
            pdf_file=uploaded_file,
            enable_parallel=enable_parallel
        )
        
        if not extracted_data:
            st.warning("⚠️ No data extracted from PDF")
            return None
        
        # Check if we need to transform the format
        # PDFProcessor returns data in template_mappings format
        # Compare with expected format and transform if needed
        
        st.success(f"✅ Successfully processed PDF")
        return extracted_data
        
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return None
```

**Note**: The old implementation had complex Streamlit UI with progress tracking, page previews, and consolidation summaries. If those are critical, we may need to:
1. Keep some UI building logic while using PDFProcessor for the actual processing
2. Or enhance PDFProcessor to accept a callback for progress updates
3. Or extract the UI logic into a separate function that wraps the PDFProcessor call

Review the old implementation (lines 1807-2400) to identify which UI elements are essential and preserve them.

### Phase 6: Replace consolidate_financial_data()

**File: `app.py`**

Replace function starting at line ~2250 (find consolidate_financial_data function):

```python
def consolidate_financial_data(extracted_results):
    """
    Consolidate financial data from multiple pages using AI - provider-agnostic.
    """
    # ... existing consolidation_prompt building code remains the same ...
    
    # Use extractor's text-only API call method
    response_text = extractor._call_text_only_api(
        prompt=consolidation_prompt,
        system_message="You are a financial data consolidation expert. Analyze multiple financial statement extractions and create a single, accurate, consolidated financial statement using standard financial terminology and hierarchical organization.",
        temperature=0.1,
        max_tokens=4000
    )
    
    # Parse the response (existing parsing logic remains the same)
    content = response_text.strip()
    
    # ... rest of existing parsing and transformation logic remains the same ...
```

### Phase 7: Replace process_pdf_with_whole_document_context()

**File: `app.py`**

Replace function starting at line 2481:

```python
def process_pdf_with_whole_document_context(uploaded_file):
    """
    Process PDF using whole document context approach for comprehensive analysis.
    Now provider-agnostic.
    """
    try:
        # Convert PDF to images and extract text from ALL pages
        images, page_info = convert_pdf_to_images(uploaded_file, enable_parallel=True)
        if not images or not page_info:
            return None

        # ... existing prompt building code remains the same ...
        
        # Use extractor's text-only API call method instead of direct client call
        response_text = extractor._call_text_only_api(
            prompt=comprehensive_prompt,
            system_message="You are a comprehensive financial analysis expert. Analyze the entire document context to extract complete, validated financial data with cross-statement verification.",
            temperature=0.1,
            max_tokens=4000
        )
        
        # Parse the response (existing parsing logic remains the same)
        content = response_text.strip()
        
        # ... rest of existing parsing and transformation logic remains the same ...
```

### Phase 8: Replace extract_comprehensive_financial_data()

**File: `app.py`**

Replace function starting at line 1353:

```python
def extract_comprehensive_financial_data(base64_image, statement_type_hint, page_text=""):
    """
    Extract comprehensive financial data using extractor (provider-agnostic).
    """
    try:
        # Use extractor's comprehensive extraction method
        extracted_data = extractor.extract_comprehensive_financial_data(
            base64_image=base64_image,
            statement_type_hint=statement_type_hint,
            page_text=page_text
        )
        
        return extracted_data
        
    except Exception as e:
        raise Exception(f"Error in comprehensive extraction: {str(e)}")
```

### Phase 9: Update convert_pdf_to_images()

**File: `app.py`**

Replace function starting at line 240:

```python
def convert_pdf_to_images(pdf_file, enable_parallel=True):
    """Convert PDF to images and extract text using AI Vision API - provider-agnostic"""
    try:
        # Use PDFProcessor's convert_pdf_to_images method
        images, page_info = pdf_processor.convert_pdf_to_images(
            pdf_file=pdf_file,
            enable_parallel=enable_parallel
        )
        
        return images, page_info
        
    except Exception as e:
        st.error(f"Error converting PDF: {str(e)}")
        return None, None
```

### Phase 10: Update Function Calls

**File: `app.py`**

1. **Line ~3540**: Update `process_pdf_with_vector_db()` call:
```python
# OLD:
extracted_data = process_pdf_with_vector_db(uploaded_file, client)

# NEW:
extracted_data = process_pdf_with_vector_db(uploaded_file, enable_parallel=True)
```

2. **Line ~3541**: Update `process_pdf_with_whole_document_context()` call:
```python
# OLD:
extracted_data = process_pdf_with_whole_document_context(uploaded_file, client)

# NEW:
extracted_data = process_pdf_with_whole_document_context(uploaded_file)
```

3. **Line ~1894**: Update `extract_financial_data_for_page()` inside `process_pdf_with_vector_db()`:
   - This function calls `extract_comprehensive_financial_data()` which will now use the extractor
   - No signature changes needed, but ensure it uses the global `extractor` variable

### Phase 11: Remove Unused OpenAI Import

**File: `app.py`**

Remove or comment out (line 11):
```python
# from openai import OpenAI  # No longer needed - using FinancialDataExtractor
```

### Phase 12: Update Error Messages

**File: `app.py`**

Update references to "OpenAI" in error messages and UI text to be provider-agnostic:
- Line ~3052: Update API key check message
- Line ~3627: Update footer text
- Any other references to "OpenAI" or "GPT-4"

## Testing Checklist

### Pre-Implementation Testing
1. **Verify Current Tests Still Pass**
   - Run existing test suite to establish baseline
   - Ensure no regressions before refactoring

### Post-Implementation Testing

1. **Environment Variable Setup**
   - Test with `AI_PROVIDER=openai` (should use OpenAI)
   - Test with `AI_PROVIDER=anthropic` (should use Claude)
   - Verify extractor initializes correctly with both providers
   - Test error handling when API keys are missing
   - Test error handling when wrong provider/key combination is set

2. **Single Image Extraction**
   - Upload PNG/JPG image
   - Verify extraction works with both providers

3. **PDF Processing**
   - Upload PDF file
   - Test both "vector_database" and "whole_document_context" approaches
   - Verify multi-page processing works

4. **Text Extraction**
   - Verify text extraction from images works
   - Check that classification still works

5. **Consolidation**
   - Process multi-page document
   - Verify consolidation works with both providers

6. **Error Handling**
   - Test with invalid API keys
   - Test with missing API keys
   - Verify error messages are provider-agnostic

## Files to Modify

### Code Files
1. `app.py` - Main refactoring changes
2. `core/extractor.py` - Add `_call_text_only_api()` method

### Documentation Files to Update
3. `docs/README.md` - Update OpenAI references, add provider selection info
4. `docs/troubleshoot_guide.md` - Make API references provider-agnostic
5. `README.md` - Add note about app.py supporting both providers (optional)

## Documentation Updates Needed

### Phase 13: Update docs/README.md

**File: `docs/README.md`**

1. **Line 3**: Update description:
```markdown
# OLD:
An AI-powered tool for extracting and analyzing financial data from PDF documents and images using OpenAI's GPT-4 Vision API.

# NEW:
An AI-powered tool for extracting and analyzing financial data from PDF documents and images using AI vision models (OpenAI GPT-4 or Anthropic Claude).
```

2. **Line 9**: Update feature description:
```markdown
# OLD:
- **AI-Powered Extraction**: Uses OpenAI GPT-4 Vision for intelligent financial data recognition

# NEW:
- **AI-Powered Extraction**: Uses AI vision models (OpenAI GPT-4 or Anthropic Claude) for intelligent financial data recognition
```

3. **Line 55**: Update prerequisites:
```markdown
# OLD:
- OpenAI API key

# NEW:
- AI Provider API key (OpenAI API key OR Anthropic API key)
```

4. **Line 74**: Update environment variable setup:
```markdown
# OLD:
# Edit .env and add your OpenAI API key

# NEW:
# Edit .env and add your API keys (see Configuration section below)
```

5. **Line 138**: Update environment variables section:
```markdown
# OLD:
OPENAI_API_KEY=your_openai_api_key_here
USE_FINANCIAL_EMBEDDINGS=false  # Optional: Enable financial-specific embeddings

# NEW:
# Required: At least one API key
AI_PROVIDER=anthropic  # Options: "anthropic" or "openai" (default: "anthropic")
ANTHROPIC_API_KEY=your_anthropic_api_key_here  # Required if using Anthropic
OPENAI_API_KEY=your_openai_api_key_here  # Required if using OpenAI
USE_FINANCIAL_EMBEDDINGS=false  # Optional: Enable financial-specific embeddings
```

6. **Line 341**: Update known limitations:
```markdown
# OLD:
- Requires OpenAI API key (paid service)

# NEW:
- Requires AI provider API key (Anthropic or OpenAI - paid service)
```

7. **Line 355**: Update footer:
```markdown
# OLD:
**Built with ❤️ using Streamlit and OpenAI GPT-4 Vision**

# NEW:
**Built with ❤️ using Streamlit and AI Vision Models (OpenAI GPT-4 / Anthropic Claude)**
```

8. **Add new section after Configuration (around line 154)**:
```markdown
### Provider Selection

The application supports both OpenAI and Anthropic providers. Configure which provider to use:

#### Using Anthropic Claude (Recommended)
```env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

#### Using OpenAI GPT-4
```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
```

#### Provider Comparison
- **Anthropic Claude**: Generally faster processing, similar accuracy
- **OpenAI GPT-4**: Alternative option, comparable performance
- Both providers support the same features and processing approaches
```

### Phase 14: Update docs/troubleshoot_guide.md

**File: `docs/troubleshoot_guide.md`**

1. **Line 32**: Update API credits reference:
```markdown
# OLD:
- **Credits**: Check your OpenAI account has sufficient credits

# NEW:
- **Credits**: Check your AI provider account (Anthropic or OpenAI) has sufficient credits
```

2. **Line 42**: Update firewall reference:
```markdown
# OLD:
- **Firewall**: Ensure OpenAI API access isn't blocked

# NEW:
- **Firewall**: Ensure your AI provider API access (Anthropic or OpenAI) isn't blocked
```

3. **Add new section after "🔐 API Issues" (around line 33)**:
```markdown
#### **Provider-Specific Issues**
- **Provider Selection**: Verify `AI_PROVIDER` is set correctly in `.env` file
- **API Key**: Ensure the correct API key is set:
  - For Anthropic: `ANTHROPIC_API_KEY` must be set
  - For OpenAI: `OPENAI_API_KEY` must be set
- **Provider Switch**: If experiencing issues with one provider, try switching to the other
  - Change `AI_PROVIDER` in `.env` and restart the application
```

### Phase 15: Update README.md (Optional)

**File: `README.md`**

Add note in Configuration section (around line 88):

```markdown
# Add after line 89:
Note: The Streamlit application (`app.py`) also supports both providers. Set `AI_PROVIDER` 
to switch between OpenAI and Anthropic when using the web interface.
```

### Phase 16: Update Test Files (If Needed)

**Review and Update Test Comments**

**File: `tests/integration/test_api_endpoints.py`**

1. **Line 79-83**: Update skipped test comments:
```python
# OLD:
@pytest.mark.skip(reason="Requires OpenAI API key and actual file processing")
def test_extract_endpoint_success_pdf(self):
    """Test successful PDF extraction (requires API key)"""
    # This test would require actual PDF files and OpenAI API key
    # Skip in unit tests, run in integration tests with real data
    pass

# NEW:
@pytest.mark.skip(reason="Requires AI provider API key and actual file processing")
def test_extract_endpoint_success_pdf(self):
    """Test successful PDF extraction (requires API key)"""
    # This test would require actual PDF files and AI provider API key (Anthropic or OpenAI)
    # Skip in unit tests, run in integration tests with real data
    pass
```

2. **Line 86-91**: Update skipped test comments:
```python
# OLD:
@pytest.mark.skip(reason="Requires OpenAI API key and actual file processing")
def test_extract_endpoint_success_image(self):
    """Test successful image extraction (requires API key)"""
    # This test would require actual image files and OpenAI API key
    # Skip in unit tests, run in integration tests with real data
    pass

# NEW:
@pytest.mark.skip(reason="Requires AI provider API key and actual file processing")
def test_extract_endpoint_success_image(self):
    """Test successful image extraction (requires API key)"""
    # This test would require actual image files and AI provider API key (Anthropic or OpenAI)
    # Skip in unit tests, run in integration tests with real data
    pass
```

**Note**: Most test files already use `FinancialDataExtractor` and `PDFProcessor` directly, which are provider-agnostic. No code changes needed - only comment updates for clarity.

## Potential Shortfalls and Considerations

### 1. Streamlit UI Elements in process_pdf_with_vector_db()

**Issue**: The current `process_pdf_with_vector_db()` in `app.py` contains Streamlit UI elements (e.g., `st.info()`, `st.success()`, progress bars) that won't be in `PDFProcessor.process_pdf_with_vector_db()`.

**Solution**: 
- Phase 5 replaces the entire function, but we should preserve Streamlit UI elements
- Wrap the PDFProcessor call with Streamlit feedback:
```python
def process_pdf_with_vector_db(uploaded_file, enable_parallel=True):
    """Process PDF using comprehensive vector database approach"""
    try:
        st.info("🔍 Processing PDF with AI-powered semantic analysis...")
        
        # Use PDFProcessor's method
        extracted_data = pdf_processor.process_pdf_with_vector_db(
            pdf_file=uploaded_file,
            enable_parallel=enable_parallel
        )
        
        if not extracted_data:
            st.warning("⚠️ No data extracted from PDF")
            return None
        
        st.success("✅ PDF processing completed")
        return extracted_data
        
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return None
```

### 2. Function Signature Changes Breaking Internal Calls

**Issue**: Some functions inside `process_pdf_with_vector_db()` might call other functions that expect `client` parameter.

**Solution**: 
- Review all internal function calls within refactored functions
- Update any functions that were called with `client` parameter
- Search for `extract_financial_data_for_page()` and similar helper functions

### 3. Return Format Compatibility

**Issue**: `PDFProcessor.process_pdf_with_vector_db()` might return data in a different format than what `app.py` expects.

**Solution**:
- Compare return formats between old and new implementations
- Add transformation logic if needed (as noted in Phase 5)
- Test with actual documents to verify format compatibility

### 4. Error Handling Differences

**Issue**: Streamlit-specific error handling (st.error, st.warning) might be lost when using PDFProcessor directly.

**Solution**:
- Ensure all refactored functions wrap PDFProcessor calls with Streamlit UI feedback
- Preserve user-facing error messages
- Maintain the same error handling patterns

### 5. Missing Validation for Provider Configuration

**Issue**: No check to ensure `AI_PROVIDER` is set correctly before initialization.

**Solution**:
- Add validation in extractor initialization section:
```python
# Validate provider configuration
if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
    st.error("❌ No API key found. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY in your .env file")
    st.stop()

provider = os.getenv("AI_PROVIDER", "anthropic").lower()
if provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
    st.error("❌ AI_PROVIDER=anthropic but ANTHROPIC_API_KEY not found")
    st.stop()
elif provider == "openai" and not os.getenv("OPENAI_API_KEY"):
    st.error("❌ AI_PROVIDER=openai but OPENAI_API_KEY not found")
    st.stop()
```

## Estimated Impact

- **Lines Changed**: ~200-300 lines in `app.py`
- **New Code**: ~50 lines in `core/extractor.py`
- **Documentation Updates**: ~50-80 lines across 2-3 documentation files
- **Breaking Changes**: Function signatures change (removing `client` parameter)
- **Backward Compatibility**: No - this changes how app.py works internally

## Notes

- The Streamlit UI will remain the same - only backend changes
- Users will need to set `AI_PROVIDER=anthropic` and `ANTHROPIC_API_KEY` to use Claude
- Users can set `AI_PROVIDER=openai` and `OPENAI_API_KEY` to use OpenAI
- The extractor automatically selects the provider based on `AI_PROVIDER` environment variable
- All existing functionality should work the same, just with provider choice
- Documentation updates ensure users know about provider selection options

