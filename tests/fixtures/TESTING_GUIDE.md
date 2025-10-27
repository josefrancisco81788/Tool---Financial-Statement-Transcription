# API Testing Guide

> **⚠️ PRIMARY USE CASE - READ THIS FIRST**  
> Financial statement documents are typically **30-80 pages long**, containing multiple sections including cover pages, management discussion, auditor reports, notes, and appendices. The actual financial statements (Balance Sheet, Income Statement, Cash Flow Statement) can appear **ANYWHERE** within this document bundle. The terms that must be matched with each template item are not known in advance and so deterministic matching is not viable.  
> **CRITICAL**: These PDFs are **non-OCR scanned documents** - they contain only images, not extractable text.

This directory contains test files and testing instructions for the Financial Statement Transcription API.

## ⚠️ Test File Types - CRITICAL DISTINCTION

### 🎯 ORIGIN Files = PRIMARY USE CASE
**Location**: `tests/fixtures/origin/`  
**Document Type**: Full 30-80 page annual reports  
**Content**: Cover pages, MD&A, auditor reports, notes, appendices + financial statements  
**Financial Statements Location**: UNPREDICTABLE (can be anywhere in document)  
**Format**: Non-OCR scanned images (no extractable text)  
**Use For**: Production validation, end-to-end testing, performance benchmarks  
**Priority**: ✅ **ALWAYS TEST ON THESE FIRST**

### 🔧 LIGHT Files = UNIT TESTING ONLY
**Location**: `tests/fixtures/light/`  
**Document Type**: Pre-extracted statement pages (3-8 pages)  
**Content**: Financial statements ONLY (already isolated)  
**Financial Statements Location**: All pages (statements already found)  
**Format**: Same as origin (scanned images)  
**Use For**: Isolated extraction logic testing, debugging specific fields  
**Priority**: ⚠️ **NOT representative of production use case**

---

## Directory Structure

```
tests/fixtures/
├── origin/           # Original large PDF documents (full financial reports)
├── light/            # Extracted statement pages (focused financial statements)
└── templates/        # Master template and filled templates
```

## File Organization

### Origin Files (Very Large, True Document Examples)
**Location**: `tests/fixtures/origin/`
- `2021 AFS with SEC Stamp.pdf`
- `afs-2021-2023.pdf`
- `AFS-2022.pdf`
- `AFS2024.pdf`

**Purpose**: Full financial reports for comprehensive testing
**Size**: Large files (full annual reports)
**Use Case**: End-to-end testing, performance testing

### Light Files (Extracted Statement Pages)
**Location**: `tests/fixtures/light/`
- `2021 AFS with SEC Stamp - statement extracted.pdf`
- `afs-2021-2023 - statement extracted.pdf`
- `AFS-2022 - statement extracted.pdf`
- `AFS2024 - statement extracted.pdf`

**Purpose**: Focused financial statement pages for API testing
**Size**: Smaller files (extracted pages only)
**Use Case**: Primary API testing, validation testing

### Templates
**Location**: `tests/fixtures/templates/`
- `FS_Input_Template_Fields.csv` - Master template
- `FS_Input_Template_Fields_2021_AFS_with_SEC_Stamp.csv` - Filled template
- `FS_Input_Template_Fields_afs_2021_2023.csv` - Filled template
- `FS_Input_Template_Fields_AFS-2022.csv` - Filled template
- `FS_Input_Template_Fields_AFS2024.csv` - Filled template

**Purpose**: Template structure and expected output format
**Use Case**: Output validation, format comparison

### Test Results
**Location**: `tests/results/`
- API response JSON files for each test document
- CSV export results and validation data
- Performance metrics and scoring results

## Testing Strategy

### 1. Light Files Testing (Primary)
- Use `tests/fixtures/light/` files for regular API testing
- These are the focused financial statement pages
- Faster processing, easier validation

### 2. Origin Files Testing (Comprehensive)
- Use `tests/fixtures/origin/` files for full document testing
- Test complete annual report processing
- Performance and accuracy validation

