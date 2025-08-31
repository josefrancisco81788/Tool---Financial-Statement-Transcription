# CSV Output Format Specification

## Overview
This document specifies the exact CSV format produced by the Financial Statement Transcription API. This format is designed to be scalable, consistent, and self-documenting for multi-year financial data.

## Format Structure

### Standard CSV Layout
```
Row 1: Header Row (Column Names)
Row 2: Year Mapping Row (Shows which years each Value_Year_X represents)
Row 3+: Data Rows (Financial data for each line item)
```

### Column Structure
```
Category, Subcategory, Field, Confidence, Confidence_Score, Value_Year_1, Value_Year_2, Value_Year_3, Value_Year_4
```

## Detailed Specification

### Header Row (Row 1)
**Purpose**: Defines column names and structure
**Format**: Standard column headers with `Value_Year_X` naming convention

```csv
Category,Subcategory,Field,Confidence,Confidence_Score,Value_Year_1,Value_Year_2,Value_Year_3,Value_Year_4
```

**Column Descriptions**:
- `Category`: Financial statement category (e.g., "Balance Sheet", "Income Statement")
- `Subcategory`: Subcategory within the statement (e.g., "Current Assets", "Revenues")
- `Field`: Specific financial line item (e.g., "Cash And Equivalents", "Net Sales")
- `Confidence`: Confidence percentage (e.g., "95.0%")
- `Confidence_Score`: Numeric confidence score (e.g., "0.95")
- `Value_Year_1`: Financial value for the most recent year
- `Value_Year_2`: Financial value for the second most recent year
- `Value_Year_3`: Financial value for the third most recent year (if present)
- `Value_Year_4`: Financial value for the fourth most recent year (if present)

### Year Mapping Row (Row 2)
**Purpose**: Shows which actual years each `Value_Year_X` column represents
**Format**: Special row with year labels

```csv
Date,Year,Year,,0.0,2024,2023,,
```

**Row Structure**:
- `Date`: Literal "Date" (identifier)
- `Year`: Literal "Year" (identifier)
- `Year`: Literal "Year" (identifier)
- `""`: Empty field
- `0.0`: Literal "0.0" (identifier)
- `2024`: Actual year for Value_Year_1
- `2023`: Actual year for Value_Year_2
- `""`: Empty (no third year)
- `""`: Empty (no fourth year)

### Data Rows (Row 3+)
**Purpose**: Contains actual financial data
**Format**: Financial line items with values for each year

```csv
Balance Sheet,Current Assets,Cash And Equivalents,95.0%,0.95,40506296,14011556,,
```

## Example Output

### Complete Example
```csv
Category,Subcategory,Field,Confidence,Confidence_Score,Value_Year_1,Value_Year_2,Value_Year_3,Value_Year_4
Date,Year,Year,,0.0,2024,2023,,
Balance Sheet,Current Assets,Cash And Equivalents,95.0%,0.95,40506296,14011556,,
Balance Sheet,Current Assets,Accounts Receivable,90.0%,0.9,93102625,102434862,,
Income Statement,Revenues,Net Sales,95.0%,0.95,249788478,292800617,,
```

### Interpretation
- **Value_Year_1 (2024)**: Cash And Equivalents = 40,506,296
- **Value_Year_2 (2023)**: Cash And Equivalents = 14,011,556
- **Value_Year_1 (2024)**: Accounts Receivable = 93,102,625
- **Value_Year_2 (2023)**: Accounts Receivable = 102,434,862

## Design Rationale

### Why Value_Year_X Columns?
1. **Scalability**: Works for any number of years (1-4)
2. **Consistency**: Same column structure regardless of years present
3. **Flexibility**: Can handle different year ranges without changing structure
4. **Standardization**: Compatible with financial analysis tools

### Why Year Mapping Row?
1. **Self-Documenting**: Users immediately know what years the data represents
2. **No External Documentation**: No need to refer to JSON or other sources
3. **Clear Interpretation**: Eliminates confusion about year assignments
4. **Professional Standard**: Common in financial data formats

### Why Not Year-Specific Column Names?
❌ **Don't use**: `Value_2024`, `Value_2023`, `Value_2022`
**Reasons**:
- Not scalable for different year ranges
- Requires code changes for new years
- Inconsistent column structure
- Harder to maintain and process

## Validation Rules

