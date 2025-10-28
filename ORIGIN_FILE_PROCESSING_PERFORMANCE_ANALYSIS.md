# Origin File Processing Performance - Optimization Request

## Executive Summary

We're processing 54-page annual reports and need to reduce execution time from **12 minutes to ~2 minutes** to improve user experience. Sequential API calls are the primary bottleneck. Requesting guidance on parallelization strategy and other optimization approaches.

**Current Performance**: 791 seconds for AFS2024.pdf (54 pages, 18 financial pages)  
**Target Performance**: ~120 seconds (6x improvement)  
**Priority**: High - affects production UX

---

## Current Architecture

**System**: Python-based financial statement extraction using Anthropic Claude API  
**Process Flow**:
1. PDF → Images (PyMuPDF, parallel)
2. Classify each page (sequential API calls)
3. Extract data from financial pages (sequential API calls)
4. Generate CSV output

**Key Files**:
- `core/pdf_processor.py` - PDF processing and classification
- `core/extractor.py` - Financial data extraction
- `tests/run_extraction_test.py` - Test runner (current implementation)

---

## Performance Analysis

### Timing Breakdown (54-page document)
- **PDF to Images**: 236s (30%) - 54 pages at 4.4s/page
- **Classification**: 334s (42%) - 54 sequential API calls at 6.2s/call ⚠️ **BOTTLENECK**
- **Extraction**: 220s (28%) - 18 sequential API calls at 12.2s/call ⚠️ **BOTTLENECK**
- **CSV Generation**: 1s

**Total**: 791s (13.2 minutes)

### Bottleneck Summary
- **72% of time** spent in sequential API calls (334s + 220s)
- API latency dominates (network + processing)
- No current parallelization for API calls

---

## Optimization Options - Seeking Guidance

### Option 1: Parallel API Calls (Proposed)
**Impact**: High - addresses 72% of processing time

**Approach**: Use concurrent.futures.ThreadPoolExecutor for API calls

**Questions**:
1. **Worker Count**: What's the optimal concurrent worker count? (4, 8, 16 workers?)
2. **Threading vs Async**: ThreadPoolExecutor vs asyncio - which is better for Anthropic API?
3. **Rate Limits**: Anthropic's rate limits - how many concurrent requests are safe?
4. **Batching**: Can we batch multiple images in single API call for classification?

**Potential Savings**: 400-450 seconds (334s → 40s classification, 220s → 30s extraction)

### Option 2: Early Classification (Alternative)
**Impact**: Medium

**Approach**: Classify during PDF conversion, skip non-financial pages early

**Questions**:
1. **Accuracy Tradeoff**: Can we use lower resolution for classification pass?
2. **Progressive Processing**: Worth implementing, or add complexity?
3. **Batch Processing**: Process pages in chunks (convert → classify → extract)?

**Potential Savings**: 100-150 seconds

### Option 3: Image Optimization (Supplementary)
**Impact**: Low-Medium

**Approach**: Reduce image quality for classification, full quality for extraction

**Questions**:
1. **Quality Threshold**: Minimum DPI for accurate classification?
2. **API Performance**: Does image size significantly affect API response time?
3. **Dual Pass**: Overhead of converting at two quality levels worth the savings?

**Potential Savings**: 50-100 seconds

---

## Technical Considerations

### Current Constraints
- Anthropic API rate limits (unknown limits)
- Memory constraints for 54-page images
- Error handling for partial failures
- Thread safety considerations

### What We Need to Know
1. **API Rate Limits**: Max concurrent requests, tokens/minute?
2. **Batching**: Supported for vision APIs?
3. **Best Practice**: ThreadPoolExecutor vs asyncio for anthropic-sdk?
4. **Error Handling**: How to gracefully handle rate limit errors?
5. **Cost Impact**: Parallel calls = linear cost increase?

---

## Proposed Implementation Strategy

### Phase 1: Parallel Extraction (18 pages)
- **Why**: Simpler, fewer pages
- **Approach**: ThreadPoolExecutor with 4-8 workers
- **Risk**: Low
- **Estimated Savings**: 180s (220s → 40s)

### Phase 2: Parallel Classification (54 pages)
- **Why**: Biggest bottleneck (334s)
- **Approach**: ThreadPoolExecutor with 8-12 workers
- **Risk**: Medium (rate limits)
- **Estimated Savings**: 250s (334s → 80s)

### Phase 3: Rate Limiting & Polish
- Rate limit handling
- Progress indicators
- Error recovery

**Expected Result**: ~120s total (90% improvement)

---

## Specific Questions for Review

### Technical Architecture
1. ThreadPoolExecutor or asyncio for this use case?
2. Optimal worker count for 54 API calls?
3. How to implement rate limiting with parallel calls?
4. Should we batch operations or process individually?

### API Usage
5. Does Anthropic support batch image classification?
6. What are actual rate limits for concurrent requests?
7. Any SDK features for parallelization we should use?
8. Cost implications of parallel vs sequential?

### Implementation Priorities
9. Which optimization should we implement first?
10. What are the risks we should monitor?
11. How to measure success and iterate?

---

## Next Steps

Requesting guidance on:
- Recommended parallelization approach
- Optimal worker counts
- Rate limiting strategy
- Any SDK features or patterns we should leverage

**Timeline**: Need to implement within next sprint for production readiness  
**Goal**: Reduce origin file processing from 12 minutes to 2 minutes

---

**Appendix**: Full timing data and code structure available in:
- `tests/outputs/AFS2024_extraction_results.json`
- `core/pdf_processor.py`
- `core/extractor.py`