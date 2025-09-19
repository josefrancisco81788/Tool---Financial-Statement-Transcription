# 📝 Documentation Update Plan

## 🎯 **Objective**
Update all documentation to remove references to deleted debug and extract files, and ensure consistency with current implementation.

## 📋 **Files to Update**

### **1. API_GUIDE.md**
**Current Issues**:
- References to deleted extract files in examples
- Outdated file paths and script names
- Missing references to core CSV export functionality

**Updates Needed**:
```markdown
# Remove these references:
- "python tests/extract_afs2024_to_template_csv.py" 
- "python tests/extract_origin_afs2024_robust.py"
- Any references to debug scripts

# Add these references:
- Core CSV export functionality
- Updated test script names
- Current working file paths
```

### **2. TESTING_GUIDE.md**
**Current Issues**:
- References to deleted debug and extract scripts
- Outdated curl commands and examples
- Missing references to current test structure

**Updates Needed**:
```markdown
# Remove these references:
- All debug script examples
- Deleted extract script references
- Outdated file paths

# Add these references:
- Current test script structure
- Core CSV export functionality
- Updated API endpoints
```

### **3. POPPLER_INTEGRATION_PLAN.md**
**Current Issues**:
- May reference deleted debug scripts
- Need to ensure consistency with current implementation

**Updates Needed**:
- Review for any references to deleted files
- Update any outdated script references
- Ensure consistency with current API structure

### **4. PHASED_EXTRACTION_MIGRATION_PLAN.md**
**Current Issues**:
- May reference deleted extract scripts
- Need to update with current implementation status

**Updates Needed**:
- Remove references to deleted extract scripts
- Update implementation status
- Ensure consistency with current API

## 🔍 **Specific Documentation Changes**

### **API_GUIDE.md Changes**

#### **Remove These Sections**:
```markdown
# Remove from "Running Tests" section:
python tests/extract_afs2024_to_template_csv.py
python tests/extract_origin_afs2024_robust.py
python tests/extract_afs_2021_2023_robust.py
python tests/extract_2021_afs_sec_robust.py
python tests/extract_afs_2022_robust.py
python tests/extract_afs2024_robust.py
python tests/extract_afs2024_to_csv.py
```

#### **Add These Sections**:
```markdown
# Add to "Running Tests" section:
python tests/export_financial_data_to_csv.py
python tests/core/csv_exporter.py  # New core CSV export
```

#### **Update Examples**:
```markdown
# Update file paths in examples:
- Change: "tests/extract_afs2024_to_template_csv.py"
- To: "tests/export_financial_data_to_csv.py"

# Update script references:
- Change: "extract_afs2024_to_template_csv.py"
- To: "export_financial_data_to_csv.py"
```

### **TESTING_GUIDE.md Changes**

#### **Remove These Sections**:
```markdown
# Remove all debug script examples:
python tests/debug_image_resize.py
python tests/debug_base64_encoding.py
python tests/debug_afs2024_extraction.py
python tests/debug_ai_response.py
python tests/debug_real_image.py
python tests/debug_pdf_processing.py
python tests/debug_extraction.py
python tests/debug_test.py
python tests/debug_session_state.py
python tests/debug_button.py
```

#### **Update Test Structure**:
```markdown
# Update test file structure:
tests/
├── core/
│   └── csv_exporter.py          # New core CSV export
├── export_financial_data_to_csv.py  # Main CSV export script
├── test_api_enhanced.py         # Main API test script
└── fixtures/
    ├── light/                   # Light test files
    ├── origin/                  # Origin test files
    └── templates/               # Template files
```

### **POPPLER_INTEGRATION_PLAN.md Changes**

#### **Review and Update**:
- Check for any references to deleted debug scripts
- Update any outdated file paths
- Ensure consistency with current API structure
- Update any script examples

### **PHASED_EXTRACTION_MIGRATION_PLAN.md Changes**

#### **Update Implementation Status**:
- Remove references to deleted extract scripts
- Update with current API implementation status
- Ensure consistency with current functionality
- Update any outdated examples

## 📊 **Documentation Validation**

### **Checklist for Each File**:
- [ ] No references to deleted debug scripts
- [ ] No references to deleted extract scripts
- [ ] All file paths are current and valid
- [ ] All script examples work with current codebase
- [ ] References to core CSV export functionality
- [ ] Consistent with current API structure
- [ ] Updated test file structure
- [ ] Current curl commands and examples

### **Cross-Reference Validation**:
- [ ] All documentation files reference same scripts
- [ ] File paths consistent across all documentation
- [ ] Examples work with current codebase
- [ ] No broken links or references

## 🎯 **Implementation Steps**

### **Step 1: Review Current Documentation**
1. Read through all documentation files
2. Identify references to deleted files
3. Note outdated examples and paths
4. Create comprehensive change list

### **Step 2: Update API_GUIDE.md**
1. Remove references to deleted extract scripts
2. Update test script examples
3. Add references to core CSV export
4. Update file paths and examples

### **Step 3: Update TESTING_GUIDE.md**
1. Remove all debug script references
2. Update test file structure
3. Update curl commands and examples
4. Add core CSV export references

### **Step 4: Update Other Documentation**
1. Review POPPLER_INTEGRATION_PLAN.md
2. Update PHASED_EXTRACTION_MIGRATION_PLAN.md
3. Ensure consistency across all files
4. Validate all examples work

### **Step 5: Final Validation**
1. Test all examples in documentation
2. Verify all file paths are valid
3. Check for broken references
4. Ensure consistency across all files

## 📈 **Success Criteria**

1. **No references** to deleted debug or extract files
2. **All examples** work with current codebase
3. **File paths** are current and valid
4. **Core CSV export** functionality documented
5. **Consistency** across all documentation files
6. **All curl commands** and examples work
7. **Test structure** accurately documented

## 🚨 **Critical Updates**

### **Must Update**:
- All script examples in API_GUIDE.md
- Test file structure in TESTING_GUIDE.md
- Any references to deleted files
- File paths in all examples

### **Should Update**:
- Add core CSV export documentation
- Update test script references
- Ensure consistency across files
- Validate all examples work

This plan ensures all documentation is accurate, current, and consistent with the cleaned-up codebase.

