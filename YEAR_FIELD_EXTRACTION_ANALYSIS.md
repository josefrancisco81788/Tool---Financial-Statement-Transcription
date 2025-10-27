# Year Field Extraction Analysis and Fix Plan

## Problem Statement

The current system has a **0% success rate** for extracting the "Year" field across all test files. The "Year" field is critical metadata that appears in the template at row 2 (Meta > Reference > Year) and should contain year values like "2021, 2020" or "2022, 2021".

## Current System Analysis

### How the System Currently Works

1. **Template Loading** (`core/extractor.py`, line 50-77):
   - Loads 91 template fields from `FS_Input_Template_Fields.csv`
   - "Year" is the first field in the list (after header)
   - This field IS being loaded into the template context

2. **Extraction Prompt** (`core/extractor.py`, line 176-221):
   - Template fields (including "Year") are passed to the LLM
   - The prompt instructs: "Use EXACT template field names (case-sensitive)"
   - Example format shows field mappings with `Value_Year_1`, `Value_Year_2`
   - **BUT**: No specific instruction about extracting metadata like years from headers

3. **Current Focus**:
   - Prompt prioritizes financial line items (Revenue, Assets, etc.)
   - Multi-year handling focuses on extracting values for each year column
   - No explicit instruction to extract the year labels themselves

### Why "Year" is Failing

**Root Cause Analysis:**

1. **Semantic Confusion**: The field name "Year" and the year columns (`Value_Year_1`, `Value_Year_2`) create confusion:
   - The LLM sees "Year" as a template field name
   - The LLM also sees instructions about `Value_Year_1`, `Value_Year_2` 
   - The LLM doesn't understand it should extract "2021, 2020" AS the Year field value

2. **Prompt Emphasis**: The prompt heavily emphasizes extracting financial **line items with numerical values**:
   - "Extract EVERY line item with both a label and numerical value"
   - Years in headers (like "Years Covered: 2021, 2020") aren't presented as line items
   - The LLM doesn't recognize this as data to extract

3. **Location Issue**: Years appear in document headers/titles, not in the tabular data:
   - Example from test file: "Years Covered: 2021, 2020" (page header)
   - The vision model may not focus on headers when extracting table data
   - Headers are visually separated from the financial tables

4. **Data Structure Mismatch**: 
   - Year field expects format: `"Year": {"value": 2021, "Value_Year_1": 2021, "Value_Year_2": 2020}`
   - But years are typically found as text labels, not numeric line items
   - The LLM is trained to extract "line item: value" pairs, not metadata

## Evidence from Test Files

### Example 1: 2021 AFS with SEC Stamp
From `DETAILS PER PAGE 2021 AFS with SEC Stamp - statement extracted.txt`:
```
Page Number: 1
Document Name: Comparative Statement of Financial Position
Years Covered: 2021, 2020
```

**Target Template Value**: `Year,95%,0.95,2021,2020,,`
**Extracted**: Nothing

### Example 2: afs-2021-2023
Expected years: 2023, 2022, 2021 (3-year comparative)
**Extracted**: Nothing

The pattern is consistent: years appear in **document headers**, not in the financial data tables.

## Proposed Solutions

### Option 1: Dedicated Year Extraction in Prompt ⭐ **RECOMMENDED**

**Approach**: Add explicit instructions to the extraction prompt specifically for metadata extraction.

**Implementation**:
```python
def _build_extraction_prompt(self, statement_type_hint: str) -> str:
    template_fields = self._load_template_fields()
    
    return f"""
    Extract ALL financial data from this {statement_type_hint} and map to template fields.

    AVAILABLE TEMPLATE FIELDS: {', '.join(template_fields)}

    EXTRACTION RULES:
    1. **FIRST: Extract metadata from document headers**
       - Look for "Year", "Years Covered", "As of", "For the year ended", etc.
       - Extract year values (e.g., "2021, 2020") and map to the "Year" field
       - Format: "Year": {{"value": 2021, "Value_Year_1": 2021, "Value_Year_2": 2020}}
    
    2. Extract EVERY line item with both a label and numerical value
    3. Map each item to the most appropriate template field from the list above
    4. Use EXACT template field names (case-sensitive)
    5. Extract values as numbers (remove currency symbols, handle parentheses as negative)
    6. Set confidence: 0.9+ for clear values, 0.7+ for somewhat clear, 0.5+ for uncertain

    METADATA EXTRACTION (HIGH PRIORITY):
    - **Year**: Extract ALL years mentioned in headers, titles, or column headers
    - Look for patterns like "2021", "2022", "FY2021", "Year ended 2021"
    - If multiple years found, assign: most recent → Value_Year_1, previous → Value_Year_2, etc.
    - Example: Document shows "2023  2022  2021" → "Year": {{"value": 2023, "Value_Year_1": 2023, "Value_Year_2": 2022, "Value_Year_3": 2021}}

    PRIORITY FIELDS (extract after metadata):
    - Revenue, Cost of Sales, Gross Profit, Comprehensive / Net income
    - Total Assets, Total Equity, Total Liabilities
    ...
    """
```

