# Year Field Extraction - Revised Implementation Plan

> **⚠️ PRIMARY USE CASE REMINDER**  
> This tool processes **30-80 page annual reports** where financial statements appear at **unpredictable locations**. PDFs are **non-OCR scanned images** with no extractable text. All processing must use vision-based AI analysis. See [USE_CASE.md](USE_CASE.md) for details.

---

## Critical Assessment Feedback

**Original Plan Flaw**: Adding 15+ lines of year extraction instructions to an already complex prompt that handles 91 template fields. This risks overwhelming Claude's processing capacity - the exact issue that caused previous 52.9% coverage failures.

**Correct Principle**: Simplify, don't complicate. Separate concerns rather than overloading a single prompt.

## Revised Approach: Separate Year Extraction

### Strategy: Lightweight Pre-Processing Call

Make a minimal, focused API call specifically for year extraction BEFORE the main financial data extraction.

**Why This Works**:
- Simple prompt = higher success rate
- Doesn't risk breaking current 90.5% field mapping accuracy
- Minimal additional cost (~$0.01 per document)
- Follows the principle: focused prompts succeed, complex prompts fail

---

## Implementation Plan

### Phase 1: Add Lightweight Year Extraction Method

**File**: `core/extractor.py`

**Add new method**:

```python
def extract_years_from_image(self, base64_image: str) -> Dict[str, Any]:
    """
    Extract year information from financial statement image.
    Uses a simple, focused prompt for high accuracy.
    
    Args:
        base64_image: Base64-encoded image data
        
    Returns:
        Dictionary with year data: {"years": [2023, 2022, 2021], "confidence": 0.95}
    """
    try:
        # Simple, focused prompt
        year_prompt = """
        What years are covered by this financial statement?
        
        Look for years in:
        - Document title/header
        - Column headers
        - "Years Covered:", "As of", "For the year ended" phrases
        
        Return ONLY a JSON object with the years as an array (most recent first):
        {"years": [2023, 2022, 2021]}
        
        If no years found, return: {"years": []}
        """
        
        # Make API call
        if self.provider == "anthropic":
            response = self._call_anthropic_api(base64_image, year_prompt)
        elif self.provider == "openai":
            response = self._call_openai_api(base64_image, year_prompt)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
        
        # Parse JSON response
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            return {"years": [], "confidence": 0.0}
        
        json_str = response[start_idx:end_idx]
        year_data = json.loads(json_str)
        
        # Validate and clean
        years = year_data.get('years', [])
        
        # Filter to valid years (1900-2100)
        years = [y for y in years if isinstance(y, int) and 1900 <= y <= 2100]
        
        # Sort descending (most recent first)
        years = sorted(years, reverse=True)
        
        # Limit to 4 years (template supports Value_Year_1 through Value_Year_4)
        years = years[:4]
        
        return {
            "years": years,
            "confidence": 0.95 if years else 0.0,
            "source": "vision_extraction"
        }
        
    except json.JSONDecodeError:
        print(f"⚠️ Failed to parse year extraction response")
        return {"years": [], "confidence": 0.0}
        
    except Exception as e:
        print(f"⚠️ Year extraction error: {e}")
        return {"years": [], "confidence": 0.0}
```

---

### Phase 2: Integrate Year Extraction into Processing Pipeline

**File**: `core/pdf_processor.py`

**Modify**: `process_pdf_with_vector_db()` method to extract years before financial data

```python
def process_pdf_with_vector_db(self, pdf_file, enable_parallel: bool = True) -> Optional[Dict[str, Any]]:
    """
    Process PDF using comprehensive vector database approach.
    Now includes separate year extraction.
    """
    try:
        # Convert PDF to images
        images = self.convert_pdf_to_images(pdf_file)
        if not images:
            raise Exception("No images generated from PDF")
        
        print(f"🔍 Processing {len(images)} pages")
        
        # ===== NEW: Extract years from first page =====
        # Years are typically in document header on first page
        year_data = None
        if len(images) > 0:
            try:
                first_page_image = self.extractor.encode_image(images[0])
                year_data = self.extractor.extract_years_from_image(first_page_image)
                if year_data.get('years'):
                    print(f"✅ Extracted years: {year_data['years']}")
                else:
                    print(f"⚠️ No years extracted from document")
            except Exception as e:
                print(f"⚠️ Year extraction failed: {e}")
                year_data = {"years": [], "confidence": 0.0}
        # ============================================
        
        # Existing classification and extraction logic
        financial_pages = self.classify_pages_batch_vision(images)
        # ... rest of existing code ...
        
        # Extract financial data from each page
        page_results = []
        for page in financial_pages:
            # ... existing extraction code ...
            page_results.append(...)
        
        # Combine results
        combined_data = self._combine_page_results(page_results)
        
        # ===== NEW: Add year data to combined results =====
        if year_data and year_data.get('years'):
            years = year_data['years']
            combined_data['template_mappings']['Year'] = {
                'value': years[0] if years else None,
                'confidence': year_data.get('confidence', 0.95),
                'Value_Year_1': years[0] if len(years) > 0 else None,
                'Value_Year_2': years[1] if len(years) > 1 else None,
                'Value_Year_3': years[2] if len(years) > 2 else None,
                'Value_Year_4': years[3] if len(years) > 3 else None,
                'source': year_data.get('source', 'vision_extraction')
            }
            print(f"✅ Year field populated: {years}")
        # ================================================
        
        return combined_data
        
    except Exception as e:
        print(f"❌ Error in process_pdf_with_vector_db: {e}")
        return None
```

