# 🧪 Financial Statement Transcription API - Testing Guide

A comprehensive guide for testing the Financial Statement Transcription API, including test files, validation methodology, and assessment criteria.

## 📋 Table of Contents

- [Overview](#overview)
- [Test File Organization](#test-file-organization)
- [Test Files Description](#test-files-description)
- [Assessment Methodology](#assessment-methodology)
- [Validation Framework](#validation-framework)
- [Testing Commands](#testing-commands)
- [Performance Benchmarks](#performance-benchmarks)
- [Quality Metrics](#quality-metrics)
- [Troubleshooting](#troubleshooting)

## 🌟 Overview

This testing framework provides comprehensive validation of the Financial Statement Transcription API using real-world financial documents and standardized assessment criteria. The framework includes:

- **4 Light Test Files**: Extracted financial statement pages for primary testing
- **4 Origin Test Files**: Complete annual reports for comprehensive testing
- **5 Template Files**: Expected output formats for validation
- **Automated Assessment**: Field-by-field comparison against expected results
- **Performance Benchmarks**: Processing time and accuracy metrics

## 📁 Test File Organization

```
tests/fixtures/
├── origin/           # Original large PDF documents (full financial reports)
├── light/            # Extracted statement pages (focused financial statements)
├── templates/        # Master template and filled templates
└── expected/         # Expected output files for validation
```

## 📄 Test Files Description

### Light Files (Primary Testing)

**Location**: `tests/fixtures/light/`
**Purpose**: Focused financial statement pages for API testing
**Size**: 50KB - 2MB (extracted pages only)
**Use Case**: Primary API testing, validation testing, development

#### 1. AFS2024 - statement extracted.pdf
- **Company**: WIRELESS SERVICES ASIA INC.
- **Document Type**: Statements of Financial Position
- **Years**: 2024, 2023
- **Pages**: 3 (Financial Position, Operations, Changes in Equity)
- **File Size**: 298KB
- **Expected Fields**: 32 financial fields
- **Test Status**: ✅ **BENCHMARK FILE** - Highest accuracy (84.6%)
- **Key Features**: 
  - Multi-year comparative data
  - Complete balance sheet structure
  - High-quality extraction results
  - Standard field naming convention

#### 2. AFS-2022 - statement extracted.pdf
- **Company**: Ideal Marketing & Manufacturing Corporation
- **Document Type**: Statements of Financial Position
- **Years**: 2022, 2021
- **Pages**: 4 (Financial Position, Changes in Equity, Cash Flows, Income)
- **File Size**: 57KB
- **Expected Fields**: 25 financial fields
- **Test Status**: ⚠️ **GOOD** - 72.5% accuracy
- **Key Features**:
  - Manufacturing company financials
  - Inventory-heavy balance sheet
  - Standard field structure
  - Good data extraction

#### 3. 2021 AFS with SEC Stamp - statement extracted.pdf
- **Company**: Metechs Industrial Corporation
- **Document Type**: Comparative Statement of Financial Position
- **Years**: 2021, 2020
- **Pages**: 5 (Financial Position, Income, Changes in Equity, Cost of Goods, Cash Flows)
- **File Size**: 2MB
- **Expected Fields**: 26 financial fields
- **Test Status**: ✅ **GOOD** - 79.1% accuracy
- **Key Features**:
  - SEC-filed document
  - Industrial manufacturing company
  - Comprehensive financial statements
  - High-quality document structure

#### 4. afs-2021-2023 - statement extracted.pdf
- **Company**: GBS Concept Advertising Inc.
- **Document Type**: Multiple Financial Statements
- **Years**: 2022, 2021 (and 2021, 2020)
- **Pages**: 8 (Multiple years of statements)
- **File Size**: 719KB
- **Expected Fields**: 17 financial fields
- **Test Status**: ⚠️ **PARTIAL** - 83.5% accuracy but field mapping issues
- **Key Features**:
  - Multi-year document (2020-2023)
  - Advertising/creative industry
  - Different data structure
  - Field mapping challenges

### Origin Files (Comprehensive Testing)

**Location**: `tests/fixtures/origin/`
**Purpose**: Full financial reports for comprehensive testing
**Size**: 5MB - 50MB (complete annual reports)
**Use Case**: End-to-end testing, performance testing, production validation

#### 1. AFS2024.pdf
- **Company**: WIRELESS SERVICES ASIA INC.
- **Document Type**: Complete Annual Financial Statement
- **Content**: Full annual report with all financial statements
- **Use Case**: Complete document processing validation

#### 2. AFS-2022.pdf
- **Company**: Ideal Marketing & Manufacturing Corporation
- **Document Type**: Complete Annual Financial Statement
- **Content**: Full annual report with all financial statements
- **Use Case**: Manufacturing company validation

#### 3. 2021 AFS with SEC Stamp.pdf
- **Company**: Metechs Industrial Corporation
- **Document Type**: SEC-filed Annual Report
- **Content**: Complete SEC-filed annual report
- **Use Case**: SEC compliance validation

#### 4. afs-2021-2023.pdf
- **Company**: GBS Concept Advertising Inc.
- **Document Type**: Multi-year Annual Reports
- **Content**: Multiple years of complete annual reports
- **Use Case**: Multi-year document processing

### Template Files (Validation Standards)

**Location**: `tests/fixtures/templates/`
**Purpose**: Template structure and expected output format
**Use Case**: Output validation, format comparison, accuracy assessment

#### 1. FS_Input_Template_Fields.csv
- **Purpose**: Master template with 91 standardized fields
- **Structure**: Category, Subcategory, Field, Confidence, Confidence_Score, Value_Year_1, Value_Year_2, Value_Year_3, Value_Year_4
- **Categories**: Meta, Balance Sheet, Income Statement, Cash Flow Statement
- **Use Case**: Template format validation

#### 2. FS_Input_Template_Fields_AFS2024.csv
- **Purpose**: Expected output for AFS2024 document
- **Fields with Data**: 32 financial fields
- **Accuracy Benchmark**: 84.6% target
- **Use Case**: AFS2024 validation

#### 3. FS_Input_Template_Fields_AFS-2022.csv
- **Purpose**: Expected output for AFS-2022 document
- **Fields with Data**: 25 financial fields
- **Accuracy Benchmark**: 72.5% target
- **Use Case**: AFS-2022 validation

#### 4. FS_Input_Template_Fields_2021_AFS_with_SEC_Stamp.csv
- **Purpose**: Expected output for 2021 AFS SEC document
- **Fields with Data**: 26 financial fields
- **Accuracy Benchmark**: 79.1% target
- **Use Case**: SEC document validation

#### 5. FS_Input_Template_Fields_afs_2021_2023.csv
- **Purpose**: Expected output for afs-2021-2023 document
- **Fields with Data**: 17 financial fields
- **Accuracy Benchmark**: 83.5% target
- **Use Case**: Multi-year document validation

## 📊 Assessment Methodology

### Validation Framework

The API testing uses a comprehensive validation framework that measures:

1. **Template Compliance**: Format and structure validation
2. **Data Accuracy**: Field-by-field comparison against expected values
3. **Field Coverage**: Number of fields extracted vs expected
4. **Performance Metrics**: Processing time and reliability
5. **Quality Scores**: Confidence levels and data integrity

### Assessment Process

#### 1. Template Compliance Validation
```bash
# Check CSV format compliance
python tests/compare_results_vs_expected.py
```

**Metrics**:
- ✅ **Format Compliance**: 100% (perfect CSV structure)
- ✅ **Field Structure**: Category, Subcategory, Field columns
- ✅ **Multi-year Support**: Value_Year_1, Value_Year_2 columns
- ✅ **Confidence Scoring**: Confidence and Confidence_Score columns

#### 2. Field Extraction Assessment (Primary Metric)
**Method**: Fields Extracted / Fields Expected (only counting fields with actual data)

```bash
# Run field extraction analysis
python tests/analyze_field_extraction_accuracy.py
```

**Metrics**:
- **Overall Extraction Rate**: 41.0% (41/100 fields with data extracted)
- **Per-File Extraction Rates**: 11.8% - 65.6%
- **Data Quality**: High confidence scores (0.95) for extracted fields
- **Multi-year Accuracy**: Proper 2-year comparative data extraction

**Results**:
| File | Fields Extracted | Fields Expected | **Extraction Rate** | Status |
|------|------------------|-----------------|---------------------|--------|
| AFS2024 | 21 | 32 | **65.6%** | ⚠️ GOOD |
| AFS-2022 | 9 | 25 | **36.0%** | ❌ NEEDS IMPROVEMENT |
| 2021 AFS SEC | 9 | 26 | **34.6%** | ❌ NEEDS IMPROVEMENT |
| afs-2021-2023 | 2 | 17 | **11.8%** | ❌ NEEDS IMPROVEMENT |

#### 3. Data Accuracy Assessment (Secondary Metric)
**Method**: Field-by-field comparison against expected templates (including empty matches)

**Metrics**:
- **Template Format Accuracy**: 79.9% (291/364 fields match exactly)
- **Per-File Format Accuracy**: 72.5% - 84.6%
- **Note**: This includes empty field matches and is less meaningful than extraction rate

#### 4. Performance Benchmarks
**Method**: Processing time measurement and reliability testing

**Results**:
- **PDF Conversion**: 15-27 seconds
- **Individual Image Processing**: 10-26 seconds per image
- **Total Processing**: 70-150 seconds per document
- **Template CSV Generation**: <1 second
- **Success Rate**: 100% (all files processed successfully)

### Quality Metrics

#### Field Extraction Thresholds (Primary Metric)
- **Excellent**: ≥80% extraction rate
- **Good**: 60-79% extraction rate
- **Acceptable**: 40-59% extraction rate
- **Needs Improvement**: <40% extraction rate

#### Template Format Thresholds (Secondary Metric)
- **Excellent**: ≥90% format accuracy
- **Good**: 80-89% format accuracy
- **Acceptable**: 70-79% format accuracy
- **Needs Improvement**: <70% format accuracy

#### Current Performance
- **Overall Extraction Rate**: 41.0% (Needs Improvement)
- **Template Compliance**: 100% (Excellent)
- **Processing Reliability**: 100% (Excellent)
- **Template Format Accuracy**: 79.9% (Good)

## 🚀 Testing Commands

### Individual File Testing
```bash
# Test AFS2024 (benchmark file)
python tests/extract_afs2024_to_template_csv.py

# Test AFS-2022
python tests/extract_afs_2022_robust.py

# Test 2021 AFS with SEC Stamp
python tests/extract_2021_afs_sec_robust.py

# Test afs-2021-2023
python tests/extract_afs_2021_2023_robust.py
```

### Comprehensive Validation
```bash
# Run field extraction analysis (PRIMARY METRIC)
python tests/analyze_field_extraction_accuracy.py

# Run full comparison against expected templates (SECONDARY METRIC)
python tests/compare_results_vs_expected.py

# Run enhanced API testing
python tests/test_api_enhanced.py --category light

# Test individual file with timeout
python tests/test_api_enhanced.py --file "AFS2024 - statement extracted.pdf" --timeout 300
```

### Performance Testing
```bash
# Test all light files with performance metrics
python tests/test_api_enhanced.py --category light --verbose

# Test with custom timeout
python tests/test_api_enhanced.py --timeout 600 --category light
```

### API Endpoint Testing
```bash
# Test single document via API
curl -X POST "http://localhost:8080/extract" \
  -F "file=@tests/fixtures/light/AFS2024 - statement extracted.pdf" \
  -F "statement_type=balance_sheet"

# Test all light files
for file in tests/fixtures/light/*.pdf; do
  echo "Testing: $file"
  curl -X POST "http://localhost:8080/extract" \
    -F "file=@$file" \
    -F "statement_type=balance_sheet"
done
```

## 📈 Performance Benchmarks

### Expected Performance
- **Small documents** (1-2 pages): 40-65 seconds
- **Medium documents** (3-5 pages): 85-120 seconds  
- **Large documents** (6+ pages): 120-300 seconds

### Performance Breakdown
- **PDF Conversion**: 19-23 seconds for 3-page documents
- **Individual Image Processing**: 20-45 seconds per image
- **Template CSV Generation**: <1 second
- **Total Processing**: Varies by document size and complexity

### Success Criteria
- **Processing Success Rate**: ≥95%
- **Template Compliance**: 100%
- **Field Extraction Rate**: ≥60% (Primary metric)
- **Template Format Accuracy**: ≥70% (Secondary metric)
- **Processing Time**: Within expected ranges

## 🔍 Quality Metrics

### Template Compliance
- **Format Structure**: Perfect CSV format match
- **Field Organization**: Proper Category, Subcategory, Field structure
- **Multi-year Support**: Correct Value_Year_1, Value_Year_2 formatting
- **Confidence Scoring**: Proper High/Medium confidence levels

### Data Accuracy
- **Exact Matches**: Values match expected templates exactly
- **Field Mapping**: Correct mapping to template field locations
- **Data Types**: Proper numerical formatting
- **Multi-year Data**: Accurate 2-year comparative extraction

### Field Coverage
- **Balance Sheet**: Current Assets, Non-Current Assets, Liabilities, Equity
- **Income Statement**: Revenue, Expenses, Profit/Loss (when available)
- **Cash Flow**: Operating, Investing, Financing activities (when available)
- **Meta Data**: Company name, period, currency, years detected

## 🔧 Troubleshooting

### Common Issues

#### 1. Field Mapping Differences
**Problem**: Fields extracted but mapped to wrong template locations
**Solution**: 
- Check field name variations in extracted data
- Update field mapping dictionary
- Verify template field names match extracted data

#### 2. Missing Data Fields
**Problem**: Expected fields not extracted
**Solution**:
- Check document structure and quality
- Verify AI extraction prompts
- Review field mapping completeness

#### 3. Processing Timeouts
**Problem**: API requests timing out
**Solution**:
- Increase timeout to 300+ seconds
- Check document size and complexity
- Monitor processing progress

#### 4. Template Format Issues
**Problem**: CSV format not matching template
**Solution**:
- Verify CSV generation logic
- Check field ordering and structure
- Validate confidence score formatting

### Debug Commands
```bash
# Debug individual extraction
python tests/debug_afs2024_extraction.py

# Check template compliance
python tests/compare_results_vs_expected.py

# Validate field mapping
python tests/extract_afs2024_to_template_csv.py
```

## 📊 Test Results Summary

### Current Performance (January 2025)
- **Overall Extraction Rate**: 41.0% (Primary metric)
- **Template Format Accuracy**: 79.9% (Secondary metric)
- **Template Compliance**: 100%
- **Processing Success Rate**: 100%
- **Processing Time**: 70-150 seconds per document

### Per-File Results
| File | **Extraction Rate** | Status | Fields | Processing Time |
|------|---------------------|--------|--------|-----------------|
| AFS2024 | **65.6%** | ⚠️ Good | 21/32 | 85-120s |
| AFS-2022 | **36.0%** | ❌ Needs Improvement | 9/25 | ~70s |
| 2021 AFS SEC | **34.6%** | ❌ Needs Improvement | 9/26 | ~100s |
| afs-2021-2023 | **11.8%** | ❌ Needs Improvement | 2/17 | ~150s |

### Production Readiness
- **Status**: ⚠️ **NEEDS IMPROVEMENT**
- **Strengths**: Perfect template compliance, robust processing, good format accuracy
- **Limitations**: Low field extraction rate (41.0%), significant field mapping issues
- **Recommendation**: Improve field extraction before production deployment

---

*Last updated: January 2025 - v1.1.0*
