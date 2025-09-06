# API Testing Guide

This directory contains test files and testing instructions for the Financial Statement Transcription API.

## Directory Structure

```
tests/fixtures/
├── origin/           # Original large PDF documents (full financial reports)
├── light/            # Extracted statement pages (focused financial statements)
├── templates/        # Master template and filled templates
└── expected/         # Expected output files for validation
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

### Expected Output
**Location**: `tests/fixtures/expected/`
- API response JSON files for each test document
- Validation results and comparison data

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

### Performance Testing with Origin Files
```bash
# Test with full documents
for file in tests/fixtures/origin/*.pdf; do
  echo "Testing: $file"
  time curl -X POST "http://localhost:8080/extract" \
    -F "file=@$file" \
    -F "statement_type=balance_sheet"
done
```

## Validation

Compare API output against expected templates:
- Check year coverage (all years present)
- Validate row counts
- Verify data accuracy
- Ensure proper JSON structure
