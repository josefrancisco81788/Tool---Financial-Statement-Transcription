# 🧪 Financial Statement Transcription API - Simplified Test Plan

## 📋 Overview

This document outlines the **simplified testing strategy** for the Financial Statement Transcription API. After consolidating scattered test files and removing complex abstractions, we now have a focused, maintainable testing process.

## 🎯 Testing Objectives

### Business Use Case
 - Scan 30-90+ page non-OCR PDFs, save all financial statement data
 - Transcribe financial statement data to fixed template

### CRITICAL CONSTRAINTS:
- PDFs are scanned images (non-selectable text)
- Traditional OCR (Tesseract, PyMuPDF OCR, PaddleOCR) has been tested and FAILS
- ONLY vision model LLMs (GPT-4V, Claude, Gemini Vision) are acceptable
- Do NOT suggest OCR libraries

### Primary Goals
1. **Validate Core Functionality** - Ensure extraction and classification work correctly
2. **Verify Extraction Accuracy** - Confirm data extraction meets production thresholds
3. **Test Performance** - Validate processing times and resource usage
4. **Ensure Reliability** - Test error handling and edge cases
5. **Validate Output Format** - Confirm JSON structure and data completeness

### Success Criteria
- ✅ **Field Extraction Rate**: ≥60% for production readiness
- ✅ **Template Format Accuracy**: ≥70% threshold
- ✅ **Processing Success Rate**: ≥95% threshold
- ✅ **Overall Score**: ≥70% weighted combination
- ✅ **Performance**: <2 minutes processing time per document
- ✅ **Reliability**: 95%+ success rate across test documents

## 🏗️ Simplified Test Architecture

### **Core Test Runners (The New Simplified System)**

#### 1. **Core Application Testing** (`tests/test_core_application.py`)
- **Purpose**: Establish baseline performance on light files
- **Command**: `python tests/test_core_application.py`
- **Tests**: All light files individually
- **Output**: Detailed per-file results and baseline metrics

#### 2. **Classification Testing** (`tests/test_classification.py`)
- **Purpose**: Test four-score classification accuracy
- **Command**: `python tests/test_classification.py`
- **Tests**: Statement type detection across all files
- **Output**: Classification confidence and accuracy metrics

#### 3. **Single File Testing** (`tests/run_extraction_test.py`)
- **Purpose**: Test individual PDF files
- **Command**: `python tests/run_extraction_test.py <pdf_path>`
- **Tests**: Simple, focused extraction test
- **Output**: Results saved to `tests/outputs/`

#### 4. **Full Test Suite** (`tests/run_tests.py`)
- **Purpose**: Comprehensive pytest-based testing
- **Command**: `python tests/run_tests.py`
- **Tests**: Unit, integration, performance, validation
- **Output**: XML reports in `tests/results/`

### **Scoring System**

#### **Primary Metrics**
- **Field Extraction Rate**: `Fields Extracted / Fields Expected × 100`
- **Template Format Accuracy**: `Matching Fields / Total Comparable Fields × 100`
- **CSV Export Integration**: `CSV Fields Mapped / Total Template Fields × 100`

#### **Scoring Commands**
```bash
python tests/analyze_field_extraction_accuracy.py    # Primary metric
python tests/compare_results_vs_expected.py         # Secondary metric
```

#### **Thresholds**
- **Excellent**: ≥80% extraction rate
- **Good**: 60-79% extraction rate  
- **Acceptable**: 40-59% extraction rate
- **Needs Improvement**: <40% extraction rate

## 📊 Test Data Strategy

### Test Documents

#### **Light Files (Primary Testing)**
- **Purpose**: Fast, focused testing
- **Files**: 4 extracted statement pages (e.g.`AFS-2022 - statement extracted.pdf`) in `tests/fixtures/light/`
- **Expected**: 20-30 rows, 2-3 years each
- **Use Case**: Regular testing, baseline establishment

#### **Origin Files (Comprehensive Testing)**
- **Purpose**: Full document processing
- **Files**: 4 complete annual reports (e.g.`AFS-2022.pdf`) in `tests/fixtures/origin/`
- **Expected**: 30+ rows, all years present
- **Use Case**: Performance testing, accuracy validation

#### **Template Validation**
- **Purpose**: Output format validation
- **Files**: 5 CSV templates (e.g. `FS_Input_Template_Fields_AFS-2022.csv`) in `tests/fixtures/templates/`
- **Expected**: Match API output structure
- **Use Case**: Data format validation

#### **Page-Specific Validation**
- **Purpose**: Verify each page of the Light Files
- **Files**: 4 Text Documents (e.g. `DETAILS PER PAGE AFS-2022 - statement extracted.txt`) in `tests/fixtures/templates/`
- **Expected**: Adhoc Inspection check
- **Use Case**: Page-specific analysis of Light Files

## 🧪 Detailed Test Cases

### **1. Core Application Tests**

