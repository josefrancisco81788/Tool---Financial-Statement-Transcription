# 🧪 Unified Testing Pipeline Plan

## 📋 Executive Summary

After reviewing the current testing infrastructure, I've identified that the project has a robust foundation but suffers from **ad-hoc test creation** and **lack of unified provider comparison**. The current approach requires writing new test scripts for each scenario, which is error-prone and inefficient.

This document outlines a comprehensive plan to create a **unified, configuration-driven testing pipeline** that eliminates the need for custom test scripts while providing comprehensive provider comparison and performance tracking capabilities.

## 🔍 Current State Analysis

### ✅ **Strengths**
- **Comprehensive Test Structure**: Well-organized test categories (unit, integration, performance, validation)
- **Rich Test Data**: Light files, origin files, and templates available
- **Scoring Framework**: Detailed metrics for field extraction accuracy and template compliance
- **CSV Export Integration**: API returns CSV data directly
- **Multiple Test Scripts**: `test_api_enhanced.py`, `test_light_files_direct.py`, etc.

### ❌ **Pain Points**
- **Ad-hoc Test Creation**: New test scripts created for each scenario (e.g., `test_single_claude.py`, `test_2025_api.py`)
- **No Provider Comparison**: No unified way to compare OpenAI vs Claude performance
- **Manual Environment Switching**: Must manually set `AI_PROVIDER` environment variable
- **Scattered Results**: Test results spread across multiple files and formats
- **No Baseline Comparison**: No automated way to compare against previous results
- **Repetitive Code**: Similar test logic duplicated across multiple scripts

## 🎯 Unified Testing Pipeline Design

### **Core Concept: Configuration-Driven Testing**

Instead of writing new test scripts, create a **single, configurable test runner** that can:
1. **Test any provider** (OpenAI, Claude, or both)
2. **Test any document set** (light, origin, or custom)
3. **Generate comprehensive reports** with provider comparisons
4. **Maintain baselines** and track performance over time
5. **Export results** in multiple formats (JSON, CSV, HTML)

## 🏗️ Proposed Architecture

### **1. Unified Test Runner** (`tests/unified_test_runner.py`)

```python
class UnifiedTestRunner:
    """Single test runner for all testing scenarios"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.results_aggregator = ResultsAggregator()
        self.provider_comparator = ProviderComparator()
    
    def run_provider_comparison(self, providers: List[str], documents: List[str]):
        """Compare multiple providers on same documents"""
        
    def run_baseline_establishment(self, provider: str, documents: List[str]):
        """Establish performance baseline for a provider"""
        
    def run_regression_testing(self, provider: str, documents: List[str]):
        """Compare current results against baseline"""
        
    def run_accuracy_validation(self, documents: List[str]):
        """Validate accuracy against templates"""
```

### **2. Test Configuration System** (`tests/config/test_config.py`)

```python
@dataclass
class TestConfig:
    """Configuration for test runs"""
    
    # Provider settings
    providers: List[str] = field(default_factory=lambda: ["openai", "anthropic"])
    provider_configs: Dict[str, Dict] = field(default_factory=dict)
    
    # Document settings
    document_sets: List[str] = field(default_factory=lambda: ["light", "origin"])
    custom_documents: List[str] = field(default_factory=list)
    
    # Test settings
    timeout_seconds: int = 300
    parallel_workers: int = 1
    retry_attempts: int = 3
    
    # Output settings
    output_formats: List[str] = field(default_factory=lambda: ["json", "csv", "html"])
    baseline_comparison: bool = True
    provider_comparison: bool = True
    
    # Validation settings
    accuracy_threshold: float = 0.6
    performance_threshold: float = 120.0  # seconds
```

### **3. Provider Management System** (`tests/providers/provider_manager.py`)

```python
class ProviderManager:
    """Manages different AI providers for testing"""
    
    def __init__(self):
        self.providers = {
            "openai": OpenAITestProvider(),
            "anthropic": AnthropicTestProvider()
        }
    
    def test_provider(self, provider_name: str, document: str) -> TestResult:
        """Test a specific provider with a document"""
        
    def compare_providers(self, providers: List[str], document: str) -> ComparisonResult:
        """Compare multiple providers on same document"""
```

### **4. Results Aggregation System** (`tests/results/results_aggregator.py`)

