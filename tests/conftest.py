"""
Pytest configuration and shared fixtures.
"""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_api_response():
    """Mock API response for testing."""
    return {
        "symbol": "AAPL",
        "companyName": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "marketCap": 3000000000000,
        "price": 180.00,
        "beta": 1.2,
        "pe": 28.5,
        "eps": 6.31,
        "dividend": 0.96
    }


@pytest.fixture
def mock_financial_statements():
    """Mock financial statements for testing."""
    return [
        {
            "date": "2023-12-31",
            "revenue": 400000000000,
            "netIncome": 100000000000,
            "eps": 6.31,
            "totalAssets": 350000000000,
            "totalLiabilities": 250000000000,
            "totalEquity": 100000000000,
            "operatingCashFlow": 110000000000,
            "capitalExpenditure": 10000000000,
            "freeCashFlow": 100000000000
        },
        {
            "date": "2022-12-31",
            "revenue": 390000000000,
            "netIncome": 99000000000,
            "eps": 6.11,
            "totalAssets": 340000000000,
            "totalLiabilities": 245000000000,
            "totalEquity": 95000000000,
            "operatingCashFlow": 108000000000,
            "capitalExpenditure": 9000000000,
            "freeCashFlow": 99000000000
        }
    ]


@pytest.fixture
def test_config():
    """Test configuration."""
    return {
        "api_key": "test_api_key",
        "base_url": "https://api.test.com",
        "initial_filters": {
            "market_cap_min": 1000000000,
            "market_cap_max": 10000000000000,
            "exclude_financial_sector": False,
            "roe": {
                "min_avg": 0.15,
                "min_each_year": 0.10,
                "years": 3
            }
        },
        "scoring": {
            "weights": {
                "growth_quality": 0.4,
                "risk_quality": 0.3,
                "valuation": 0.2,
                "sentiment": 0.1
            }
        }
    }


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("FMP_API_KEY", "test_api_key")
    monkeypatch.setenv("DEBUG", "true")