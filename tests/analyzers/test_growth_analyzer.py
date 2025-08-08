"""
Unit tests for the Growth Analyzer.
"""

import pytest
from datetime import datetime
from api.python.analyzers.growth_analyzer import GrowthAnalyzer


class TestGrowthAnalyzer:
    """Test suite for GrowthAnalyzer class."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a GrowthAnalyzer instance."""
        return GrowthAnalyzer()
    
    @pytest.fixture
    def sample_financial_data(self):
        """Sample financial data for testing."""
        return [
            {
                "date": "2023-12-31",
                "revenue": 100000000,
                "eps": 5.0,
                "operatingCashFlow": 30000000,
                "capitalExpenditure": 10000000
            },
            {
                "date": "2022-12-31",
                "revenue": 85000000,
                "eps": 4.2,
                "operatingCashFlow": 25000000,
                "capitalExpenditure": 8000000
            },
            {
                "date": "2021-12-31",
                "revenue": 70000000,
                "eps": 3.5,
                "operatingCashFlow": 20000000,
                "capitalExpenditure": 7000000
            },
            {
                "date": "2020-12-31",
                "revenue": 60000000,
                "eps": 3.0,
                "operatingCashFlow": 18000000,
                "capitalExpenditure": 6000000
            }
        ]
    
    def test_calculate_cagr(self, analyzer):
        """Test CAGR calculation."""
        # Test with positive growth
        values = [100, 120, 140, 160]
        cagr = analyzer._calculate_cagr(values, len(values) - 1)
        assert 0.16 < cagr < 0.17  # ~16.96% CAGR
        
        # Test with negative growth
        values = [100, 90, 80, 70]
        cagr = analyzer._calculate_cagr(values, len(values) - 1)
        assert cagr < 0
        
        # Test with zero initial value
        values = [0, 10, 20, 30]
        cagr = analyzer._calculate_cagr(values, len(values) - 1)
        assert cagr == 0
        
        # Test with single value
        values = [100]
        cagr = analyzer._calculate_cagr(values, 1)
        assert cagr == 0
    
    def test_calculate_consistency_score(self, analyzer):
        """Test consistency score calculation."""
        # Perfect consistency
        growth_rates = [0.1, 0.1, 0.1, 0.1]
        score = analyzer._calculate_consistency_score(growth_rates)
        assert score == 1.0
        
        # High variability
        growth_rates = [0.5, -0.3, 0.8, -0.2]
        score = analyzer._calculate_consistency_score(growth_rates)
        assert 0 < score < 0.5
        
        # Empty list
        growth_rates = []
        score = analyzer._calculate_consistency_score(growth_rates)
        assert score == 0
    
    def test_analyze_revenue_growth(self, analyzer, sample_financial_data):
        """Test revenue growth analysis."""
        result = analyzer.analyze_revenue_growth(sample_financial_data)
        
        assert result is not None
        assert "cagr" in result
        assert "yoy_growth_rates" in result
        assert "consistency_score" in result
        assert "volatility" in result
        
        # Check CAGR is reasonable
        assert 0.1 < result["cagr"] < 0.25  # Between 10% and 25%
        
        # Check YoY growth rates
        assert len(result["yoy_growth_rates"]) == 3
        assert all(rate > 0 for rate in result["yoy_growth_rates"])
    
    def test_analyze_eps_growth(self, analyzer, sample_financial_data):
        """Test EPS growth analysis."""
        result = analyzer.analyze_eps_growth(sample_financial_data)
        
        assert result is not None
        assert "cagr" in result
        assert "yoy_growth_rates" in result
        assert "consistency_score" in result
        
        # Check CAGR is reasonable
        assert 0.1 < result["cagr"] < 0.25
    
    def test_analyze_fcf_growth(self, analyzer, sample_financial_data):
        """Test FCF growth analysis."""
        result = analyzer.analyze_fcf_growth(sample_financial_data)
        
        assert result is not None
        assert "cagr" in result
        assert "yoy_growth_rates" in result
        assert "consistency_score" in result
        assert "fcf_values" in result
        
        # Check FCF values are calculated correctly
        fcf_values = result["fcf_values"]
        assert len(fcf_values) == len(sample_financial_data)
        assert fcf_values[0] == 20000000  # 30M - 10M
    
    def test_calculate_growth_score(self, analyzer):
        """Test growth score calculation."""
        growth_metrics = {
            "revenue_cagr": 0.15,
            "eps_cagr": 0.20,
            "fcf_cagr": 0.18,
            "revenue_consistency": 0.8,
            "eps_consistency": 0.75,
            "fcf_consistency": 0.7
        }
        
        score = analyzer.calculate_growth_score(growth_metrics)
        
        assert 0 <= score <= 1
        assert score > 0.5  # Should be relatively high given good metrics
    
    def test_handle_missing_data(self, analyzer):
        """Test handling of missing or invalid data."""
        # Empty data
        result = analyzer.analyze_revenue_growth([])
        assert result["cagr"] == 0
        assert result["consistency_score"] == 0
        
        # Data with None values
        data_with_none = [
            {"date": "2023-12-31", "revenue": None},
            {"date": "2022-12-31", "revenue": 100000}
        ]
        result = analyzer.analyze_revenue_growth(data_with_none)
        assert result is not None
        
        # Data with negative values
        data_with_negative = [
            {"date": "2023-12-31", "revenue": -100000},
            {"date": "2022-12-31", "revenue": 100000}
        ]
        result = analyzer.analyze_revenue_growth(data_with_negative)
        assert result is not None
    
    def test_sector_relative_scoring(self, analyzer):
        """Test sector-relative scoring."""
        growth_metrics = {
            "revenue_cagr": 0.15,
            "eps_cagr": 0.20,
            "fcf_cagr": 0.18
        }
        
        sector_benchmarks = {
            "revenue_growth": 0.10,
            "eps_growth": 0.12,
            "fcf_growth": 0.10
        }
        
        score = analyzer.calculate_sector_relative_score(growth_metrics, sector_benchmarks)
        
        assert 0 <= score <= 1
        assert score > 0.6  # Should be high since metrics exceed benchmarks