```python
class ResultsAggregator:
    """Aggregates and analyzes test results"""
    
    def aggregate_results(self, results: List[TestResult]) -> AggregatedResults:
        """Aggregate multiple test results"""
        
    def compare_with_baseline(self, current: TestResult, baseline: TestResult) -> ComparisonReport:
        """Compare current results with baseline"""
        
    def generate_provider_comparison(self, results: Dict[str, TestResult]) -> ProviderComparisonReport:
        """Generate provider comparison report"""
```

## 🚀 Implementation Plan

### **Phase 1: Core Infrastructure** (Week 1)

#### **1.1 Create Unified Test Runner**
- [ ] Create `tests/unified_test_runner.py` with basic structure
- [ ] Implement provider switching logic
- [ ] Add timeout and error handling
- [ ] Create configuration system

#### **1.2 Provider Management**
- [ ] Create `tests/providers/` directory
- [ ] Implement `OpenAITestProvider` class
- [ ] Implement `AnthropicTestProvider` class
- [ ] Add provider validation and health checks

#### **1.3 Results System**
- [ ] Create `tests/results/results_aggregator.py`
- [ ] Implement result storage and retrieval
- [ ] Add baseline management
- [ ] Create comparison logic

### **Phase 2: Advanced Features** (Week 2)

#### **2.1 Configuration System**
- [ ] Create YAML/JSON configuration files
- [ ] Add command-line interface
- [ ] Implement configuration validation
- [ ] Add preset configurations (quick, comprehensive, regression)

#### **2.2 Reporting System**
- [ ] Create HTML report generator
- [ ] Add CSV export with provider comparisons
- [ ] Implement performance charts and graphs
- [ ] Add email/Slack notifications for failures

#### **2.3 Baseline Management**
- [ ] Implement baseline storage and retrieval
- [ ] Add automatic baseline updates
- [ ] Create regression detection
- [ ] Add performance trend analysis

### **Phase 3: Integration & Optimization** (Week 3)

#### **3.1 CI/CD Integration**
- [ ] Add GitHub Actions workflow
- [ ] Implement automated testing on PRs
- [ ] Add performance regression detection
- [ ] Create deployment gates

#### **3.2 Advanced Analytics**
- [ ] Add statistical analysis of results
- [ ] Implement A/B testing framework
- [ ] Create performance prediction models
- [ ] Add cost analysis (API usage)

## 📊 Usage Examples

### **1. Quick Provider Comparison**
```bash
# Compare OpenAI vs Claude on light files
python tests/unified_test_runner.py --providers openai,anthropic --documents light --compare

# Output: Provider comparison report with accuracy, speed, and cost metrics
```

### **2. Establish Claude Baseline**
```bash
# Establish baseline for Claude provider
python tests/unified_test_runner.py --provider anthropic --documents light --baseline

# Output: Baseline results saved for future comparison
```

### **3. Regression Testing**
```bash
# Test Claude against established baseline
python tests/unified_test_runner.py --provider anthropic --documents light --regression

# Output: Comparison with baseline, highlighting any regressions
```

### **4. Comprehensive Testing**
```bash
# Full test suite with all providers and documents
python tests/unified_test_runner.py --config comprehensive

# Output: Complete test report with all metrics and comparisons
```

### **5. Custom Test Configuration**
```yaml
# tests/config/custom_test.yaml
providers: ["anthropic"]
documents: ["AFS2024 - statement extracted.pdf"]
timeout_seconds: 600
output_formats: ["json", "html"]
baseline_comparison: true
accuracy_threshold: 0.8
```

```bash
python tests/unified_test_runner.py --config tests/config/custom_test.yaml
```

## 📈 Expected Benefits

### **1. Eliminate Ad-hoc Testing**
- ✅ **Single test runner** for all scenarios
- ✅ **Configuration-driven** testing
- ✅ **No more custom scripts** for each test case
- ✅ **Consistent test execution** across all scenarios

### **2. Unified Provider Comparison**
- ✅ **Side-by-side comparison** of OpenAI vs Claude
- ✅ **Performance metrics** (speed, accuracy, cost)
- ✅ **Statistical significance** testing
- ✅ **Automated recommendations** for best provider

### **3. Comprehensive Reporting**
- ✅ **Unified results format** across all tests
- ✅ **Historical tracking** of performance
- ✅ **Regression detection** and alerts
- ✅ **Executive dashboards** for stakeholders

