# 🛡️ CSV Format Standards Enforcement

## Overview
This document establishes mandatory standards and enforcement mechanisms to prevent unauthorized changes to the CSV format specification. **ALL changes to CSV format require approval and must follow the process outlined below.**

## 🚨 Critical Files - DO NOT MODIFY WITHOUT APPROVAL

### Protected Code Files
1. **`api/services/file_processor.py`**
   - Contains `_transform_data_for_csv()` method
   - Contains `_validate_csv_format()` method
   - **CRITICAL**: Any changes require approval

2. **`app.py`**
   - Contains `transform_to_analysis_ready_format()` function
   - Contains `create_ifrs_csv_export()` function
   - **CRITICAL**: Any changes require approval

3. **`validate_csv_success.py`**
   - Automated validation script
   - **CRITICAL**: Must not be modified without approval

### Protected Documentation Files
1. **`CSV_FORMAT_SPECIFICATION.md`**
   - Authoritative specification document
   - **CRITICAL**: Version-controlled, requires approval for changes

2. **`STANDARDS_ENFORCEMENT.md`** (this file)
   - Standards enforcement rules
   - **CRITICAL**: Must not be modified without approval

## 📋 Required CSV Format Standards

### Column Structure (IMMUTABLE)
```
Category, Subcategory, Field, Confidence, Value_Year_1, Value_Year_2, Value_Year_3, Value_Year_4
```

### Year Mapping Row (IMMUTABLE)
```
Date, Year, Year, , 0.0, 2024, 2023, , 
```

### Success Criteria (IMMUTABLE)
1. **Column Structure**: Must have exact column names
2. **Year Mapping Row**: Must be second row with correct format
3. **Data Completeness**: All financial values must be present
4. **Row Integrity**: No empty rows between data

## 🔒 Enforcement Mechanisms

### 1. Code-Level Protections
- **Immutable Comments**: All critical files have protection headers
- **Version Numbers**: All files include format version numbers
- **Validation**: API responses include format validation
- **Assertions**: Code includes format compliance checks

### 2. API Response Validation
- **Automatic Validation**: All CSV responses are validated
- **Version Tracking**: API responses include `csv_format_version`
- **Error Reporting**: Format violations are reported in responses
- **Fallback Protection**: Invalid formats trigger fallback mechanisms

### 3. Testing Requirements
- **Mandatory Validation**: All tests must use `validate_csv_success.py`
- **Success Criteria**: All tests must pass 4 success criteria
- **Automated Checks**: Pre-commit hooks validate format compliance
- **Continuous Validation**: CI/CD pipeline includes format checks

## 📝 Change Approval Process

### Step 1: Change Request
1. Create a detailed change request document
2. Explain why the change is necessary
3. Provide impact analysis
4. Include rollback plan

### Step 2: Approval Requirements
1. **Technical Review**: Code changes reviewed by team
2. **Documentation Update**: All documentation updated
3. **Testing Validation**: All tests must pass
4. **Version Update**: Version numbers incremented

### Step 3: Implementation
1. **Code Changes**: Implement with protection headers
2. **Documentation**: Update all relevant documentation
3. **Testing**: Run full validation suite
4. **Deployment**: Deploy with validation checks

### Step 4: Verification
1. **Format Validation**: Verify new format passes validation
2. **Backward Compatibility**: Ensure existing functionality works
3. **Documentation Review**: Verify all docs are updated
4. **Team Notification**: Notify team of changes

## 🚫 Prohibited Changes

### Code Changes (REQUIRES APPROVAL)
- Modifying `_transform_data_for_csv()` method
- Changing `transform_to_analysis_ready_format()` function
- Modifying `validate_csv_success.py` validation logic
- Removing or changing protection headers

### Documentation Changes (REQUIRES APPROVAL)
- Modifying `CSV_FORMAT_SPECIFICATION.md`
- Changing success criteria definitions
- Removing cross-references to standards
- Modifying this enforcement document

### Process Changes (REQUIRES APPROVAL)
- Bypassing validation requirements
- Removing approval processes
- Changing testing requirements
- Modifying deployment validation

## 🔍 Monitoring and Compliance

### Automated Monitoring
- **API Response Validation**: All responses validated
- **Format Version Tracking**: Version numbers monitored
- **Error Logging**: Format violations logged
- **Alert System**: Violations trigger alerts

### Manual Monitoring
- **Code Reviews**: All changes reviewed
- **Documentation Reviews**: All docs reviewed
- **Testing Reviews**: All tests reviewed
- **Deployment Reviews**: All deployments reviewed

### Compliance Reporting
- **Weekly Reports**: Format compliance status
- **Monthly Reviews**: Standards enforcement review
- **Quarterly Audits**: Full compliance audit
- **Annual Assessment**: Standards effectiveness review

## 🚨 Emergency Procedures

### Format Violation Response
1. **Immediate Rollback**: Revert to last known good version
2. **Investigation**: Identify cause of violation
3. **Fix Implementation**: Implement approved fix
4. **Validation**: Verify fix resolves issue
5. **Documentation**: Update incident documentation

### Emergency Changes
1. **Emergency Approval**: Get emergency approval
2. **Minimal Changes**: Make only necessary changes
3. **Documentation**: Document emergency nature
4. **Review**: Post-emergency review required
5. **Process Update**: Update process if needed

## 📞 Contact Information

### Standards Committee
- **Technical Lead**: Responsible for code standards
- **Documentation Lead**: Responsible for documentation standards
- **Testing Lead**: Responsible for testing standards
- **Process Lead**: Responsible for process standards

### Escalation Process
1. **Direct Contact**: Contact relevant lead
2. **Team Review**: Team reviews issue
3. **Management Escalation**: Escalate to management if needed
4. **External Review**: External review if necessary

## 📋 Version History

### Version 1.0 (Current)
- Initial standards enforcement document
- Code-level protections implemented
- API validation added
- Testing requirements established

### Future Versions
- All version changes require approval
- Version history must be maintained
- Changes must be documented
- Rollback procedures must be available

---

**⚠️ IMPORTANT: This document is protected and should not be modified without approval. All changes to CSV format standards require following the approval process outlined above.**
