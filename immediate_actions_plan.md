# 🎯 Immediate Actions Plan

## 📋 **Three Critical Actions Required**

Based on the cleanup summary and the relevant MD files, here are the three immediate actions needed:

---

## **Action 1: Implement Core CSV Export Function** 🏗️

### **Objective**
Create a centralized, reusable CSV export function that can be used across all future tests and API functionality.

### **Current State Analysis**
- **Existing**: `tests/extract_afs2024_to_template_csv.py` - Working template CSV generator
- **Problem**: Scattered CSV export logic across multiple files
- **Solution**: Centralize into `tests/core/csv_exporter.py`

### **Implementation Steps**

#### **Step 1.1: Create Core Directory Structure**
```bash
mkdir -p tests/core
```

#### **Step 1.2: Implement Core CSV Exporter**
**File**: `tests/core/csv_exporter.py`

**Key Features to Implement**:
- Template-compliant CSV generation
- Multiple output formats (summary, detailed, template)
- Configurable field mapping
- Error handling and validation
- Reusable across all test types

**Core Functions**:
```python
class CSVExporter:
    def __init__(self, template_path: str = "tests/fixtures/templates/FS_Input_Template_Fields.csv")
    def export_to_template_csv(self, extracted_data: Dict[str, Any], output_path: str) -> bool
    def export_to_summary_csv(self, test_results: List[Dict], output_path: str) -> bool
    def export_to_detailed_csv(self, extracted_data: Dict[str, Any], output_path: str) -> bool
    def validate_template_compliance(self, csv_path: str) -> Dict[str, Any]
```

#### **Step 1.3: Port Existing Logic**
- Extract field mapping logic from `tests/extract_afs2024_to_template_csv.py`
- Port template CSV generation functionality
- Add comprehensive field mapping system
- Implement error handling and validation

#### **Step 1.4: Integration Points**
- **API Integration**: Update `api_app.py` to use core CSV exporter
- **Test Integration**: Update `tests/test_api_enhanced.py` to use core exporter
- **Replacement**: Replace `tests/export_financial_data_to_csv.py` with core function

### **Success Criteria**
- [ ] Core CSV exporter module created
- [ ] Template CSV generation working
- [ ] Field mapping system implemented
- [ ] Error handling and validation added
- [ ] API integration updated
- [ ] Test integration updated

---

## **Action 2: Update Documentation** 📝

### **Objective**
Update all documentation to remove references to deleted debug and extract files, and ensure consistency with current implementation.

### **Current State Analysis**
- **Problem**: Documentation references 18 deleted files
- **Impact**: Broken examples, outdated file paths, misleading information
- **Solution**: Comprehensive documentation update

### **Files to Update**

#### **Step 2.1: Update API_GUIDE.md**
**Critical Changes**:
- Remove references to deleted extract scripts:
  - `python tests/extract_afs2024_to_template_csv.py`
  - `python tests/extract_origin_afs2024_robust.py`
  - `python tests/extract_afs_2021_2023_robust.py`
  - `python tests/extract_2021_afs_sec_robust.py`
  - `python tests/extract_afs_2022_robust.py`
  - `python tests/extract_afs2024_robust.py`
  - `python tests/extract_afs2024_to_csv.py`

- Add references to core CSV export functionality:
  - `python tests/core/csv_exporter.py`
  - `python tests/export_financial_data_to_csv.py`

- Update file paths in examples
- Update script references
- Add core CSV export documentation

#### **Step 2.2: Update TESTING_GUIDE.md**
**Critical Changes**:
- Remove all debug script references:
  - `python tests/debug_image_resize.py`
  - `python tests/debug_base64_encoding.py`
  - `python tests/debug_afs2024_extraction.py`
  - `python tests/debug_ai_response.py`
  - `python tests/debug_real_image.py`
  - `python tests/debug_pdf_processing.py`
  - `python tests/debug_extraction.py`
  - `python tests/debug_test.py`
  - `python tests/debug_session_state.py`
  - `python tests/debug_button.py`