### **4. Improved Reliability**
- ✅ **Standardized error handling** across all tests
- ✅ **Timeout protection** for all operations
- ✅ **Retry logic** for transient failures
- ✅ **Health checks** before test execution

### **5. Better Maintainability**
- ✅ **Single codebase** for all testing logic
- ✅ **Modular design** for easy extension
- ✅ **Clear separation** of concerns
- ✅ **Comprehensive documentation** and examples

## 🎯 Success Metrics

### **Immediate Goals (Week 1)**
- [ ] Single command can test any provider on any document set
- [ ] Provider comparison reports generated automatically
- [ ] Baseline establishment and comparison working
- [ ] All existing test scenarios covered by unified runner

### **Medium-term Goals (Week 2-3)**
- [ ] HTML reports with charts and visualizations
- [ ] Automated regression detection
- [ ] CI/CD integration working
- [ ] Performance trend analysis

### **Long-term Goals (Month 2+)**
- [ ] A/B testing framework for provider selection
- [ ] Cost optimization recommendations
- [ ] Predictive performance modeling
- [ ] Integration with monitoring and alerting systems

## 🔧 Migration Strategy

### **Phase 1: Parallel Implementation**
- Keep existing test scripts working
- Implement unified runner alongside
- Gradually migrate test scenarios
- Validate results match existing tests

### **Phase 2: Gradual Replacement**
- Mark existing scripts as deprecated
- Update documentation to use unified runner
- Train team on new testing approach
- Remove old scripts after validation

### **Phase 3: Full Migration**
- All testing through unified runner
- Enhanced features and reporting
- CI/CD integration
- Performance optimization

## 📝 Detailed Implementation Specifications

### **Directory Structure**
```
tests/
├── unified_test_runner.py          # Main test runner
├── config/
│   ├── test_config.py             # Configuration classes
│   ├── presets/
│   │   ├── quick.yaml             # Quick test preset
│   │   ├── comprehensive.yaml     # Full test preset
│   │   └── regression.yaml        # Regression test preset
│   └── custom/                    # Custom configurations
├── providers/
│   ├── __init__.py
│   ├── provider_manager.py        # Provider management
│   ├── openai_provider.py         # OpenAI test provider
│   ├── anthropic_provider.py      # Anthropic test provider
│   └── base_provider.py           # Base provider class
├── results/
│   ├── results_aggregator.py      # Result aggregation
│   ├── baseline_manager.py        # Baseline management
│   ├── comparison_engine.py       # Comparison logic
│   └── report_generator.py        # Report generation
├── utils/
│   ├── timeout_handler.py         # Timeout management
│   ├── error_handler.py           # Error handling
│   └── validation.py              # Input validation
└── reports/
    ├── html/                      # HTML reports
    ├── csv/                       # CSV exports
    └── json/                      # JSON results
```

### **Core Classes and Methods**

#### **UnifiedTestRunner**
```python
class UnifiedTestRunner:
    def __init__(self, config: TestConfig):
        self.config = config
        self.provider_manager = ProviderManager()
        self.results_aggregator = ResultsAggregator()
        self.baseline_manager = BaselineManager()
    
    def run_provider_comparison(self, providers: List[str], documents: List[str]) -> ComparisonReport:
        """Compare multiple providers on same documents"""
        
    def run_baseline_establishment(self, provider: str, documents: List[str]) -> BaselineResult:
        """Establish performance baseline for a provider"""
        
    def run_regression_testing(self, provider: str, documents: List[str]) -> RegressionReport:
        """Compare current results against baseline"""
        
    def run_accuracy_validation(self, documents: List[str]) -> ValidationReport:
        """Validate accuracy against templates"""
        
    def run_comprehensive_test(self) -> ComprehensiveReport:
        """Run all test types based on configuration"""
```

#### **ProviderManager**
```python
class ProviderManager:
    def __init__(self):
        self.providers = {
            "openai": OpenAITestProvider(),
            "anthropic": AnthropicTestProvider()
        }
    
    def test_provider(self, provider_name: str, document: str) -> TestResult:
        """Test a specific provider with a document"""
        
    def compare_providers(self, providers: List[str], document: str) -> ComparisonResult:
        """Compare multiple providers on same document"""
        
    def validate_provider(self, provider_name: str) -> bool:
        """Validate provider configuration and health"""
```

