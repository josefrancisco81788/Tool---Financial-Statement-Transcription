# Financial Statement Extraction Test Results Comparison

## Test Summary Table

| Test File | Target Fields | Extracted Fields | Coverage | Field Mapping Accuracy | Value Accuracy | Precision | Recall | F1 Score | Processing Time |
|-----------|---------------|------------------|----------|------------------------|----------------|-----------|--------|----------|-----------------|
| **2021 AFS with SEC Stamp** | 26 | 26 | 100.0% | 88.5% | 89.1% | 88.5% | 88.5% | 88.5% | 83.2s |
| **afs-2021-2023** | 17 | 20 | 117.6% | 94.1% | 56.2% | 80.0% | 94.1% | 86.5% | 95.3s |
| **AFS-2022** | 25 | 25 | 100.0% | 92.0% | 95.7% | 92.0% | 92.0% | 92.0% | 50.9s |
| **AFS2024** | 32 | 36 | 112.5% | 87.5% | 83.6% | 77.8% | 87.5% | 82.4% | 68.2s |

## Key Metrics Analysis

### **Field Mapping Accuracy (How well we match target fields)**
- **Best**: afs-2021-2023 (94.1%)
- **Worst**: AFS2024 (87.5%)
- **Average**: 90.5%

### **Value Accuracy (How correct are the extracted values)**
- **Best**: AFS-2022 (95.7%)
- **Worst**: afs-2021-2023 (56.2%)
- **Average**: 81.2%

### **Precision (How many extracted fields are correct)**
- **Best**: AFS-2022 (92.0%)
- **Worst**: AFS2024 (77.8%)
- **Average**: 84.6%

### **Recall (How many target fields were extracted)**
- **Best**: afs-2021-2023 (94.1%)
- **Worst**: AFS2024 (87.5%)
- **Average**: 90.5%

### **F1 Score (Harmonic mean of precision and recall)**
- **Best**: AFS-2022 (92.0%)
- **Worst**: AFS2024 (82.4%)
- **Average**: 87.4%

### **Processing Time**
- **Fastest**: AFS-2022 (50.9s)
- **Slowest**: afs-2021-2023 (95.3s)
- **Average**: 74.4s

## Detailed Field Analysis

### **Common Issues Across All Tests**

1. **Missing "Year" Field**: All tests failed to extract the "Year" field
2. **False Positives**: All tests extracted fields that shouldn't exist in target templates
3. **Multi-year Data**: All tests successfully extracted multi-year data (Value_Year_1, Value_Year_2, etc.)

### **Test-Specific Issues**

#### **2021 AFS with SEC Stamp**
- **Missing Fields**: Current tax liabilities (current), Liabilities, Year
- **False Positives**: Current tax liabilities, Other current non-financial liabilities, Total Current Liabilities
- **Value Issues**: Net Cashflow from Operations has sign mismatch (positive vs negative)

#### **afs-2021-2023**
- **Missing Fields**: Year
- **False Positives**: Amortization Expense, Cash and Cash Equivalents, Depreciation Expense, Other income
- **Value Issues**: Many fields have incorrect year mappings (Value_Year_1 vs Value_Year_2 confusion)

#### **AFS-2022**
- **Missing Fields**: Liabilities, Year
- **False Positives**: Net Cashflow from Operations (per FS), Other current non-financial assets
- **Value Issues**: Profit (loss) before tax values don't match target

#### **AFS2024**
- **Missing Fields**: Current tax liabilities (current), Other non-current financial assets, Trade and other non-current payables, Year
- **False Positives**: 8 extra fields including Current tax liabilities, Investments in subsidiaries, etc.
- **Value Issues**: Several fields have significant value discrepancies

## Business Use Case Assessment

### **Strengths**
- ✅ **High Field Mapping Accuracy**: Average 90.5% - system correctly identifies most target fields
- ✅ **Good Value Accuracy**: Average 81.2% - extracted values are generally correct
- ✅ **Multi-year Support**: All tests successfully extracted multi-year data
- ✅ **Key Financial Data**: All tests extracted Revenue, Cost of Sales, Total Assets, Total Equity, Net Income
- ✅ **Processing Time**: Average 74.4s - acceptable for business use

### **Areas for Improvement**
- ❌ **Year Field Extraction**: 0% success rate across all tests
- ❌ **False Positives**: System extracts fields that shouldn't exist
- ❌ **Value Mapping Issues**: Some fields have incorrect year-to-year mappings
- ❌ **Sign Handling**: Issues with negative values (especially cash flow)

### **Overall Performance Rating**
- **Field Mapping**: 90.5% (Excellent)
- **Value Accuracy**: 81.2% (Good)
- **Precision**: 84.6% (Good)
- **Recall**: 90.5% (Excellent)
- **F1 Score**: 87.4% (Good)

## Recommendations

1. **Fix Year Field Extraction**: Implement specific logic to extract year information
2. **Reduce False Positives**: Improve field filtering to only extract target template fields
3. **Fix Value Mapping**: Ensure correct year-to-year value assignments
4. **Handle Negative Values**: Improve sign handling for cash flow and liability fields
5. **Optimize Processing Time**: Reduce average processing time from 74.4s to under 60s

## Conclusion

The LLM-First Direct Mapping approach shows **excellent performance** with an average F1 score of 87.4%. The system successfully extracts the majority of target fields with high accuracy, making it suitable for business use. The main areas for improvement are reducing false positives and fixing the year field extraction.
