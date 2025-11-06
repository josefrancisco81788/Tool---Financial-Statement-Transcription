# Year Mapping Issue Analysis - CSV Export

## 🔍 Problem Statement

**Issue**: CSV export shows only one year of data per field, when both years should be present.

**Example**:
- **Expected**: 
  - Value_Year_1 (2024): 17,299,358
  - Value_Year_2 (2023): 29,984,998
- **Actual**: 
  - Value_Year_1: 29,984,998 (only one year, appears to be 2023 value)
  - Value_Year_2: (empty)

**Root Cause**: Multiple issues in the data flow from extraction → combination → CSV export.

---

## 📊 Data Flow Analysis

### Phase 1: Extraction (✅ Working)

**Location**: `core/batch_processor.py` lines 1634-1639

**What Happens**:
- Each extracted item is stored as:
  ```python
  {
      'value': 17299358,
      'confidence': 0.95,
      'year': '2024',  # ← Year stored separately
      'page_num': 3
  }
  ```
- Multiple entries can exist for same field name with different years:
  - Entry 1: `{"Cash and Cash Equivalents": {"value": 17299358, "year": "2024", ...}}`
  - Entry 2: `{"Cash and Cash Equivalents": {"value": 29984998, "year": "2023", ...}}`

**Status**: ✅ **Working correctly** - Both years are extracted

---

### Phase 2: Combining Results (❌ PROBLEM)

**Location**: `core/pdf_processor.py` lines 1508-1517 (`_combine_page_results`)

**What Happens**:
```python
# Merge mappings (use highest confidence for duplicates)
for field_name, mapping in page_mappings.items():
    if field_name not in combined_mappings:
        combined_mappings[field_name] = mapping
    else:
        # Keep higher confidence value
        existing_confidence = combined_mappings[field_name].get('confidence', 0)
        new_confidence = mapping.get('confidence', 0)
        if new_confidence > existing_confidence:
            combined_mappings[field_name] = mapping  # ← OVERWRITES!
```

**Problem**: 
- When same field name appears with different years, **one overwrites the other**
- Only the higher confidence entry is kept (or last one processed)
- **Result**: Only one year's data survives in `template_mappings`

**Example**:
- Page 1 extract: `{"Cash and Cash Equivalents": {"value": 17299358, "year": "2024", "confidence": 0.95}}`
- Page 2 extract: `{"Cash and Cash Equivalents": {"value": 29984998, "year": "2023", "confidence": 0.95}}`
- After combining: `{"Cash and Cash Equivalents": {"value": 29984998, "year": "2023", ...}}` (only one!)

**Fix Required**: Merge years instead of overwriting

---

### Phase 3: CSV Export (❌ PROBLEM)

**Location**: `tests/core/csv_exporter.py` lines 712-736 (`export_to_template_csv`)

**What Happens**:
```python
if field_name in template_mappings:
    mapping = template_mappings[field_name]
    filled_row['Value_Year_1'] = mapping.get('value')  # ← Only one value
    
    # Handle multi-year data if available
    if 'Value_Year_1' in mapping:  # ← These keys don't exist!
        filled_row['Value_Year_1'] = mapping.get('Value_Year_1')
    if 'Value_Year_2' in mapping:
        filled_row['Value_Year_2'] = mapping.get('Value_Year_2')
```

**Problems**:
1. **Only uses `mapping.get('value')`** - which is a single value
2. **Doesn't check `mapping.get('year')`** - doesn't use the year field to map to correct column
3. **Doesn't use `years_detected`** - doesn't know which year goes in which column
4. **Expects `Value_Year_1`, `Value_Year_2` keys** - but data structure has `year: "2024"` instead

**Example**:
- Input: `{"Cash and Cash Equivalents": {"value": 29984998, "year": "2023", ...}}`
- CSV export: Puts `29984998` in `Value_Year_1` (wrong - should be Value_Year_2 for 2023)
- **Missing**: The 2024 value (17299358) was lost in Phase 2

**Fix Required**: Map based on `year` field and `years_detected` list