#### **ResultsAggregator**
```python
class ResultsAggregator:
    def aggregate_results(self, results: List[TestResult]) -> AggregatedResults:
        """Aggregate multiple test results"""
        
    def compare_with_baseline(self, current: TestResult, baseline: TestResult) -> ComparisonReport:
        """Compare current results with baseline"""
        
    def generate_provider_comparison(self, results: Dict[str, TestResult]) -> ProviderComparisonReport:
        """Generate provider comparison report"""
        
    def calculate_statistics(self, results: List[TestResult]) -> StatisticsReport:
        """Calculate statistical metrics"""
```

### **Configuration Examples**

#### **Quick Test Configuration**
```yaml
# tests/config/presets/quick.yaml
name: "Quick Test"
description: "Fast test for development and CI/CD"

providers: ["anthropic"]
document_sets: ["light"]
timeout_seconds: 180
parallel_workers: 1
retry_attempts: 2

output_formats: ["json", "csv"]
baseline_comparison: false
provider_comparison: false

accuracy_threshold: 0.5
performance_threshold: 180.0
```

#### **Comprehensive Test Configuration**
```yaml
# tests/config/presets/comprehensive.yaml
name: "Comprehensive Test"
description: "Full test suite for release validation"

providers: ["openai", "anthropic"]
document_sets: ["light", "origin"]
timeout_seconds: 600
parallel_workers: 2
retry_attempts: 3

output_formats: ["json", "csv", "html"]
baseline_comparison: true
provider_comparison: true

accuracy_threshold: 0.6
performance_threshold: 300.0
```

#### **Regression Test Configuration**
```yaml
# tests/config/presets/regression.yaml
name: "Regression Test"
description: "Compare against established baselines"

providers: ["anthropic"]
document_sets: ["light"]
timeout_seconds: 300
parallel_workers: 1
retry_attempts: 3

output_formats: ["json", "html"]
baseline_comparison: true
provider_comparison: false

accuracy_threshold: 0.6
performance_threshold: 120.0
regression_threshold: 0.1  # 10% performance degradation threshold
```

### **Command Line Interface**

#### **Basic Usage**
```bash
# Run with default configuration
python tests/unified_test_runner.py

# Run with specific preset
python tests/unified_test_runner.py --config quick

# Run with custom configuration file
python tests/unified_test_runner.py --config tests/config/custom_test.yaml
```

#### **Provider-Specific Commands**
```bash
# Test single provider
python tests/unified_test_runner.py --provider anthropic --documents light

# Compare multiple providers
python tests/unified_test_runner.py --providers openai,anthropic --documents light --compare

# Establish baseline
python tests/unified_test_runner.py --provider anthropic --documents light --baseline

# Regression testing
python tests/unified_test_runner.py --provider anthropic --documents light --regression
```

#### **Advanced Options**
```bash
# Custom timeout and parallel workers
python tests/unified_test_runner.py --timeout 600 --workers 2

# Specific output formats
python tests/unified_test_runner.py --output json,csv,html

# Custom accuracy threshold
python tests/unified_test_runner.py --accuracy-threshold 0.8

# Verbose output
python tests/unified_test_runner.py --verbose

# Dry run (show what would be tested)
python tests/unified_test_runner.py --dry-run
```

### **Report Formats**

#### **JSON Report Structure**
```json
{
  "test_run": {
    "timestamp": "2025-01-15T10:30:00Z",
    "config": "comprehensive",
    "duration_seconds": 1250.5
  },
  "providers": {
    "openai": {
      "success_rate": 1.0,
      "average_processing_time": 45.2,
      "accuracy_score": 0.65,
      "cost_estimate": 0.12
    },
    "anthropic": {
      "success_rate": 1.0,
      "average_processing_time": 38.7,
      "accuracy_score": 0.72,
      "cost_estimate": 0.08
    }
  },
  "comparison": {
    "winner": "anthropic",
    "performance_difference": 0.07,
    "cost_difference": -0.04,
    "statistical_significance": true
  },
  "baseline_comparison": {
    "regression_detected": false,
    "performance_change": 0.02,
    "accuracy_change": 0.01
  }
}
```

