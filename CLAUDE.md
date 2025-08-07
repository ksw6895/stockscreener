# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Enhanced NASDAQ Stock Screener - A Python-based stock analysis tool with comprehensive financial metrics, backtesting, and both GUI/CLI interfaces. Analyzes NASDAQ stocks using the Financial Modeling Prep API.

## Development Commands

### Initial Setup
```bash
pip install -r requirements.txt
```

### Running the Application
- **GUI Mode**: `python gui.py`
- **CLI Mode**: `python stock_screener.py`
- **Backtesting**: `python backtest.py`

### API Configuration
1. Copy `.env.example` to `.env`
2. Add your Financial Modeling Prep API key: `FMP_API_KEY=your_api_key_here`

## Architecture

### Core Components

**Analyzers** (src/analyzers/):
- `growth_analyzer.py`: Revenue, earnings, and EPS growth metrics
- `risk_analyzer.py`: Beta, volatility, debt ratios, financial health scores
- `valuation_analyzer.py`: P/E, PEG, P/B ratios, DCF valuation
- `sentiment_analyzer.py`: Analyst ratings, price targets, ESG scores

**API Client** (src/api_client.py):
- Async HTTP client with rate limiting (300 requests/minute)
- Connection pooling and retry logic
- Caches sector data to minimize API calls

**Data Flow**:
1. `stock_screener.py` orchestrates the analysis pipeline
2. `src/data_fetcher.py` retrieves and caches financial data
3. Analyzers process metrics and calculate scores
4. `src/output_formatter.py` generates Excel reports with charts

### Key Design Patterns

- **Async/Await**: All API calls use asyncio for concurrent processing
- **Sector-Relative Scoring**: Metrics compared to sector peers (11 sectors supported)
- **Quality Score**: Weighted combination of growth (40%), risk (30%), valuation (20%), sentiment (10%)
- **Error Resilience**: Comprehensive error handling with fallback values

### Configuration

**config.json**: Contains analyzer parameters, API settings, screening criteria
- Modify thresholds, weights, and filters without code changes
- Sector-specific configurations for targeted analysis

**Environment Variables**:
- `FMP_API_KEY`: Required for API access
- `DEBUG`: Enable detailed logging

## Important Notes

- API key is required and must be kept secure (use .env file)
- Rate limiting is enforced at 300 requests/minute
- Excel output includes automated charts using openpyxl
- Backtesting uses historical data with matplotlib visualizations
- GUI built with tkinter, provides real-time analysis updates