#### **Baseline Establishment**
```bash
python tests/test_core_application.py
```
- Tests all light files individually
- Establishes baseline performance metrics
- Shows detailed per-file results
- Compares against `BASELINE_TEST_RESULTS_PRE_REFACTOR.md`

#### **Classification Validation**
```bash
python tests/test_classification.py
```
- Tests four-score classification accuracy
- Validates statement type detection
- Tests across all files
- Measures classification confidence

### **2. Individual File Testing**

#### **Single File Extraction**
```bash
python tests/run_extraction_test.py tests/fixtures/light/AFS2024\ -\ statement\ extracted.pdf
```
- Tests individual PDF files
- Simple, focused extraction test
- Saves results to `tests/outputs/`
- Provides detailed extraction metrics

### **3. Comprehensive Test Suite**

#### **Pytest-Based Testing**
```bash
python tests/run_tests.py
```

**Unit Tests** (`tests/unit/`)
- Core extraction logic validation
- Configuration management
- Error handling
- Data processing functions

**Integration Tests** (`tests/integration/`)
- API endpoint functionality
- File upload and processing
- Response format validation
- Error response handling

**Performance Tests** (`tests/performance/`)
- Processing time benchmarks
- Memory usage monitoring
- Concurrent request handling
- Large file processing

**Validation Tests** (`tests/validation/`)
- Output accuracy against templates
- Year coverage validation
- Data completeness checks
- Format consistency

## 🔄 Testing Workflow

### **Daily Testing**
1. **Run Core Application Test**: `python tests/test_core_application.py`
2. **Check Classification**: `python tests/test_classification.py`
3. **Review Results**: Compare against baseline metrics

### **Feature Testing**
1. **Test Single File**: `python tests/run_extraction_test.py <file>`
2. **Run Full Suite**: `python tests/run_tests.py`
3. **Calculate Metrics**: `python tests/analyze_field_extraction_accuracy.py`

### **Regression Testing**
1. **Establish Baseline**: Run core application test
2. **Make Changes**: Implement new features
3. **Re-run Tests**: Compare against baseline
4. **Verify No Regression**: Ensure metrics don't decrease

## 📈 Performance Benchmarks

### **Processing Times**
- **Light Files**: 15-30 seconds processing time
- **Origin Files**: 60-120 seconds processing time
- **Memory Usage**: <2GB peak usage
- **Success Rate**: >95% across all test documents

### **Accuracy Benchmarks**
- **Field Extraction Rate**: ≥60% for production readiness
- **Template Format Accuracy**: ≥70% threshold
- **Year Coverage**: 100% of expected years extracted
- **Data Quality**: Clean numbers, proper confidence scores

## 🚨 Key Principles

### **Simplified Testing Philosophy**
1. **Simple & Direct** - No complex abstractions
2. **Focused** - Each test runner has one clear purpose
3. **Standardized** - Consistent scoring methodology
4. **Maintainable** - Easy to understand and modify
5. **Preserved Functionality** - All working features maintained

### **What Was Simplified**
- **Before**: 18+ scattered test files in root directory
- **After**: 3 focused test runners in `tests/` directory
- **Before**: Complex unified testing system with provider management
- **After**: Simple, direct testing without complex abstractions
- **Before**: Multiple test output formats
- **After**: Standardized scoring framework
- **Before**: Ad-hoc test creation for each scenario
- **After**: All scattered files archived in `tests/archive/`

## 🔧 Maintenance

### **Adding New Tests**
1. **Check existing test runners** - Can it be added to an existing runner?
2. **Keep it simple** - Avoid creating new complex abstractions
3. **Follow patterns** - Use existing test runners as templates
4. **Update scoring** - Ensure new tests integrate with scoring framework

### **Updating Tests**
1. **Reference baseline** - Compare against `BASELINE_TEST_RESULTS_PRE_REFACTOR.md`
2. **Maintain thresholds** - Keep production readiness criteria
3. **Test incrementally** - Make small changes and test frequently
4. **Document changes** - Update this plan when modifying tests

---

## 📞 Quick Reference

### **Essential Commands**
```bash
# Core application baseline test
python tests/test_core_application.py

# Classification accuracy test
python tests/test_classification.py

# Single file test
python tests/run_extraction_test.py <pdf_path>

# Full test suite
python tests/run_tests.py

# Calculate metrics
python tests/analyze_field_extraction_accuracy.py
python tests/compare_results_vs_expected.py
```

### **Key Files**
- `tests/test_core_application.py` - Core application testing
- `tests/test_classification.py` - Classification testing
- `tests/run_extraction_test.py` - Single file testing
- `tests/run_tests.py` - Full test suite
- `tests/SCORING_FRAMEWORK.md` - Scoring methodology
- `BASELINE_TEST_RESULTS_PRE_REFACTOR.md` - Baseline metrics

---

**Last Updated**: October 27, 2025  
**Purpose**: Simplified testing strategy after consolidation  
**Status**: Active - replaces complex unified testing system