- Update test file structure:
  ```
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

- Update curl commands and examples
- Add core CSV export references

#### **Step 2.3: Update Other Documentation**
- **POPPLER_INTEGRATION_PLAN.md**: Review for deleted file references
- **PHASED_EXTRACTION_MIGRATION_PLAN.md**: Update implementation status

### **Success Criteria**
- [ ] No references to deleted debug scripts
- [ ] No references to deleted extract scripts
- [ ] All file paths are current and valid
- [ ] All script examples work with current codebase
- [ ] References to core CSV export functionality
- [ ] Consistent with current API structure
- [ ] Updated test file structure
- [ ] Current curl commands and examples

---

## **Action 3: Test All Examples** 🧪

### **Objective**
Test all examples in documentation to ensure they work with the current codebase.

### **Current State Analysis**
- **Problem**: Documentation examples may be broken after file deletions
- **Risk**: Users following documentation will encounter errors
- **Solution**: Comprehensive testing of all examples

### **Testing Steps**

#### **Step 3.1: Test Script Examples**
**Test Commands**:
```bash
# Test core CSV export functionality
python tests/core/csv_exporter.py

# Test main CSV export script
python tests/export_financial_data_to_csv.py

# Test API enhanced script
python tests/test_api_enhanced.py --file "AFS2024 - statement extracted.pdf"

# Test all light files
python tests/test_api_enhanced.py --category light
```

#### **Step 3.2: Test API Examples**
**Test API Endpoints**:
```bash
# Test health endpoint
curl -X GET "http://localhost:8000/health"

# Test extract endpoint
curl -X POST "http://localhost:8000/extract" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@tests/fixtures/light/AFS2024 - statement extracted.pdf"

# Test API documentation
curl -X GET "http://localhost:8000/docs"
```

#### **Step 3.3: Test File Paths**
**Verify File Existence**:
- [ ] `tests/core/csv_exporter.py` exists
- [ ] `tests/export_financial_data_to_csv.py` exists
- [ ] `tests/test_api_enhanced.py` exists
- [ ] `tests/fixtures/light/` directory exists
- [ ] `tests/fixtures/origin/` directory exists
- [ ] `tests/fixtures/templates/` directory exists

#### **Step 3.4: Test Cross-References**
**Validate Consistency**:
- [ ] All documentation files reference same scripts
- [ ] File paths consistent across all documentation
- [ ] Examples work with current codebase
- [ ] No broken links or references

### **Success Criteria**
- [ ] All script examples execute successfully
- [ ] All API examples work correctly
- [ ] All file paths are valid
- [ ] No broken references in documentation
- [ ] Cross-reference validation passes
- [ ] All examples produce expected output

---

## **📊 Implementation Priority**

### **Priority 1: Core CSV Export Function**
- **Why First**: Foundation for all other functionality
- **Dependencies**: None
- **Impact**: High - enables centralized CSV export

### **Priority 2: Documentation Updates**
- **Why Second**: Depends on core CSV export being implemented
- **Dependencies**: Action 1 completion
- **Impact**: High - ensures documentation accuracy

### **Priority 3: Test All Examples**
- **Why Third**: Depends on both previous actions
- **Dependencies**: Actions 1 & 2 completion
- **Impact**: Critical - validates everything works

---

## **🎯 Success Metrics**

### **Overall Success Criteria**
1. **All CSV outputs** use the core CSV exporter
2. **Template compliance** validated across all outputs
3. **Field mapping** consistent and maintainable
4. **Error handling** robust and informative
5. **Documentation** updated to reference core function
6. **Tests** validate CSV export functionality
7. **All examples** work with current codebase
8. **No broken references** in documentation

### **Quality Assurance**
- [ ] All examples execute without errors
- [ ] All file paths are valid and accessible
- [ ] Documentation is consistent across all files
- [ ] Core CSV export functionality is robust
- [ ] Template compliance is maintained
- [ ] Error handling is comprehensive

---

## **🚨 Critical Dependencies**

### **Must Complete in Order**
1. **Action 1** must complete before Action 2 (documentation references core CSV export)
2. **Action 2** must complete before Action 3 (testing validates updated documentation)
3. **Action 3** validates that Actions 1 & 2 were successful

### **Blocking Issues**
- If core CSV export fails, documentation updates will be incomplete
- If documentation updates fail, testing will fail
- If testing fails, the entire implementation is invalid

### **Risk Mitigation**
- Test each action independently before proceeding
- Validate success criteria at each step
- Have rollback plan for each action
- Document any issues encountered

This plan ensures a systematic, validated approach to implementing the three critical actions needed after the codebase cleanup.

