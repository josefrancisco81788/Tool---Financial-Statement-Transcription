# 📊 API Testing Scoring Framework

This document defines the standardized scoring methodology for evaluating the Financial Statement Transcription API performance.

## 🎯 Primary Metrics

### 1. Field Extraction Rate (Primary Metric)
**Formula**: `Fields Extracted / Fields Expected × 100`

**Definition**:
- **Fields Extracted**: Count of template fields that have actual data (non-empty values) in the API output
- **Fields Expected**: Count of template fields that have actual data (non-empty values) in the expected template

**Why This Matters**: This measures how many fields with actual financial data were successfully extracted, which is the core value proposition of the API.

**Thresholds**:
- **Excellent**: ≥80% extraction rate
- **Good**: 60-79% extraction rate  
- **Acceptable**: 40-59% extraction rate
- **Needs Improvement**: <40% extraction rate

**Command to Calculate**:
```bash
python tests/analyze_field_extraction_accuracy.py
```

### 2. Template Format Accuracy (Secondary Metric)
**Formula**: `Matching Fields / Total Comparable Fields × 100`

**Definition**:
- **Matching Fields**: Count of fields where actual value exactly matches expected value (including empty matches)
- **Total Comparable Fields**: Total number of fields that exist in both actual and expected outputs

**Why This Matters**: This measures template compliance and format accuracy, but includes empty field matches which can be misleading.

**Thresholds**:
- **Excellent**: ≥90% format accuracy
- **Good**: 80-89% format accuracy
- **Acceptable**: 70-79% format accuracy
- **Needs Improvement**: <70% format accuracy

**Command to Calculate**:
```bash
python tests/compare_results_vs_expected.py
```

## 📋 Test File Benchmarks

### Light Test Files (Primary Testing)

| File | Expected Fields | Target Extraction Rate | Current Performance |
|------|-----------------|----------------------|-------------------|
| **AFS2024** | 32 | ≥80% (Excellent) | 65.6% (Good) |
| **AFS-2022** | 25 | ≥80% (Excellent) | 36.0% (Needs Improvement) |
| **2021 AFS SEC** | 26 | ≥80% (Excellent) | 34.6% (Needs Improvement) |
| **afs-2021-2023** | 17 | ≥80% (Excellent) | 11.8% (Needs Improvement) |

### Overall Performance Targets
- **Minimum Acceptable**: 60% overall extraction rate
- **Production Ready**: 80% overall extraction rate
- **Current Performance**: 41.0% overall extraction rate

## 🔍 Scoring Methodology

### Step 1: Run Field Extraction Analysis
```bash
python tests/analyze_field_extraction_accuracy.py
```

**Output**: Per-file extraction rates and overall performance

### Step 2: Run Template Format Analysis
```bash
python tests/compare_results_vs_expected.py
```

**Output**: Template compliance and format accuracy

### Step 3: Calculate Overall Score
**Formula**: `(Extraction Rate × 0.7) + (Format Accuracy × 0.3)`

**Weighting**:
- **70%**: Field Extraction Rate (primary value)
- **30%**: Template Format Accuracy (secondary value)

### Step 4: Determine Status
- **Excellent**: Overall Score ≥85%
- **Good**: Overall Score 70-84%
- **Acceptable**: Overall Score 55-69%
- **Needs Improvement**: Overall Score <55%

## 📊 Current Performance (January 2025)

### Per-File Scores
| File | Extraction Rate | Format Accuracy | Overall Score | Status |
|------|-----------------|-----------------|---------------|--------|
| AFS2024 | 65.6% | 84.6% | 71.1% | Good |
| AFS-2022 | 36.0% | 72.5% | 48.2% | Needs Improvement |
| 2021 AFS SEC | 34.6% | 79.1% | 49.4% | Needs Improvement |
| afs-2021-2023 | 11.8% | 83.5% | 35.4% | Needs Improvement |

### Overall Performance
- **Overall Extraction Rate**: 41.0%
- **Overall Format Accuracy**: 79.9%
- **Overall Score**: 52.1%
- **Status**: **Needs Improvement**

## 🎯 Production Readiness Criteria

### Minimum Requirements
- **Field Extraction Rate**: ≥60%
- **Template Format Accuracy**: ≥70%
- **Processing Success Rate**: ≥95%
- **Overall Score**: ≥70%

### Current Status
- **Field Extraction Rate**: 41.0% ❌ (Below 60% threshold)
- **Template Format Accuracy**: 79.9% ✅ (Above 70% threshold)
- **Processing Success Rate**: 100% ✅ (Above 95% threshold)
- **Overall Score**: 52.1% ❌ (Below 70% threshold)

**Verdict**: ⚠️ **NOT PRODUCTION READY** - Field extraction rate needs significant improvement

## 🔧 Improvement Targets

### Short-term Goals (Next Release)
- **Field Extraction Rate**: 60%+ (from current 41.0%)
- **Overall Score**: 70%+ (from current 52.1%)

### Long-term Goals (Production Ready)
- **Field Extraction Rate**: 80%+ (Excellent level)
- **Overall Score**: 85%+ (Excellent level)

## 📝 Scoring Checklist

### For Each Test Run:
- [ ] Run `python tests/analyze_field_extraction_accuracy.py`
- [ ] Run `python tests/compare_results_vs_expected.py`
- [ ] Calculate overall score using weighted formula
- [ ] Compare against thresholds
- [ ] Document results and status
- [ ] Identify improvement areas

### For Production Deployment:
- [ ] All files achieve ≥60% extraction rate
- [ ] Overall extraction rate ≥60%
- [ ] Template format accuracy ≥70%
- [ ] Processing success rate ≥95%
- [ ] Overall score ≥70%

---

*This scoring framework ensures objective, measurable assessment of API performance with clear production readiness criteria.*
