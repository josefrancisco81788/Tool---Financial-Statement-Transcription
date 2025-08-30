# Project Folder Structure

## Overview
This document describes the organized folder structure for the Financial Statement Transcription project.

## Directory Structure

```
/
├── data/                          # Data files
│   ├── input/                     # Input files for processing
│   │   ├── documents/             # PDF documents to process
│   │   │   ├── .gitkeep          # Track empty directory
│   │   │   ├── AFS2024.pdf       # Financial statements
│   │   │   ├── AFS2024 - statement extracted.pdf
│   │   │   ├── AFS2022.pdf
│   │   │   ├── afs-2021-2023.pdf
│   │   │   ├── afs-2021-2023 - statement extracted.pdf
│   │   │   ├── 2021 AFS with SEC Stamp.pdf
│   │   │   └── 9_extracted_2021 AFS with SEC Stamp.pdf
│   │   └── samples/               # Sample/test files
│   │       ├── .gitkeep          # Track empty directory
│   │       ├── test_financial_statement.pdf
│   │       └── test_financial_statement.png
│   ├── output/                    # Generated output files (ignored by git)
│   │   ├── extracted_data_*.csv   # CSV output files
│   │   ├── afs2024_extracted_data_*.csv
│   │   └── *_full_response_*.json # JSON response files
│   └── samples/                   # Sample outputs for documentation
│       └── .gitkeep              # Track empty directory
├── tests/                         # Test files
│   ├── outputs/                   # Test-specific outputs (ignored by git)
│   │   ├── test_csv_fix_output.csv
│   │   └── afs2024_proper_format_*.csv
│   └── fixtures/                  # Test data files
│       └── .gitkeep              # Track empty directory
├── api/                           # API application
├── streamlit/                     # Streamlit application
├── docs/                          # Documentation
├── scripts/                       # Utility scripts
├── backups/                       # Backup files
└── [other project files]
```

## File Organization

### Input Files
- **Location**: `data/input/documents/`
- **Purpose**: PDF files to be processed by the API
- **Git Status**: Tracked (but large files may be ignored)
- **Examples**: AFS2024.pdf, financial statements

### Sample Files
- **Location**: `data/input/samples/`
- **Purpose**: Test files for development and testing
- **Git Status**: Tracked
- **Examples**: test_financial_statement.pdf

### Output Files
- **Location**: `data/output/`
- **Purpose**: Generated CSV and JSON files from API processing
- **Git Status**: Ignored (not tracked)
- **Examples**: extracted_data_*.csv, *_full_response_*.json

### Test Outputs
- **Location**: `tests/outputs/`
- **Purpose**: Test-specific output files
- **Git Status**: Ignored (not tracked)
- **Examples**: test_csv_fix_output.csv

## Usage

### For Development
```bash
# Test with sample files
python test_simple_api.py

# Test with real documents
python test_cloudrun_afs2024.py

# Generate test files
python create_test_file.py
```

### For API Testing
```bash
# Upload files from data/input/documents/
curl -X POST "http://localhost:8000/api/v1/extract-financial-data/sync" \
  -F "file=@data/input/documents/AFS2024.pdf" \
  -F "processing_approach=auto" \
  -F "output_format=csv"
```

### File Paths in Scripts
All scripts have been updated to use the new folder structure:
- Input files: `data/input/documents/` or `data/input/samples/`
- Output files: `data/output/` or `tests/outputs/`

## Git Configuration

### .gitignore Rules
```gitignore
# Output folders (ignore all contents)
data/output/
tests/outputs/

# Specific output patterns (backup)
extracted_data_*.csv
*_full_response_*.json
test_csv_fix_output.csv
afs2024_proper_format_*.csv

# Keep .gitkeep files
!data/input/samples/.gitkeep
!data/input/documents/.gitkeep
!data/samples/.gitkeep
!tests/fixtures/.gitkeep
```

### Benefits
1. **Organized Structure**: Clear separation of input, output, and test files
2. **Reduced Repository Size**: Output files are not tracked
3. **Easy File Management**: Logical grouping of related files
4. **Team Collaboration**: Consistent structure across team members
5. **Scalability**: Easy to add new file types and categories

## Migration Notes

This structure was implemented as part of the project reorganization. All scripts and documentation have been updated to use the new paths. The old file locations are no longer supported.
