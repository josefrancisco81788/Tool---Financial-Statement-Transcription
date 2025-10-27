# 🤖 Anthropic API Implementation Analysis & Error Consultation

## 📋 **Executive Summary**

We're experiencing consistent **HTTP 400 Bad Request** errors when calling the Anthropic API for financial document processing. The implementation appears to follow the correct 2025 v4.2 API format, but something in our request structure is causing the API to reject our requests.

**Request for Senior Developer Consultation:** Please review the implementation and identify what's causing the HTTP 400 errors.

---

## 🔧 **Current Implementation Overview**

### **1. API Configuration**
```python
# core/config.py
class Config:
    def __init__(self):
        # Anthropic Configuration
        self.ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        self.ANTHROPIC_MAX_TOKENS: int = int(os.getenv("ANTHROPIC_MAX_TOKENS", "4096"))
        self.ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY")
```

### **2. Client Initialization**
```python
# core/extractor.py
class FinancialDataExtractor:
    def __init__(self):
        self.config = Config()
        self.provider = self.config.AI_PROVIDER.lower()
        
        # Initialize Anthropic client
        if self.provider == "anthropic":
            self.anthropic_client = anthropic.Anthropic(
                api_key=self.config.ANTHROPIC_API_KEY
            )
```

### **3. API Call Implementation**
```python
# core/extractor.py - _call_anthropic_api method
def _call_anthropic_api(self, base64_image: str, prompt: str) -> str:
    """Make API call to Anthropic with retry logic using 2025 v4.2 API"""
    def api_call():
        # Use the correct 2025 v4.2 Anthropic API format
        response = self.anthropic_client.messages.create(
            model=self.config.ANTHROPIC_MODEL,
            max_tokens=self.config.ANTHROPIC_MAX_TOKENS,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image
                            }
                        }
                    ]
                }
            ]
        )
        
        # Handle response from 2025 v4.2 API
        if hasattr(response, 'content') and response.content:
            return response.content[0].text if isinstance(response.content, list) else response.content
        else:
            raise Exception(f"Unexpected response format: {type(response)}")
    
    return self.exponential_backoff_retry(api_call)
```

---

## 🚨 **Error Analysis**

### **Error Pattern:**
```
2025-09-23 20:28:15,218 - httpx - INFO - HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 400 Bad Request"
2025-09-23 20:28:15,229 - httpx - INFO - HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 400 Bad Request"
2025-09-23 20:28:15,235 - httpx - INFO - HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 400 Bad Request"
```

### **Error Characteristics:**
- ✅ **Authentication**: API key appears valid (not getting 401/403 errors)
- ❌ **Request Format**: Consistent HTTP 400 suggests malformed request
- ❌ **Rate Limiting**: Not the issue (getting immediate 400, not 429)
- ❌ **Model Availability**: Model name validated and working in validation

---

## 🔍 **Detailed Request Structure Analysis**

### **Expected Request Format (2025 v4.2 API):**
```json
{
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 4096,
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Extract financial data from this image..."
        },
        {
          "type": "image",
          "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": "iVBORw0KGgoAAAANSUhEUgAA..."
          }
        }
      ]
    }
  ]
}
```

### **Our Implementation:**
```python
response = self.anthropic_client.messages.create(
    model="claude-sonnet-4-20250514",        # ✅ Correct model
    max_tokens=4096,                         # ✅ Valid token limit
    messages=[                               # ✅ Correct messages structure
        {
            "role": "user",                  # ✅ Valid role
            "content": [                     # ✅ Array format
                {"type": "text", "text": prompt},  # ✅ Text content
                {
                    "type": "image",         # ✅ Image content type
                    "source": {
                        "type": "base64",    # ✅ Base64 source
                        "media_type": "image/png",  # ✅ Media type
                        "data": base64_image # ✅ Base64 data
                    }
                }
            ]
        }
    ]
)
```

---

## 🧪 **Test Provider Implementation**