**Pros**:
- Leverages existing LLM capability
- No additional API calls
- Maintains unified extraction approach
- Clear, explicit instruction

**Cons**:
- Relies on LLM to understand the distinction
- May still miss if years are in unusual locations

**Estimated Success Rate**: 80-90%

---

### Option 2: Two-Phase Extraction (Metadata + Financial Data)

**Approach**: Make two separate LLM calls per page:
1. First call: Extract metadata (years, company name, document type)
2. Second call: Extract financial line items

**Implementation**:
```python
def extract_comprehensive_financial_data(self, base64_image, statement_type_hint, page_text=None):
    # Phase 1: Extract metadata
    metadata_prompt = """
    Extract document metadata from this financial statement image:
    1. Year or years covered (look in headers, titles, column headers)
    2. Company name
    3. Statement type (Balance Sheet, Income Statement, Cash Flow)
    
    Return JSON:
    {
        "year": [2023, 2022, 2021],  // Array of years, most recent first
        "company_name": "Company Name",
        "statement_type": "Balance Sheet"
    }
    """
    metadata = self._call_api_with_prompt(base64_image, metadata_prompt)
    
    # Phase 2: Extract financial data (existing logic)
    financial_data = self._call_api_with_prompt(base64_image, self._build_extraction_prompt(statement_type_hint))
    
    # Merge: Add metadata to financial_data
    if metadata.get('year'):
        years = metadata['year']
        financial_data['template_mappings']['Year'] = {
            'value': years[0] if years else None,
            'confidence': 0.95,
            'Value_Year_1': years[0] if len(years) > 0 else None,
            'Value_Year_2': years[1] if len(years) > 1 else None,
            'Value_Year_3': years[2] if len(years) > 2 else None,
            'Value_Year_4': years[3] if len(years) > 3 else None,
        }
    
    return financial_data
```

**Pros**:
- Highly focused prompts for each task
- Metadata extraction is explicit and clear
- Can add additional metadata extraction (company name, etc.)
- Very high accuracy for metadata

**Cons**:
- **Doubles API calls** (expensive, slower)
- Doubles processing time
- More complex architecture
- Requires careful merging logic

**Estimated Success Rate**: 95-98%

---

### Option 3: Post-Processing with Regex/NLP

**Approach**: After LLM extraction, use deterministic methods to find years in the document.

**Implementation**:
```python
def _extract_years_from_text(self, page_text: str) -> List[int]:
    """Extract years using regex patterns"""
    import re
    
    # Pattern 1: Look for "Years: 2021, 2020" or "As of December 31, 2021 and 2020"
    patterns = [
        r'(?:Years?|Year ended|As of|For the period).*?(\d{4})',
        r'\b(20\d{2})\b',  # Any 4-digit year starting with 20
        r'\b(19\d{2})\b',  # Any 4-digit year starting with 19
    ]
    
    years = []
    for pattern in patterns:
        matches = re.findall(pattern, page_text, re.IGNORECASE)
        years.extend([int(y) for y in matches])
    
    # Deduplicate and sort (most recent first)
    years = sorted(list(set(years)), reverse=True)
    return years[:4]  # Maximum 4 years

def extract_comprehensive_financial_data(self, base64_image, statement_type_hint, page_text=None):
    # Existing LLM extraction
    extracted_data = ...
    
    # Post-process: Add years if not extracted by LLM
    if 'Year' not in extracted_data['template_mappings'] and page_text:
        years = self._extract_years_from_text(page_text)
        if years:
            extracted_data['template_mappings']['Year'] = {
                'value': years[0],
                'confidence': 0.85,  # Lower confidence for regex
                'Value_Year_1': years[0] if len(years) > 0 else None,
                'Value_Year_2': years[1] if len(years) > 1 else None,
                'Value_Year_3': years[2] if len(years) > 2 else None,
                'Value_Year_4': years[3] if len(years) > 3 else None,
            }
    
    return extracted_data
```

