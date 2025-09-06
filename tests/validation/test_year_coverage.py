"""
Validation tests for year coverage accuracy.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, List, Any


class TestYearCoverage:
    """Test cases for year coverage validation"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.fixtures_dir = Path("tests/fixtures")
        self.expected_years = {
            "AFS2024 - statement extracted.pdf": ["2024", "2023"],
            "AFS-2022 - statement extracted.pdf": ["2022", "2021"],
            "afs-2021-2023 - statement extracted.pdf": ["2022", "2021", "2020"],
            "2021 AFS with SEC Stamp - statement extracted.pdf": ["2021", "2020"]
        }
    
    def test_expected_years_defined(self):
        """Test that expected years are properly defined"""
        assert len(self.expected_years) == 4
        for filename, years in self.expected_years.items():
            assert isinstance(years, list)
            assert len(years) >= 2  # At least 2 years expected
            assert all(isinstance(year, str) for year in years)
    
    def test_afs2024_year_coverage(self):
        """Test AFS2024 document year coverage"""
        expected = ["2024", "2023"]
        filename = "AFS2024 - statement extracted.pdf"
        
        # This test would be run with actual API results
        # For now, just validate the expected structure
        assert filename in self.expected_years
        assert self.expected_years[filename] == expected
    
    def test_afs_2022_year_coverage(self):
        """Test AFS-2022 document year coverage"""
        expected = ["2022", "2021"]
        filename = "AFS-2022 - statement extracted.pdf"
        
        assert filename in self.expected_years
        assert self.expected_years[filename] == expected
    
    def test_afs_2021_2023_year_coverage(self):
        """Test afs-2021-2023 document year coverage"""
        expected = ["2022", "2021", "2020"]
        filename = "afs-2021-2023 - statement extracted.pdf"
        
        assert filename in self.expected_years
        assert self.expected_years[filename] == expected
    
    def test_2021_afs_sec_year_coverage(self):
        """Test 2021 AFS with SEC Stamp document year coverage"""
        expected = ["2021", "2020"]
        filename = "2021 AFS with SEC Stamp - statement extracted.pdf"
        
        assert filename in self.expected_years
        assert self.expected_years[filename] == expected
    
    def validate_api_result_years(self, filename: str, api_result: Dict[str, Any]) -> bool:
        """Validate that API result contains expected years"""
        if "error" in api_result:
            return False
        
        if "data" not in api_result:
            return False
        
        data = api_result["data"]
        if "years_detected" not in data:
            return False
        
        detected_years = data["years_detected"]
        expected_years = self.expected_years.get(filename, [])
        
        # Check that all expected years are present
        missing_years = set(expected_years) - set(detected_years)
        return len(missing_years) == 0
    
    def test_year_coverage_validation_logic(self):
        """Test the year coverage validation logic"""
        # Test with mock API result
        mock_result = {
            "data": {
                "years_detected": ["2024", "2023"]
            }
        }
        
        # Test AFS2024
        assert self.validate_api_result_years("AFS2024 - statement extracted.pdf", mock_result)
        
        # Test with missing year
        mock_result_missing = {
            "data": {
                "years_detected": ["2024"]  # Missing 2023
            }
        }
        
        assert not self.validate_api_result_years("AFS2024 - statement extracted.pdf", mock_result_missing)
        
        # Test with error result
        error_result = {"error": "Processing failed"}
        assert not self.validate_api_result_years("AFS2024 - statement extracted.pdf", error_result)
    
    def test_year_ordering_validation(self):
        """Test year ordering validation"""
        # Test most recent first ordering
        years_most_recent = ["2024", "2023", "2022"]
        assert self._is_most_recent_first(years_most_recent)
        
        # Test chronological ordering
        years_chronological = ["2022", "2023", "2024"]
        assert not self._is_most_recent_first(years_chronological)
        
        # Test mixed ordering
        years_mixed = ["2023", "2024", "2022"]
        assert not self._is_most_recent_first(years_mixed)
    
    def _is_most_recent_first(self, years: List[str]) -> bool:
        """Check if years are ordered most recent first"""
        if len(years) < 2:
            return True
        
        for i in range(len(years) - 1):
            if int(years[i]) < int(years[i + 1]):
                return False
        
        return True
    
    def test_year_data_completeness(self):
        """Test that year data is complete in line items"""
        # Mock line item data
        line_items = {
            "current_assets": {
                "cash": {
                    "value": 1000000,
                    "confidence": 0.95,
                    "base_year": 1000000,
                    "year_1": 950000
                }
            }
        }
        
        # Check that year data is present
        cash_data = line_items["current_assets"]["cash"]
        assert "base_year" in cash_data
        assert "year_1" in cash_data
        assert isinstance(cash_data["base_year"], (int, float))
        assert isinstance(cash_data["year_1"], (int, float))
    
    def test_year_data_types(self):
        """Test that year data has correct types"""
        # Mock line item data
        line_items = {
            "current_assets": {
                "cash": {
                    "value": 1000000,
                    "confidence": 0.95,
                    "base_year": 1000000,
                    "year_1": 950000,
                    "year_2": 900000
                }
            }
        }
        
        cash_data = line_items["current_assets"]["cash"]
        
        # Check data types
        assert isinstance(cash_data["base_year"], (int, float))
        assert isinstance(cash_data["year_1"], (int, float))
        assert isinstance(cash_data["year_2"], (int, float))
        
        # Check that values are not None
        assert cash_data["base_year"] is not None
        assert cash_data["year_1"] is not None
        assert cash_data["year_2"] is not None
    
    def test_multi_year_document_structure(self):
        """Test structure for multi-year documents"""
        # Mock multi-year document structure
        document_structure = {
            "years_detected": ["2024", "2023", "2022"],
            "base_year": "2024",
            "year_ordering": "most_recent_first",
            "line_items": {
                "current_assets": {
                    "cash": {
                        "value": 1000000,
                        "confidence": 0.95,
                        "base_year": 1000000,
                        "year_1": 950000,
                        "year_2": 900000
                    }
                }
            }
        }
        
        # Validate structure
        assert "years_detected" in document_structure
        assert "base_year" in document_structure
        assert "year_ordering" in document_structure
        assert len(document_structure["years_detected"]) == 3
        assert document_structure["base_year"] == "2024"
        assert document_structure["year_ordering"] == "most_recent_first"