### 3. Template Validation
- Compare API output against `tests/fixtures/templates/` files
- Validate data structure and completeness
- Ensure proper field mapping

## File Placement Instructions

1. **Copy your test files** to the appropriate directories:
   ```bash
   # Origin files (large)
   cp "2021 AFS with SEC Stamp.pdf" tests/fixtures/origin/
   cp "afs-2021-2023.pdf" tests/fixtures/origin/
   cp "AFS-2022.pdf" tests/fixtures/origin/
   cp "AFS2024.pdf" tests/fixtures/origin/
   
   # Light files (extracted)
   cp "2021 AFS with SEC Stamp - statement extracted.pdf" tests/fixtures/light/
   cp "afs-2021-2023 - statement extracted.pdf" tests/fixtures/light/
   cp "AFS-2022 - statement extracted.pdf" tests/fixtures/light/
   cp "AFS2024 - statement extracted.pdf" tests/fixtures/light/
   
   # Templates
   cp "FS_Input_Template_Fields.csv" tests/fixtures/templates/
   cp "FS_Input_Template_Fields_2021_AFS_with_SEC_Stamp.csv" tests/fixtures/templates/
   cp "FS_Input_Template_Fields_afs_2021_2023.csv" tests/fixtures/templates/
   cp "FS_Input_Template_Fields_AFS-2022.csv" tests/fixtures/templates/
   cp "FS_Input_Template_Fields_AFS2024.csv" tests/fixtures/templates/
   ```

2. **Update .gitignore** to exclude large files:
   ```gitignore
   # Test fixtures (large files)
   tests/fixtures/origin/*.pdf
   tests/fixtures/light/*.pdf
   ```

3. **Create test scripts** to use these files for API testing

## Testing Commands

### API Testing with Light Files
```bash
# Test single document
curl -X POST "http://localhost:8000/extract" \
  -F "file=@tests/fixtures/light/AFS2024 - statement extracted.pdf" \
  -F "statement_type=balance_sheet"

# Test all light files
for file in tests/fixtures/light/*.pdf; do
  echo "Testing: $file"
  curl -X POST "http://localhost:8000/extract" \
    -F "file=@$file" \
    -F "statement_type=balance_sheet"
done
```

### Performance Testing with Origin Files
```bash
# Test with full documents
for file in tests/fixtures/origin/*.pdf; do
  echo "Testing: $file"
  time curl -X POST "http://localhost:8000/extract" \
    -F "file=@$file" \
    -F "statement_type=balance_sheet"
done
```

## CSV Export

The API now returns CSV data directly in responses and supports comprehensive CSV export functionality:

### API CSV Integration
The API now returns:
- `template_csv`: Base64-encoded CSV data
- `template_fields_mapped`: Count of populated template fields

### CSV Export Commands
```bash
# Test core CSV exporter directly
python tests/core/csv_exporter.py

# Export financial data to template CSV
python tests/export_financial_data_to_csv.py <json_file> <output_csv>

# Run enhanced API tests (includes CSV export)
python tests/test_api_enhanced.py --category light

# Run single file with CSV export
python tests/test_api_enhanced.py --file "AFS2024 - statement extracted.pdf"
```

**CSV Output Locations**:
- **Summary CSV**: `tests/results/api_test_results_[timestamp].csv`
- **Template CSV**: Generated from API responses with base64 decoding
- **Core CSV Exporter**: `tests/core/csv_exporter.py` - Centralized CSV export functionality

**Summary CSV Columns**:
- File, Company, Statement Type, Years, Processing Time (s)
- Pages Processed, Line Items Count, Total Assets, Total Liabilities, Total Equity
- Success, Status Code, Error Message

**Template CSV Format**:
- Category, Subcategory, Field, Confidence, Confidence_Score
- Value_Year_1, Value_Year_2, Value_Year_3, Value_Year_4

## Validation

Compare API output against expected templates:
- Check year coverage (all years present)
- Validate row counts
- Verify data accuracy
- Ensure proper JSON structure
