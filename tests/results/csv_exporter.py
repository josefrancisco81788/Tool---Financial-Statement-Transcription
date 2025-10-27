"""
Advanced CSV export system for unified testing pipeline
"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import TestResult from providers
import sys
from pathlib import Path as PathLib
sys.path.insert(0, str(PathLib(__file__).parent.parent))
from providers.base_provider import TestResult

class CSVExporter:
    """Exports test results to detailed CSV format"""
    
    def __init__(self, output_dir: str = "tests/reports/csv"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_test_results(self, results: List[TestResult], filename: Optional[str] = None) -> str:
        """Export test results to detailed CSV"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"detailed_test_results_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            header = self._get_csv_header()
            writer.writerow(header)
            
            # Write data rows
            for result in results:
                row = self._result_to_csv_row(result)
                writer.writerow(row)
        
        return str(filepath)
    
    def _get_csv_header(self) -> List[str]:
        """Get CSV header with all field information"""
        return [
            # Basic info
            "Provider",
            "Document",
            "Success",
            "Error",
            "Timestamp",
            
            # Performance metrics
            "Processing_Time_Seconds",
            "Extraction_Rate",
            "Format_Accuracy",
            "Overall_Score",
            "API_Calls_Made",
            "Pages_Processed",
            
            # Field-level data
            "Total_Fields_Extracted",
            "Total_Template_Fields",
            "Missing_Fields_Count",
            "Field_Accuracy_Average",
            
            # Individual field data (will be expanded)
            "Extracted_Fields_JSON",
            "Template_Fields_JSON",
            "Missing_Fields_JSON",
            "Field_Accuracy_JSON",
            "Confidence_Scores_JSON"
        ]
    
    def _result_to_csv_row(self, result: TestResult) -> List[str]:
        """Convert TestResult to CSV row"""
        # Calculate average field accuracy
        avg_field_accuracy = 0.0
        if result.field_accuracy:
            avg_field_accuracy = sum(result.field_accuracy.values()) / len(result.field_accuracy)
        
        return [
            # Basic info
            result.provider,
            result.document,
            str(result.success),
            result.error or "",
            result.timestamp,
            
            # Performance metrics
            str(result.processing_time),
            str(result.extraction_rate),
            str(result.format_accuracy),
            str(result.overall_score),
            str(result.api_calls_made),
            str(result.pages_processed),
            
            # Field-level data
            str(len(result.extracted_fields)),
            str(len(result.template_fields)),
            str(len(result.missing_fields)),
            str(avg_field_accuracy),
            
            # JSON data for detailed analysis
            json.dumps(result.extracted_fields, ensure_ascii=False),
            json.dumps(result.template_fields, ensure_ascii=False),
            json.dumps(result.missing_fields, ensure_ascii=False),
            json.dumps(result.field_accuracy, ensure_ascii=False),
            json.dumps(result.confidence_scores, ensure_ascii=False)
        ]
    
    def export_field_level_analysis(self, results: List[TestResult], filename: Optional[str] = None) -> str:
        """Export detailed field-level analysis CSV"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"field_level_analysis_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header for field-level analysis
            header = [
                "Provider",
                "Document",
                "Field_Name",
                "Field_Value",
                "Field_Accuracy",
                "Confidence_Score",
                "Is_Template_Field",
                "Is_Missing",
                "Extraction_Method"
            ]
            writer.writerow(header)
            
            # Write field-level data
            for result in results:
                self._write_field_level_rows(writer, result)
        
        return str(filepath)
    
    def _write_field_level_rows(self, writer: csv.writer, result: TestResult):
        """Write field-level rows for a single test result"""
        all_fields = set(result.extracted_fields.keys()) | set(result.template_fields)
        
        for field_name in all_fields:
            field_value = result.extracted_fields.get(field_name, "")
            field_accuracy = result.field_accuracy.get(field_name, 0.0)
            confidence_score = result.confidence_scores.get(field_name, 0.0)
            is_template_field = field_name in result.template_fields
            is_missing = field_name in result.missing_fields
            
            writer.writerow([
                result.provider,
                result.document,
                field_name,
                str(field_value),
                str(field_accuracy),
                str(confidence_score),
                str(is_template_field),
                str(is_missing),
                "ai_extraction"  # Could be enhanced to track extraction method
            ])
    
    def export_provider_comparison(self, provider_results: Dict[str, List[TestResult]], filename: Optional[str] = None) -> str:
        """Export provider comparison CSV"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"provider_comparison_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            header = [
                "Provider",
                "Document",
                "Success_Rate",
                "Avg_Processing_Time",
                "Avg_Extraction_Rate",
                "Avg_Format_Accuracy",
                "Avg_Overall_Score",
                "Total_Fields_Extracted",
                "Fields_Accuracy_Above_80%",
                "Production_Ready"
            ]
            writer.writerow(header)
            
            # Write comparison data
            for provider, results in provider_results.items():
                if results:
                    avg_metrics = self._calculate_average_metrics(results)
                    writer.writerow([
                        provider,
                        "ALL_DOCUMENTS",  # Or could be per-document
                        str(avg_metrics["success_rate"]),
                        str(avg_metrics["avg_processing_time"]),
                        str(avg_metrics["avg_extraction_rate"]),
                        str(avg_metrics["avg_format_accuracy"]),
                        str(avg_metrics["avg_overall_score"]),
                        str(avg_metrics["total_fields_extracted"]),
                        str(avg_metrics["fields_accuracy_above_80"]),
                        str(avg_metrics["production_ready"])
                    ])
        
        return str(filepath)
    
    def _calculate_average_metrics(self, results: List[TestResult]) -> Dict[str, float]:
        """Calculate average metrics for a set of results"""
        if not results:
            return {}
        
        successful_results = [r for r in results if r.success]
        
        return {
            "success_rate": len(successful_results) / len(results),
            "avg_processing_time": sum(r.processing_time for r in successful_results) / len(successful_results) if successful_results else 0,
            "avg_extraction_rate": sum(r.extraction_rate for r in successful_results) / len(successful_results) if successful_results else 0,
            "avg_format_accuracy": sum(r.format_accuracy for r in successful_results) / len(successful_results) if successful_results else 0,
            "avg_overall_score": sum(r.overall_score for r in successful_results) / len(successful_results) if successful_results else 0,
            "total_fields_extracted": sum(len(r.extracted_fields) for r in successful_results),
            "fields_accuracy_above_80": sum(
                sum(1 for acc in r.field_accuracy.values() if acc >= 0.8) 
                for r in successful_results
            ),
            "production_ready": sum(1 for r in successful_results if r.overall_score >= 0.6)
        }