---

## 🔍 Root Cause Summary

### Primary Issue: Data Loss During Combination

**Location**: `core/pdf_processor.py` `_combine_page_results()` method

**Problem**: When multiple pages have the same field with different years:
- Current: Overwrites one with the other (only keeps one)
- Should: Merge years into `Value_Year_1`, `Value_Year_2`, etc.

**Example**:
```python
# Current behavior (WRONG):
combined_mappings['Cash and Cash Equivalents'] = {
    'value': 29984998,  # Only one value!
    'year': '2023',     # Only one year!
    'confidence': 0.95
}

# Expected behavior (CORRECT):
combined_mappings['Cash and Cash Equivalents'] = {
    'value': 17299358,  # Most recent year value
    'confidence': 0.95,
    'Value_Year_1': 17299358,  # 2024 value
    'Value_Year_2': 29984998,  # 2023 value
    'year': '2024'  # Most recent year
}
```

### Secondary Issue: CSV Export Doesn't Use Year Field

**Location**: `tests/core/csv_exporter.py` `export_to_template_csv()` method

**Problem**: CSV exporter doesn't:
1. Check the `year` field in mapping data
2. Use `years_detected` to determine which column to use
3. Map `year: "2024"` → `Value_Year_1`, `year: "2023"` → `Value_Year_2`

**Example**:
```python
# Current (WRONG):
mapping = {'value': 29984998, 'year': '2023', ...}
filled_row['Value_Year_1'] = mapping.get('value')  # Always Value_Year_1!

# Should be (CORRECT):
years_detected = ['2024', '2023']  # Sorted, most recent first
if mapping.get('year') == '2024':
    filled_row['Value_Year_1'] = mapping.get('value')  # 2024 → Value_Year_1
elif mapping.get('year') == '2023':
    filled_row['Value_Year_2'] = mapping.get('value')  # 2023 → Value_Year_2
```

---

## 💡 Solution Analysis

### Solution 1: Fix Combination Logic (Recommended)

**Location**: `core/pdf_processor.py` `_combine_page_results()` method (lines 1508-1517)

**Change Required**:
- Instead of overwriting, **merge years** into `Value_Year_1`, `Value_Year_2`, etc.
- Use `years_detected` to determine which year goes in which column
- Preserve all year values

**Logic**:
```python
for field_name, mapping in page_mappings.items():
    if field_name not in combined_mappings:
        combined_mappings[field_name] = mapping
    else:
        # MERGE instead of overwrite
        existing = combined_mappings[field_name]
        new_year = mapping.get('year')
        existing_year = existing.get('year')
        
        # If different years, merge into Value_Year_X columns
        if new_year != existing_year:
            # Use years_detected to determine column mapping
            years = combined_data.get('years_detected', [])
            # Map years to columns and merge values
            # ...
        else:
            # Same year - keep higher confidence
            if mapping.get('confidence', 0) > existing.get('confidence', 0):
                combined_mappings[field_name] = mapping
```