### Required Elements
- [ ] Header row with `Value_Year_X` columns
- [ ] Year mapping row showing actual years
- [ ] At least one data row with financial values
- [ ] Consistent column count across all rows

### Data Validation
- [ ] Year mapping row contains valid year numbers
- [ ] Financial values are numeric or empty
- [ ] Confidence scores are between 0.0 and 1.0
- [ ] Confidence percentages are formatted as "XX.X%"

### Format Validation
- [ ] CSV uses CRLF line endings (`\r\n`)
- [ ] Empty fields are represented as empty strings
- [ ] No trailing commas
- [ ] Proper CSV escaping for special characters

## Success Criteria & Testing Standards

### Required Success Criteria
Every CSV output MUST meet ALL of the following criteria:

#### 1. Column Structure ✅
- **Required columns**: `Category, Subcategory, Field, Confidence, Value_Year_1, Value_Year_2, Value_Year_3, Value_Year_4`
- **No extra columns** (like `Base_Year`, `Year_1`, `Year_2`, `Year_3`)
- **No missing columns** from the required set

#### 2. Row Integrity ✅
- **No empty rows** between data rows in Excel
- **No skipped rows** in the sequence
- **Consistent row structure** throughout the CSV

#### 3. Year Mapping Row ✅
- **Row 2 must be**: `Date, Year, Year, [empty], [empty], 2024, 2023, [empty], [empty]`
- **Category**: "Date"
- **Subcategory**: "Year" 
- **Field**: "Year"
- **Value_Year_1**: "2024" (actual year)
- **Value_Year_2**: "2023" (actual year)
- **Value_Year_3, Value_Year_4**: empty (or actual years if present)

#### 4. Data Completeness ✅
- **ALL financial values must be present** (no empty cells where data should exist)
- **No "None" values** in financial data cells
- **No missing Balance Sheet items** (Cash, Accounts Receivable, etc.)
- **No missing Income Statement items** (Net Sales, Cost of Goods Sold, etc.)
- **No missing Cash Flow items** (Net Income, Depreciation, etc.)

### Failure Conditions
**Any of these = FAIL:**
- Wrong column headers
- Missing year mapping row
- Empty rows between data
- Missing financial values (empty cells where data should be)
- "None" values in financial data
- Wrong year labels in mapping row

### Success Conditions
**ALL of these = PASS:**
- Correct column structure
- Year mapping row present and correct
- No empty rows
- All financial data present and complete

## Common Issues and Solutions

### Issue: Missing Year Mapping Row
**Symptoms**: CSV starts directly with data rows
**Cause**: API bug in CSV generation
**Solution**: Ensure `transform_to_analysis_ready_format` function is working

### Issue: Incorrect Year Data Placement
**Symptoms**: Years appear in wrong columns
**Cause**: Data mapping logic error
**Solution**: Verify year sorting and data assignment logic

### Issue: Empty Value_Year_2 Column
**Symptoms**: Only Value_Year_1 has data
**Cause**: Multi-year extraction not working
**Solution**: Check document processing and year detection

### Issue: Wrong Column Names
**Symptoms**: Columns named `Value_2024`, `Value_2023`
**Cause**: Incorrect CSV generation
**Solution**: Use `Value_Year_X` naming convention

## Testing Guidelines

### Manual Testing
1. **Check Year Mapping Row**: Verify second row shows correct years
2. **Validate Data Placement**: Ensure financial values are in correct columns
3. **Test Scalability**: Try documents with different numbers of years
4. **Verify Format**: Check CSV structure and line endings

### Automated Testing
1. **Parse CSV**: Extract and validate year mapping row
2. **Data Validation**: Verify financial values are numeric
3. **Structure Check**: Ensure consistent column count
4. **Format Validation**: Check CSV syntax and encoding

## Implementation Notes

### API Requirements
- CSV generation must include year mapping row
- Use `Value_Year_X` column naming convention
- Sort years in descending order (most recent first)
- Handle missing years gracefully (empty fields)

### Client Requirements
- Parse year mapping row to understand data structure
- Use year mapping to interpret `Value_Year_X` columns
- Handle variable number of years
- Validate CSV structure before processing

## Version History

### Version 1.0 (Current)
- Standardized `Value_Year_X` column naming
- Added year mapping row
- Scalable format for 1-4 years
- CRLF line endings for Excel compatibility

### Future Enhancements
- Support for more than 4 years
- Additional metadata columns
- Enhanced validation rules
- Standardized error handling