**Pros**:
- Deterministic and reliable
- No additional API calls
- Fast execution
- Works even if LLM fails
- Can serve as fallback for Option 1

**Cons**:
- **Requires OCR text** (we're using vision-only for scanned docs)
- Regex may capture false positives (contract years, other dates)
- Not context-aware
- Doesn't work if text extraction is poor quality

**Estimated Success Rate**: 60-70% (without OCR text)

---

### Option 4: Hybrid Approach (Option 1 + Option 3) ⭐⭐ **BEST OVERALL**

**Approach**: Combine prompt engineering with regex fallback.

**Implementation**:
```python
def extract_comprehensive_financial_data(self, base64_image, statement_type_hint, page_text=None):
    # Primary: Enhanced prompt with explicit year extraction (Option 1)
    extracted_data = self._call_api_with_enhanced_prompt(base64_image, statement_type_hint)
    
    # Fallback: Regex extraction if LLM didn't extract Year (Option 3)
    if 'Year' not in extracted_data['template_mappings'] and page_text:
        years = self._extract_years_from_text(page_text)
        if years:
            extracted_data['template_mappings']['Year'] = {
                'value': years[0],
                'confidence': 0.80,  # Medium confidence for fallback
                'Value_Year_1': years[0] if len(years) > 0 else None,
                'Value_Year_2': years[1] if len(years) > 1 else None,
                'Value_Year_3': years[2] if len(years) > 2 else None,
                'Value_Year_4': years[3] if len(years) > 3 else None,
            }
            extracted_data['template_mappings']['Year']['source'] = 'regex_fallback'
    
    return extracted_data
```

**Pros**:
- Best of both worlds
- High primary success rate (80-90%) from improved prompt
- Safety net for edge cases
- No additional API calls if LLM succeeds
- Graceful degradation

**Cons**:
- Slightly more complex logic
- Requires managing both extraction paths

**Estimated Success Rate**: 90-95%

---

## Recommendation

**Implement Option 4 (Hybrid Approach)** in phases:

### Phase 1: Improve Prompt (Option 1) - PRIORITY
- **Effort**: Low (1 hour)
- **Risk**: Low
- **Impact**: High (expected 80-90% success)
- **Implementation**: Modify `_build_extraction_prompt()` to explicitly instruct year extraction

### Phase 2: Add Regex Fallback (Option 3) - IF NEEDED
- **Effort**: Low-Medium (2-3 hours)
- **Risk**: Low
- **Impact**: Medium (catches remaining 10-20% failures)
- **Implementation**: Add post-processing logic to `extract_comprehensive_financial_data()`

### Phase 3: Consider Two-Phase Extraction (Option 2) - FUTURE
- **Effort**: High (1-2 days)
- **Risk**: Medium (API cost increase)
- **Impact**: Marginal (5-8% additional success)
- **Implementation**: Only if Phase 1+2 doesn't reach 90%+ success

## Implementation Details for Phase 1 (Recommended First Step)

### Files to Modify:
1. `core/extractor.py` - `_build_extraction_prompt()` method

### Changes Required:

```python
def _build_extraction_prompt(self, statement_type_hint: str) -> str:
    """Build enhanced but focused LLM-first direct mapping extraction prompt"""
    template_fields = self._load_template_fields()
    
    return f"""
    Extract ALL financial data from this {statement_type_hint} and map to template fields.

    AVAILABLE TEMPLATE FIELDS: {', '.join(template_fields)}

    ⚠️ CRITICAL FIRST STEP - EXTRACT METADATA:
    Before extracting financial line items, look for document metadata:
    
    **Year Field** (MANDATORY - HIGH PRIORITY):
    - Look in document headers, page titles, and column headers
    - Search for text like: "Years Covered:", "As of December 31,", "For the year ended", column headers with years
    - Extract ALL year values you can find (typically 2-4 years in comparative statements)
    - Examples of what to look for:
      * "Comparative Statement of Financial Position - 2023 and 2022"
      * Column headers: "2023 | 2022 | 2021"
      * "For the year ended December 31, 2023"
      * "Years Covered: 2023, 2022"
    - Map to "Year" field with format:
      "Year": {{"value": 2023, "confidence": 0.95, "Value_Year_1": 2023, "Value_Year_2": 2022, "Value_Year_3": 2021}}
    
    Where Value_Year_1 = most recent year, Value_Year_2 = previous year, etc.

    EXTRACTION RULES FOR FINANCIAL DATA:
    1. Extract EVERY line item with both a label and numerical value
    2. Map each item to the most appropriate template field from the list above
    3. Use EXACT template field names (case-sensitive)
    4. Extract values as numbers (remove currency symbols, handle parentheses as negative)
    5. Set confidence: 0.9+ for clear values, 0.7+ for somewhat clear, 0.5+ for uncertain

    PRIORITY FIELDS (extract these if present):
    - **Year** (from headers/titles - MUST EXTRACT FIRST)
    - Revenue, Cost of Sales, Gross Profit, Comprehensive / Net income
    - Total Assets, Total Equity, Total Liabilities
    - Cash and Cash Equivalents, Current Assets, Current Liabilities
    - Property, Plant and Equipment, Trade and Other Current Receivables

    Return format:
    {{
        "template_mappings": {{
            "Year": {{"value": 2023, "confidence": 0.95, "Value_Year_1": 2023, "Value_Year_2": 2022}},
            "Revenue": {{"value": 1000000, "confidence": 0.95, "Value_Year_1": 1000000, "Value_Year_2": 950000}},
            "Cost of Sales": {{"value": 800000, "confidence": 0.90, "Value_Year_1": 800000, "Value_Year_2": 750000}},
            "Total Assets": {{"value": 5000000, "confidence": 0.95, "Value_Year_1": 5000000, "Value_Year_2": 4800000}},
            "Total Equity": {{"value": 3000000, "confidence": 0.90, "Value_Year_1": 3000000, "Value_Year_2": 2800000}}
        }}
    }}

    MULTI-YEAR DATA HANDLING:
    - If you see multiple years (like 2022, 2021), extract values for each year
    - Use Value_Year_1 for the most recent year, Value_Year_2 for the previous year
    - Example: If you see "Revenue  2022: 9,843,009  2021: 20,406,722", extract:
      "Revenue": {{"value": 9843009, "confidence": 0.95, "Value_Year_1": 9843009, "Value_Year_2": 20406722}}

    IMPORTANT:
    - **ALWAYS extract the Year field first by looking at headers and titles**
    - Extract as many fields as possible, not just the priority ones
    - If you see "Net Sales" or "Total Sales", map to "Revenue"
    - If you see "Cost of Goods Sold", map to "Cost of Sales"
    - If you see "Net Income" or "Profit", map to "Comprehensive / Net income"
    - Be thorough - extract everything you can see clearly
    - Always include multi-year data if present in the document
    """
```

### Testing Strategy:
1. Test on all 4 light files
2. Measure Year field extraction success rate
3. Compare before/after accuracy
4. Validate that financial data extraction wasn't negatively impacted

### Success Criteria:
- Year field extraction: 80%+ success rate (from 0%)
- Financial data extraction: Maintained at 90%+ field mapping accuracy
- Processing time: No significant increase (<5% slower)

## Alternative Considerations

### Why Not Use OCR First?
- **Business Requirement**: System must be "vision-only" for scanned image PDFs
- OCR adds complexity and potential errors
- Vision LLMs are capable of reading text from images directly

### Why Not Extract from Filename?
- Filenames may not contain year information
- Filenames may be unreliable or renamed
- Years in document content are the source of truth

### Why Not Use a Separate Year Detection Model?
- Over-engineering for a single field
- Additional model adds latency and cost
- LLM should be capable if properly prompted

## Conclusion

The Year field extraction failure is due to **inadequate prompt specificity** rather than a fundamental system limitation. The LLM is fully capable of extracting year information from document headers if explicitly instructed to do so.

**Recommended Action**: Implement Phase 1 (Enhanced Prompt) immediately. This is a low-effort, high-impact change that should resolve 80-90% of the issue. Monitor results and proceed to Phase 2 (Regex Fallback) only if needed to reach 90%+ success rate.