**Pros**:
- ✅ Fixes data loss at the source
- ✅ Preserves all year data
- ✅ Works with existing CSV exporter (if it's fixed too)

**Cons**:
- ⚠️ More complex logic
- ⚠️ Need to handle year ordering

---

### Solution 2: Fix CSV Export Logic (Also Required)

**Location**: `tests/core/csv_exporter.py` `export_to_template_csv()` method (lines 712-736)

**Change Required**:
- Use `years_detected` to map year values to correct columns
- Check `mapping.get('year')` to determine which column
- Handle multi-year data properly

**Logic**:
```python
# Get years_detected from extracted_data
years_detected = extracted_data.get('years_detected', [])
if not years_detected:
    years_detected = ['2024', '2023']  # Fallback

# Sort years (most recent first)
years_detected = sorted([str(y) for y in years_detected], reverse=True)

if field_name in template_mappings:
    mapping = template_mappings[field_name]
    year = mapping.get('year', '')
    value = mapping.get('value', '')
    
    # Map year to correct column
    if year in years_detected:
        year_index = years_detected.index(year)
        if year_index == 0:
            filled_row['Value_Year_1'] = value
        elif year_index == 1:
            filled_row['Value_Year_2'] = value
        elif year_index == 2:
            filled_row['Value_Year_3'] = value
        elif year_index == 3:
            filled_row['Value_Year_4'] = value
```

**Pros**:
- ✅ Handles year-to-column mapping correctly
- ✅ Works even if data has `year` field instead of `Value_Year_X`

**Cons**:
- ⚠️ Still needs Solution 1 to prevent data loss during combination

---

### Solution 3: Combined Approach (Best)

**Both fixes needed**:
1. **Fix combination logic** to merge years instead of overwriting
2. **Fix CSV export** to map years to correct columns

**Why both**:
- Solution 1: Prevents data loss (preserves all years)
- Solution 2: Ensures correct column mapping (year → Value_Year_X)

---

## 📋 Implementation Plan

### Step 1: Fix Combination Logic

**File**: `core/pdf_processor.py`  
**Method**: `_combine_page_results()`  
**Lines**: 1508-1517

**Change**:
- Detect when same field has different years
- Merge years into `Value_Year_1`, `Value_Year_2`, etc.
- Use `years_detected` to determine column mapping

### Step 2: Fix CSV Export Logic

**File**: `tests/core/csv_exporter.py`  
**Method**: `export_to_template_csv()`  
**Lines**: 712-736

**Change**:
- Use `years_detected` from `extracted_data`
- Map `year` field to correct `Value_Year_X` column
- Handle both formats (with `Value_Year_X` keys and with `year` field)

### Step 3: Test

**Test Case**:
- Document with 2 years (2024, 2023)
- Same field appears on multiple pages with different years
- Verify both years appear in CSV in correct columns

---

## 🔍 Data Structure Examples

### Current Structure (After Combination - WRONG)

```python
template_mappings = {
    'Cash and Cash Equivalents': {
        'value': 29984998,  # Only one value!
        'year': '2023',     # Only one year!
        'confidence': 0.95
    }
}
```

### Expected Structure (After Fix - CORRECT)

```python
template_mappings = {
    'Cash and Cash Equivalents': {
        'value': 17299358,  # Most recent year
        'confidence': 0.95,
        'Value_Year_1': 17299358,  # 2024 value
        'Value_Year_2': 29984998,  # 2023 value
        'year': '2024'  # Most recent year
    }
}
```

**OR** (Alternative format that should also work):

```python
template_mappings = {
    'Cash and Cash Equivalents': {
        'value': 17299358,
        'confidence': 0.95,
        'year': '2024',  # Most recent
        'year_data': {
            '2024': 17299358,
            '2023': 29984998
        }
    }
}
```

---

## 📊 Impact Analysis

### Current Behavior
- **Data Loss**: 50% of multi-year data is lost (only one year kept)
- **Incorrect Mapping**: Year values may be in wrong columns
- **User Impact**: Users see incomplete data

### After Fix
- **Data Preservation**: All years preserved
- **Correct Mapping**: Years in correct columns
- **User Impact**: Users see complete multi-year data

---

## 🎯 Priority

**Priority: HIGH** - This is a data accuracy issue that affects the core functionality.

**Effort**: Medium (2-3 hours)
- Fix combination logic: ~1.5 hours
- Fix CSV export logic: ~1 hour
- Testing: ~30 minutes

---

## ✅ Success Criteria

After fix:
- ✅ CSV shows both years for fields with multi-year data
- ✅ Years mapped to correct columns (2024 → Value_Year_1, 2023 → Value_Year_2)
- ✅ No data loss when same field appears on multiple pages
- ✅ Works with 2, 3, or 4 years of data

---

## 📝 Notes

- The extraction phase is working correctly (both years extracted)
- The problem is in the combination and export phases
- Both phases need fixes for complete solution
- The CSV format is correct (Value_Year_1, Value_Year_2, etc.) - just needs correct data