### **Anthropic Test Provider:**
```python
# tests/providers/anthropic_provider.py
class AnthropicTestProvider(BaseTestProvider):
    def test_document(self, document_path: str, timeout: int = 300) -> TestResult:
        try:
            # Set environment variable
            self._set_environment_variable("anthropic")
            
            # Re-initialize to pick up environment variable
            self.extractor = FinancialDataExtractor()
            self.pdf_processor = PDFProcessor(self.extractor)
            
            # Process document
            with open(document_path, 'rb') as f:
                pdf_data = f.read()
            extracted_data = self.pdf_processor.process_pdf_with_vector_db(pdf_data)
            
            # ... rest of processing
```

---

## 🔧 **Environment & Dependencies**

### **SDK Version:**
```bash
pip install anthropic>=0.68.0
```

### **Environment Variables:**
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514
ANTHROPIC_MAX_TOKENS=4096
AI_PROVIDER=anthropic
```

### **Python Version:**
```bash
Python 3.11+
```

---

## 🎯 **Specific Questions for Senior Developer**

### **1. API Request Format:**
- Is our `messages.create()` call structure correct for the 2025 v4.2 API?
- Are we missing any required headers or parameters?
- Is the image content format correct for base64 PNG data?

### **2. Model & Configuration:**
- Is `claude-sonnet-4-20250514` the correct model identifier?
- Are our `max_tokens=4096` within acceptable limits?
- Should we be using a different endpoint or API version?

### **3. SDK Usage:**
- Are we using the `anthropic` SDK correctly?
- Should we be using a different method or client initialization?
- Is there a newer SDK version we should be using?

### **4. Error Handling:**
- How can we get more detailed error information from HTTP 400 responses?
- Are there specific validation checks we should be performing before API calls?

---

## 🔍 **Debugging Attempts Made**

### **1. Validation Check:**
```python
def validate_configuration(self) -> bool:
    # ✅ API key validation passes
    # ✅ Model validation passes  
    # ✅ Provider switching works
    print(f"✅ Anthropic provider validated: {self.extractor.config.ANTHROPIC_MODEL}")
```

### **2. Request Logging:**
- HTTP requests are being made to correct endpoint
- Authentication appears to be working (no 401/403 errors)
- Consistent 400 errors suggest request format issue

### **3. Comparison with Working Implementation:**
- OpenAI implementation works perfectly with same data
- Same base64 image encoding used for both providers
- Same prompt structure used for both providers

---

## 📊 **Error Context**

### **When Errors Occur:**
- During financial document processing
- When calling `_call_anthropic_api()` method
- Specifically during image processing with base64 data
- Happens immediately (not after processing delay)

### **Success vs Failure:**
- ✅ **OpenAI**: All requests return HTTP 200 OK
- ❌ **Anthropic**: All requests return HTTP 400 Bad Request
- ✅ **Validation**: Anthropic provider validation passes
- ❌ **Processing**: Actual API calls fail

---

## 🎯 **Requested Consultation Areas**

### **High Priority:**
1. **Request Format Validation**: Is our API call structure correct?
2. **SDK Usage**: Are we using the Anthropic SDK properly?
3. **Error Debugging**: How to get detailed error messages from HTTP 400?

### **Medium Priority:**
1. **Model Configuration**: Correct model identifier and parameters?
2. **Image Processing**: Proper base64 encoding and media type?
3. **Rate Limiting**: Any hidden rate limiting we're hitting?

### **Low Priority:**
1. **Alternative Approaches**: Should we use different API methods?
2. **SDK Version**: Any known issues with current SDK version?
3. **Best Practices**: Recommended patterns for Anthropic API usage?

---

## 📝 **Next Steps Requested**

1. **Code Review**: Please review the implementation for obvious issues
2. **API Documentation**: Verify against latest Anthropic API docs
3. **Error Analysis**: Help identify what's causing HTTP 400 errors
4. **Fix Recommendations**: Suggest specific changes to resolve the issue

---

**The implementation appears to follow the documented API format, but we're getting consistent HTTP 400 errors. Any insights into what might be wrong with our request structure would be greatly appreciated.**