#### **CSV Report Structure**
```csv
Provider,Document,Success,Processing_Time,Accuracy,Cost,Baseline_Comparison,Regression_Detected
openai,AFS2024,True,45.2,0.65,0.12,0.02,False
anthropic,AFS2024,True,38.7,0.72,0.08,0.01,False
```

#### **HTML Report Features**
- Interactive charts and graphs
- Provider comparison tables
- Performance trend analysis
- Regression detection alerts
- Executive summary dashboard
- Detailed drill-down capabilities

## 🚨 Risk Assessment

### **Technical Risks**
- **Complexity**: Unified system may become overly complex
- **Performance**: Single runner may be slower than specialized scripts
- **Compatibility**: May not support all existing test scenarios initially

### **Mitigation Strategies**
- **Phased Implementation**: Start simple, add complexity gradually
- **Parallel Development**: Keep existing scripts during transition
- **Comprehensive Testing**: Validate all scenarios before migration
- **Fallback Options**: Maintain ability to use old scripts if needed

### **Operational Risks**
- **Learning Curve**: Team needs to learn new testing approach
- **Dependency**: Single point of failure for all testing
- **Maintenance**: More complex system requires more maintenance

### **Mitigation Strategies**
- **Training**: Comprehensive documentation and training materials
- **Redundancy**: Keep critical test scenarios in multiple formats
- **Monitoring**: Implement health checks and alerting
- **Documentation**: Maintain detailed operational procedures

## 🚨 **IMPLEMENTATION ISSUES & LESSONS LEARNED**

### **📊 Post-Implementation Analysis (January 2025)**

After implementing the unified testing pipeline, several critical issues emerged that disrupted core functionality:

#### **❌ Major Issues Identified**

1. **Architecture Disruption**
   - **PyMuPDF Usage**: Incorrectly implemented PDF→Image conversion for scanned documents
   - **Unnecessary Complexity**: Added conversion layers that weren't needed for 30-90MB scanned PDFs
   - **Performance Degradation**: Slower processing due to conversion overhead
   - **Quality Loss**: Additional conversion steps reduced document quality

2. **Import Path Conflicts**
   - **Module Resolution**: `unified_test_runner.py` had incorrect import paths
   - **Dependency Conflicts**: New testing infrastructure conflicted with existing API
   - **Broken Imports**: Required manual fixes to restore functionality

3. **Processing Flow Disruption**
   - **Direct LLM Processing Lost**: Original PDF→LLM flow replaced with PDF→PyMuPDF→Images→LLM
   - **File Size Issues**: No proper handling for large scanned documents (30-90MB)
   - **Quality Preservation**: Lost original document quality through unnecessary conversions

#### **🔍 Root Cause Analysis**

**Why the Unified Pipeline Broke Functionality:**

1. **Over-Engineering**: Added unnecessary complexity to a working system
2. **Architecture Mismatch**: PyMuPDF approach wrong for scanned documents
3. **Import Path Issues**: New testing infrastructure conflicted with existing code
4. **Processing Flow Disruption**: Replaced working direct processing with complex conversion

**What Should Have Been Done:**

1. **Incremental Improvement**: Enhance existing working system
2. **Preserve Core Functionality**: Keep working extraction flow
3. **Add Testing Layer**: Without disrupting existing functionality
4. **Maintain Performance**: Don't add unnecessary conversion steps

#### **✅ What Actually Works**

**Unified Testing Pipeline (Working):**
- ✅ Provider comparison functionality
- ✅ CSV export and reporting
- ✅ Baseline establishment and tracking
- ✅ Configuration-driven testing
- ✅ Results aggregation and analysis

**Core Extraction (Broken):**
- ❌ PyMuPDF usage for scanned documents
- ❌ Unnecessary conversion overhead
- ❌ Quality loss through conversion
- ❌ Poor handling of large files (30-90MB)

#### **🔧 Resolution Strategy**

**Keep What Works:**
- Unified testing pipeline for provider comparison
- CSV export and reporting functionality
- Configuration-driven testing approach

**Fix What's Broken:**
- Remove PyMuPDF dependency for scanned documents
- Restore direct LLM processing for large files
- Implement proper chunking for 30-90MB documents
- Preserve original document quality

---

## 🎯 **MVP: IDEAL BARE MINIMUM FUNCTIONALITY**

### **📋 Core Requirements for Production Readiness**

Based on the implementation issues and lessons learned, here's the ideal bare minimum functionality:

