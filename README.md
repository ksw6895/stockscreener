# Enhanced NASDAQ Stock Screener

[한국어 README](README.ko.md)

A comprehensive stock screening and analysis system for NASDAQ stocks, focusing on:
- Growth quality (revenue, EPS, and FCF growth)
- Risk assessment (debt, margins, working capital)
- Valuation metrics (P/E, P/B, FCF yield)
- Market sentiment (insider trading, earnings surprises)

## Features

- **Advanced Financial Analysis**: Comprehensive analysis using 20+ financial metrics
- **Sector-Relative Scoring**: Compare stocks to sector benchmarks
- **Growth Quality Assessment**: Analyze growth magnitude, consistency, and sustainability
- **Risk Profiling**: Evaluate debt levels, margin stability, and cash flow quality
- **Valuation Analysis**: Compare traditional and growth-adjusted valuation metrics
- **Market Sentiment Analysis**: Incorporate insider trading patterns and earnings surprises
- **Detailed Reporting**: Generate comprehensive reports in text and Excel formats
- **User-Friendly GUI**: Configure and run the screener with an intuitive interface
- **Secure API Key Management**: Uses environment variables for safe API key storage

## Installation

### Prerequisites

- Python 3.8 or later
- Financial Modeling Prep API subscription
- Required Python packages (install via pip):
  - aiohttp
  - numpy
  - openpyxl
  - python-dotenv
  - tkinter (usually comes with Python)

### Setup

1. Clone this repository:
```bash
git clone https://github.com/ksw6895/stockscreener.git
cd stockscreener
```

2. Install the required dependencies:
```bash
pip install aiohttp numpy openpyxl python-dotenv
```

3. Create a `.env` file in the project root and add your API key:
```
# Financial Modeling Prep API Key
FMP_API_KEY=your_api_key_here
```

4. Configure other settings in `enhanced_config.json` if needed

## Usage

### GUI Mode

To run the application with the graphical user interface:

```bash
python gui.py
```

### Command Line Mode

To run the application from the command line:

```bash
python stock_screener.py
```

### Backtesting Mode

To run backtesting analysis:

```bash
python backtest.py
```

## Configuration

The application uses two configuration methods:

1. **Environment Variables** (`.env` file):
   - `FMP_API_KEY`: Your Financial Modeling Prep API key (required)

2. **Configuration File** (`enhanced_config.json`):
   - `initial_filters`: Market cap and sector filters
   - `growth_quality`: Growth rate targets and analysis weights
   - `scoring`: Component weight settings for the final quality score
   - `output`: Report format and file naming options
   - `sector_benchmarks`: Industry-specific benchmark values

Key configuration options:

- **Market Cap Filters**: Set minimum and maximum market cap ranges
- **Growth Targets**: Define minimum growth rates for revenue, EPS, and FCF
- **Risk Thresholds**: Configure debt-to-equity and other risk limits
- **Scoring Weights**: Adjust the importance of different analysis components
- **Output Options**: Customize report formats and file naming

## File Structure

```
├── analyzers/              # Financial analysis modules
│   ├── base_analyzer.py    # Base class for analyzers
│   ├── growth_analyzer.py  # Growth quality analysis
│   ├── risk_analyzer.py    # Risk assessment
│   ├── valuation_analyzer.py # Valuation metrics analysis
│   └── sentiment_analyzer.py # Market sentiment analysis
├── backtest_results/       # Backtesting output files
├── api_client.py          # API communication layer
├── backtest.py           # Backtesting functionality
├── config.py             # Configuration management
├── data_processing.py    # Data preparation and processing
├── enhanced_config.json  # Main configuration file
├── gui.py               # User interface
├── models.py            # Data models and type definitions
├── output.py            # Report generation
├── quality_scorer.py    # Comprehensive quality scoring
└── stock_screener.py    # Main screening logic
```

## API Requirements

This application requires a **paid subscription** to [Financial Modeling Prep API](https://financialmodelingprep.com/). The free tier has limited requests that won't be sufficient for comprehensive stock screening.

Required API endpoints:
- Company profiles and stock lists
- Financial statements (Income, Balance Sheet, Cash Flow)
- Financial ratios and key metrics
- Insider trading data
- Social sentiment data
- Historical price data

## Example Output

The screener generates detailed reports with:

1. **Summary Report**: All qualifying stocks ranked by quality score
2. **Detailed Analysis** for each stock including:
   - Growth metrics (revenue CAGR, EPS CAGR, FCF CAGR)
   - Risk metrics (debt-to-equity, interest coverage)
   - Valuation metrics (P/E, P/B, FCF yield)
   - Component scores for each analysis area
   - Sector-relative percentile rankings

3. **Excel Reports** with additional visualizations:
   - Sector distribution charts
   - Growth comparison charts
   - Valuation comparison charts
   - Sector performance analysis

4. **Backtesting Results**:
   - Portfolio performance analysis
   - Individual stock performance tracking
   - Wealth growth visualization
   - Risk-adjusted returns

## Security Features

- **Environment Variables**: API keys are stored securely in `.env` files
- **Git Ignore**: Sensitive files are automatically excluded from version control
- **Configuration Separation**: Public settings separated from private credentials

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Notes

- The quality score is a composite of multiple weighted components and is relative to other screened stocks
- Sector benchmarks are used to provide context for stock performance
- All financial data is fetched in real-time from Financial Modeling Prep API
- The application includes rate limiting to respect API constraints

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This software is for educational and research purposes only. It should not be considered as financial advice. Always consult with a qualified financial advisor before making investment decisions.