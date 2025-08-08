"""
Unit tests for the Risk Analyzer.
"""

import pytest
from src.analyzers.risk_analyzer import RiskAnalyzer


class TestRiskAnalyzer:
    """Test suite for RiskAnalyzer class."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a RiskAnalyzer instance."""
        return RiskAnalyzer()
    
    @pytest.fixture
    def sample_financial_data(self):
        """Sample financial data for testing."""
        return [
            {
                "date": "2023-12-31",
                "totalDebt": 50000000,
                "totalEquity": 100000000,
                "currentAssets": 40000000,
                "currentLiabilities": 20000000,
                "interestExpense": 2000000,
                "operatingIncome": 20000000,
                "freeCashFlow": 15000000
            },
            {
                "date": "2022-12-31",
                "totalDebt": 45000000,
                "totalEquity": 90000000,
                "currentAssets": 35000000,
                "currentLiabilities": 18000000,
                "interestExpense": 1800000,
                "operatingIncome": 18000000,
                "freeCashFlow": 12000000
            },
            {
                "date": "2021-12-31",
                "totalDebt": 40000000,
                "totalEquity": 80000000,
                "currentAssets": 30000000,
                "currentLiabilities": 15000000,
                "interestExpense": 1600000,
                "operatingIncome": 16000000,
                "freeCashFlow": 10000000
            }
        ]
    
    @pytest.fixture
    def sample_price_data(self):
        """Sample price data for volatility testing."""
        return [100, 102, 98, 103, 99, 101, 97, 104, 100, 102]
    
    def test_calculate_debt_metrics(self, analyzer, sample_financial_data):
        """Test debt metrics calculation."""
        metrics = analyzer.calculate_debt_metrics(sample_financial_data)
        
        assert "debt_to_equity" in metrics
        assert "interest_coverage" in metrics
        assert "debt_trend" in metrics
        
        # Check debt-to-equity ratio (50M / 100M = 0.5)
        assert abs(metrics["debt_to_equity"] - 0.5) < 0.01
        
        # Check interest coverage (20M / 2M = 10)
        assert abs(metrics["interest_coverage"] - 10) < 0.1
        
        # Check debt trend (debt is increasing)
        assert metrics["debt_trend"] > 0
    
    def test_calculate_liquidity_metrics(self, analyzer, sample_financial_data):
        """Test liquidity metrics calculation."""
        metrics = analyzer.calculate_liquidity_metrics(sample_financial_data)
        
        assert "current_ratio" in metrics
        assert "working_capital" in metrics
        assert "working_capital_trend" in metrics
        
        # Check current ratio (40M / 20M = 2.0)
        assert abs(metrics["current_ratio"] - 2.0) < 0.01
        
        # Check working capital (40M - 20M = 20M)
        assert metrics["working_capital"] == 20000000
    
    def test_calculate_volatility(self, analyzer, sample_price_data):
        """Test volatility calculation."""
        volatility = analyzer.calculate_volatility(sample_price_data)
        
        assert volatility > 0
        assert volatility < 1  # Should be reasonable for the sample data
    
    def test_calculate_beta(self, analyzer):
        """Test beta calculation."""
        stock_returns = [0.02, -0.01, 0.03, -0.02, 0.01]
        market_returns = [0.01, -0.005, 0.02, -0.01, 0.005]
        
        beta = analyzer.calculate_beta(stock_returns, market_returns)
        
        assert beta is not None
        assert 0 < beta < 3  # Reasonable beta range
    
    def test_calculate_risk_score(self, analyzer):
        """Test risk score calculation."""
        risk_metrics = {
            "debt_to_equity": 0.5,
            "interest_coverage": 10,
            "current_ratio": 2.0,
            "volatility": 0.2,
            "beta": 1.1,
            "debt_trend": 0.05
        }
        
        score = analyzer.calculate_risk_score(risk_metrics)
        
        assert 0 <= score <= 1
        assert score > 0.6  # Should be relatively high for good metrics
    
    def test_financial_health_score(self, analyzer, sample_financial_data):
        """Test financial health score calculation."""
        score = analyzer.calculate_financial_health_score(sample_financial_data)
        
        assert 0 <= score <= 1
        assert score > 0.5  # Should indicate decent financial health
    
    def test_handle_missing_data(self, analyzer):
        """Test handling of missing or invalid data."""
        # Empty data
        metrics = analyzer.calculate_debt_metrics([])
        assert metrics["debt_to_equity"] == float('inf')
        assert metrics["interest_coverage"] == 0
        
        # Data with None values
        data_with_none = [
            {
                "date": "2023-12-31",
                "totalDebt": None,
                "totalEquity": 100000000,
                "interestExpense": 2000000,
                "operatingIncome": 20000000
            }
        ]
        metrics = analyzer.calculate_debt_metrics(data_with_none)
        assert metrics is not None
        
        # Zero equity (edge case)
        data_zero_equity = [
            {
                "date": "2023-12-31",
                "totalDebt": 50000000,
                "totalEquity": 0,
                "interestExpense": 2000000,
                "operatingIncome": 20000000
            }
        ]
        metrics = analyzer.calculate_debt_metrics(data_zero_equity)
        assert metrics["debt_to_equity"] == float('inf')
    
    def test_margin_stability(self, analyzer):
        """Test margin stability calculation."""
        margins = [0.15, 0.16, 0.14, 0.15, 0.16]
        stability = analyzer.calculate_margin_stability(margins)
        
        assert 0 <= stability <= 1
        assert stability > 0.8  # Should be high for consistent margins
        
        # Test with volatile margins
        volatile_margins = [0.10, 0.20, 0.05, 0.25, 0.08]
        stability = analyzer.calculate_margin_stability(volatile_margins)
        assert stability < 0.5
    
    def test_cash_flow_quality(self, analyzer, sample_financial_data):
        """Test cash flow quality assessment."""
        quality = analyzer.assess_cash_flow_quality(sample_financial_data)
        
        assert 0 <= quality <= 1
        assert quality > 0.5  # Should be decent for positive FCF
        
        # Test with negative FCF
        negative_fcf_data = sample_financial_data.copy()
        negative_fcf_data[0]["freeCashFlow"] = -5000000
        quality = analyzer.assess_cash_flow_quality(negative_fcf_data)
        assert quality < 0.5