#### **1. Core API Functionality**
- ✅ **Server Startup**: FastAPI server starts without errors
- ✅ **Health Check**: `/health` endpoint returns proper status
- ✅ **File Upload**: `/extract` endpoint accepts PDF/image uploads
- ✅ **Error Handling**: Proper error responses and logging
- ✅ **Provider Switching**: OpenAI/Anthropic configuration working

#### **2. Document Processing**
- ✅ **Direct LLM Processing**: PDF → LLM Vision API (no conversion)
- ✅ **Large File Support**: Handle 30-90MB scanned documents
- ✅ **Quality Preservation**: Maintain original document quality
- ✅ **Multi-year Support**: Process 2-year and 3-year documents
- ✅ **Scanned Document Support**: No OCR dependency

#### **3. Data Extraction**
- ✅ **Financial Data Extraction**: Extract line items, values, years
- ✅ **Template Compliance**: Output matches FS_Input_Template_Fields.csv
- ✅ **Confidence Scoring**: Provide confidence levels for extracted data
- ✅ **Multi-year Data**: Handle overlapping years and data consolidation
- ✅ **Field Mapping**: Proper categorization of financial data

#### **4. CSV Export**
- ✅ **Template CSV**: Generate template-compliant CSV output
- ✅ **Field Mapping**: Map extracted data to standard fields
- ✅ **Validation**: Template compliance checking
- ✅ **Multiple Formats**: Summary, detailed, and comparison CSV formats

#### **5. Provider Comparison**
- ✅ **Provider Testing**: Test OpenAI vs Anthropic performance
- ✅ **Baseline Management**: Establish and compare baselines
- ✅ **Results Export**: CSV reports with provider comparisons
- ✅ **Performance Tracking**: Speed, accuracy, and cost metrics

### **🚫 What to Avoid (Lessons Learned)**

#### **❌ Anti-Patterns**
- **PyMuPDF for Scanned Documents**: Unnecessary conversion overhead
- **Complex Conversion Chains**: PDF→Image→Base64→LLM
- **Over-Engineering**: Adding complexity to working systems
- **Breaking Existing Functionality**: Disrupting working extraction flow
- **Quality Loss**: Unnecessary conversion steps

#### **✅ Best Practices**
- **Direct Processing**: PDF → LLM Vision API for scanned documents
- **Incremental Enhancement**: Build on working systems
- **Preserve Quality**: Maintain original document quality
- **Performance First**: Optimize for speed and efficiency
- **Test-Driven Development**: Validate changes don't break existing functionality

### **🎯 Success Criteria**

**Minimum Viable Product Must Achieve:**
1. **Server Stability**: API server starts and runs without errors
2. **Document Processing**: Handle 30-90MB scanned PDFs successfully
3. **Data Extraction**: Extract financial data with ≥70% accuracy
4. **CSV Generation**: Produce template-compliant CSV output
5. **Provider Comparison**: Compare OpenAI vs Anthropic performance
6. **End-to-End Flow**: Complete pipeline from upload to CSV export

**Quality Thresholds:**
- **Rightmost Column Completeness**: ≥70% (Current: 14-28%)
- **2020 Data Extraction**: ≥70% of expected values (Current: 0%)
- **Processing Time**: <5 minutes for 3-year documents
- **Success Rate**: ≥90% for 2-year documents
- **Template Compliance**: 100% field mapping accuracy

---

## 📞 Next Steps

1. **Restore Core Functionality** - Fix PyMuPDF usage and restore direct LLM processing
2. **Implement MVP Requirements** - Focus on bare minimum functionality
3. **Validate End-to-End Flow** - Test complete pipeline from upload to CSV
4. **Performance Optimization** - Ensure 30-90MB file handling works efficiently
5. **Provider Comparison** - Validate OpenAI vs Anthropic testing works
6. **Documentation Update** - Update all documentation to reflect current state
7. **Monitor and Iterate** - Continuous improvement based on usage

---

This unified testing pipeline will transform the testing process from **error-prone ad-hoc script creation** to **reliable, configuration-driven testing** with comprehensive provider comparison and performance tracking. The system will be maintainable, scalable, and provide valuable insights for decision-making.

**Critical Lesson**: The unified pipeline should enhance existing functionality, not replace it. The core extraction system was working and should have been preserved while adding the testing infrastructure as a complementary layer.