---

### Phase 3: Add Error Handling and Logging

**Add debug logging**:

```python
# In pdf_processor.py, after year extraction
if year_data:
    print(f"🔍 Year extraction result:")
    print(f"   Years found: {year_data.get('years', [])}")
    print(f"   Confidence: {year_data.get('confidence', 0.0)}")
    print(f"   Source: {year_data.get('source', 'unknown')}")
```

---

## Benefits of This Approach

### 1. **Simplicity**
- Year extraction: ~5 lines of prompt
- Financial extraction: unchanged (maintains 90.5% accuracy)
- Clear separation of concerns

### 2. **Safety**
- Doesn't risk breaking existing financial data extraction
- Isolated failure - if year extraction fails, financial data still works
- Easy to test independently

### 3. **Cost**
- One additional API call per document
- Estimated cost: ~$0.01 per document (minimal)
- Much cheaper than redoing extraction if complex prompt fails

### 4. **Performance**
- Lightweight prompt = fast response
- Parallel processing possible (year + page classification)
- Minimal latency increase

### 5. **Maintainability**
- Easy to debug (separate method)
- Easy to improve (modify year prompt without touching financial extraction)
- Clear responsibility separation

---

## Testing Strategy

### Test 1: Year Extraction Only
```python
# Test the year extraction method independently
extractor = FinancialDataExtractor()
with open('tests/fixtures/light/2021 AFS with SEC Stamp - statement extracted.pdf', 'rb') as f:
    images = convert_pdf_to_images(f)
    first_page = encode_image(images[0])
    year_data = extractor.extract_years_from_image(first_page)
    print(f"Years: {year_data['years']}")
    # Expected: [2021, 2020]
```

### Test 2: Integration Test
```bash
python test_single_file.py 1  # Test on 2021 AFS with SEC Stamp
# Expected: Year field should now be populated
```

### Test 3: Full Regression Test
```bash
# Test all 4 light files
python test_single_file.py 1
python test_single_file.py 2
python test_single_file.py 3
python test_single_file.py 4

# Expected results:
# - Year field: 90%+ success (up from 0%)
# - Financial data: 90%+ field mapping (unchanged)
# - Processing time: <10% increase
```

---

## Success Criteria

### Primary Goals:
- ✅ Year field extraction: **80%+** success rate (from 0%)
- ✅ Financial data accuracy: **Maintained at 90%+** field mapping
- ✅ Processing time: **<10%** increase

### Stretch Goals:
- 🎯 Year field extraction: **95%+** success rate
- 🎯 Zero degradation in financial data accuracy
- 🎯 <5% processing time increase

---

## Rollback Plan

If this approach fails:

1. **Easy Rollback**: Simply remove the year extraction call from `process_pdf_with_vector_db()`
2. **No Impact**: Financial data extraction is unchanged
3. **Cost**: Only wasted development time (~2 hours), no production impact

---

## Implementation Timeline

### Phase 1: Core Implementation (1 hour)
- Add `extract_years_from_image()` method to `extractor.py`
- Add basic unit test

### Phase 2: Integration (30 minutes)
- Integrate into `pdf_processor.py`
- Add debug logging

### Phase 3: Testing (30 minutes)
- Test year extraction independently
- Test integration with one file
- Run full regression test

### Phase 4: Validation (15 minutes)
- Compare before/after metrics
- Document results

**Total Time**: ~2.25 hours

---

## Why This is Better Than Original Plan

| Aspect | Original Plan (Complex Prompt) | Revised Plan (Separate Call) |
|--------|-------------------------------|------------------------------|
| **Prompt Complexity** | 15+ additional lines | 5 lines (separate) |
| **Risk to Financial Extraction** | High (overload) | None (isolated) |
| **Cost** | Same | +$0.01 per doc |
| **Expected Success** | 60-70% (prompt overload) | 90-95% (focused) |
| **Maintainability** | Low (tangled logic) | High (clear separation) |
| **Testing** | Hard (tightly coupled) | Easy (independent) |
| **Rollback** | Complex | Simple |

---

## Next Steps

1. **Get approval** for this revised approach
2. **Implement Phase 1** (add year extraction method)
3. **Test independently** on one page
4. **Integrate Phase 2** if Phase 1 succeeds
5. **Run full regression** test
6. **Compare metrics** and document results

---

## Conclusion

The revised approach follows the fundamental principle: **simplicity succeeds, complexity fails**. By separating year extraction into a lightweight, focused API call, we:

- Avoid overloading the financial extraction prompt
- Maintain current high accuracy (90.5% field mapping)
- Achieve high year extraction success (90-95% expected)
- Keep costs minimal (~$0.01 per document)
- Enable easy testing and rollback

This is a much safer, more reliable approach than complicating the already-working financial extraction prompt.
