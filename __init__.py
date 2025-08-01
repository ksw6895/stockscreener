"""
Enhanced NASDAQ Stock Screener

A comprehensive stock screening and analysis system for NASDAQ stocks,
focusing on growth quality, risk assessment, valuation, and market sentiment.

This package provides:
- Advanced financial analysis using multiple metrics
- Sector-relative performance benchmarking
- Quality scoring system with multiple weighted components
- Detailed reporting in text and Excel formats
- User-friendly GUI for configuration and execution
"""

__version__ = "1.0.0"
__author__ = "Financial Analyst AI"

from config import config_manager
from models import StockAnalysisResult
from stock_screener import run_screener

__all__ = ['config_manager', 'StockAnalysisResult', 'run_screener']