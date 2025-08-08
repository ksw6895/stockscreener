# Enhanced NASDAQ Stock Screener 📈

A comprehensive stock screening and analysis system for NASDAQ stocks with powerful financial analysis, backtesting capabilities, and professional reporting.

강력한 금융 분석, 백테스팅 기능 및 전문적인 리포팅을 갖춘 NASDAQ 주식을 위한 종합적인 주식 스크리닝 및 분석 시스템입니다.

## 🌟 Key Features

### Core Functionality
- **Advanced Financial Analysis**: 20+ financial metrics with comprehensive scoring
- **Sector-Relative Evaluation**: Compare performance within the same sector (11 sectors supported)
- **Risk Profiling**: Debt levels, margin stability, cash flow quality assessment
- **Backtesting Engine**: Historical strategy validation with Sharpe Ratio, Maximum Drawdown
- **Benchmark Comparison**: Performance analysis against S&P 500, NASDAQ indices
- **Multi-Interface Support**: Both GUI and CLI with full feature parity
- **Professional Reports**: Excel, CSV, JSON, and text outputs with charts

### New Features (v2.1.0)
- **Pydantic Configuration**: Type-safe configuration with validation
- **Custom Profiles**: Save and load custom screening profiles
- **Input Validation**: Real-time validation with helpful tooltips in GUI
- **Enhanced Excel Output**: Freeze panes, filters, conditional formatting, hyperlinks
- **Run Metadata**: Complete audit trail of each screening run
- **CI/CD Pipeline**: GitHub Actions for automated testing and daily runs
- **Caching System**: Multi-backend cache (memory/file/SQLite) for API optimization
- **Unit Tests**: Comprehensive test coverage for analyzers

## 📋 Prerequisites

- Python 3.8 or higher
- Financial Modeling Prep API key (paid subscription required)
- 4GB RAM minimum
- Internet connection

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/ksw6895/stockscreener.git
cd stockscreener

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac/WSL:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

### 2. Configuration

Create a `.env` file in the project root:

```env
FMP_API_KEY=your_api_key_here
DEBUG=false
```

### 3. Run the Screener

```bash
# GUI mode
python gui.py

# CLI mode with default settings
python stock_screener.py

# CLI with custom parameters
python stock_screener.py --profile quality --min-market-cap 1000 --top-n 20

# Backtesting
python backtest.py --period 6m --investment 100000
```

## 📖 User Guide

### GUI Mode

#### Starting the GUI

```bash
python gui.py
```

#### GUI Features

1. **Initial Filters Tab**
   - Market Cap Range: Set minimum and maximum market capitalization
   - Sector Filters: Option to exclude financial sector
   - ROE Criteria: Configure Return on Equity thresholds

2. **Growth Settings Tab**
   - Revenue CAGR: Minimum revenue growth rate
   - EPS CAGR: Minimum earnings per share growth
   - FCF CAGR: Minimum free cash flow growth

3. **Risk Settings Tab**
   - Debt/Equity: Maximum debt-to-equity ratio
   - Interest Coverage: Minimum interest coverage ratio
   - Volatility thresholds

4. **Valuation Settings Tab**
   - P/E Ratio: Maximum price-to-earnings ratio
   - P/B Ratio: Maximum price-to-book ratio
   - FCF Yield: Minimum free cash flow yield

5. **Output Settings Tab**
   - File formats: Excel, CSV, JSON, Text
   - Top N stocks to display
   - Minimum quality score threshold

6. **Presets**
   - **Quality**: Focus on stable, profitable companies
   - **Growth**: High-growth companies
   - **Value**: Undervalued opportunities
   - **Balanced**: Equal weight across all factors

7. **Custom Profiles**
   - Save Profile: Save current settings to a JSON file
   - Load Profile: Load previously saved settings

### CLI Mode

#### Command Line Options

```bash
# Configuration
--config FILE               Path to configuration file
--profile PROFILE          Load preset profile (quality/growth/value/balanced)
--log-level LEVEL          Set logging level (DEBUG/INFO/WARNING/ERROR)

# Market Cap Filters
--min-market-cap VALUE     Minimum market cap in millions
--max-market-cap VALUE     Maximum market cap in millions

# Financial Metrics
--min-roe VALUE           Minimum ROE percentage
--min-revenue-growth VALUE Minimum revenue CAGR percentage
--min-eps-growth VALUE    Minimum EPS CAGR percentage

# Output Options
--output-format FORMAT    Output format (excel/csv/json/text)
--output-dir DIR         Output directory path
--top-n NUMBER           Number of top stocks to display
```

#### CLI Examples

```bash
# High-quality companies with strong fundamentals
python stock_screener.py --profile quality --min-market-cap 5000 --top-n 20

# Growth stocks with specific criteria
python stock_screener.py --min-revenue-growth 20 --min-eps-growth 15

# Full custom configuration
python stock_screener.py \
    --min-market-cap 1000 \
    --max-market-cap 50000 \
    --min-roe 15 \
    --min-revenue-growth 10 \
    --output-format excel \
    --top-n 30
```

### Backtesting

```bash
# 6-month backtest with $100,000 investment
python backtest.py --period 6m --investment 100000

# 1-year backtest with quarterly rebalancing
python backtest.py --period 1y --rebalance quarterly

# Compare against QQQ instead of SPY
python backtest.py --period 1y --benchmark QQQ
```

## 💻 Platform-Specific Installation

### Windows Installation

1. **Install Python**
   - Download Python 3.8+ from [python.org](https://www.python.org/downloads/)
   - Check "Add Python to PATH" during installation

2. **Install Git (optional)**
   - Download from [git-scm.com](https://git-scm.com/download/win)

3. **Setup Project**
   ```cmd
   git clone https://github.com/ksw6895/stockscreener.git
   cd stockscreener
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

### WSL (Windows Subsystem for Linux)

1. **Install WSL2**
   ```powershell
   wsl --install
   ```

2. **Setup Ubuntu**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install python3.8 python3-pip python3-venv git python3-tk -y
   ```

3. **Setup X Server for GUI**
   - Install [VcXsrv](https://sourceforge.net/projects/vcxsrv/) on Windows
   - Add to ~/.bashrc:
   ```bash
   export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
   ```

4. **Install Project**
   ```bash
   git clone https://github.com/ksw6895/stockscreener.git
   cd stockscreener
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## 📊 Output Files

### Excel Output (`.xlsx`)
- **Summary Sheet**: Top stocks with key metrics
- **Details Sheet**: Comprehensive metrics for all stocks
- **Growth Analysis**: Revenue, EPS, FCF growth details
- **Risk Analysis**: Debt, liquidity, volatility metrics
- **Valuation Sheet**: P/E, P/B, DCF valuations
- **Sector Analysis**: Sector-wise performance comparison
- **Charts**: Visual representations of key metrics

Features:
- Frozen header rows
- Auto-filters on all columns
- Conditional formatting for scores
- Hyperlinks to Yahoo Finance

### Other Formats
- **CSV**: Tabular format for further analysis
- **JSON**: Complete structured data with metadata
- **Text**: Human-readable summary report
- **Run Metadata**: Complete audit trail (`run_metadata.json`)

## 🏗️ Project Structure

```
stockscreener/
├── src/
│   ├── analyzers/          # Financial analysis modules
│   │   ├── growth_analyzer.py
│   │   ├── risk_analyzer.py
│   │   ├── valuation_analyzer.py
│   │   └── sentiment_analyzer.py
│   ├── api_client.py       # Async HTTP client with rate limiting
│   ├── cache.py            # Caching system
│   ├── config_model.py     # Pydantic configuration
│   ├── data_fetcher.py     # Data retrieval and caching
│   ├── gui_helpers.py      # GUI utilities
│   └── metadata_manager.py # Run metadata tracking
├── tests/                  # Unit tests
├── .github/workflows/      # CI/CD pipelines
├── stock_screener.py       # Main CLI application
├── gui.py                  # GUI application
├── backtest.py            # Backtesting engine
├── config.py              # Configuration management
├── output.py              # Report generation
└── requirements.txt       # Dependencies
```

## 🔑 API Key Setup

### Getting Financial Modeling Prep API Key

1. Visit [Financial Modeling Prep](https://financialmodelingprep.com/)
2. Click "Pricing" menu
3. Choose appropriate plan (minimum Starter plan $19/month recommended)
4. After signup, copy API key from Dashboard
5. Add to `.env` file

**Note**: Free plan limited to 250 requests/day - insufficient for full functionality

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/analyzers/test_growth_analyzer.py
```

## 🔧 Troubleshooting

### Common Issues

#### API Key Error
```
Error: API_KEY not found
```
Solution: Ensure `.env` file exists with `FMP_API_KEY=your_key`

#### Import Error
```
ModuleNotFoundError: No module named 'aiohttp'
```
Solution: Install dependencies with `pip install -r requirements.txt`

#### GUI Not Opening (WSL)
```
_tkinter.TclError: no display name
```
Solution: Install and configure X Server (VcXsrv)

#### Rate Limiting
```
Error: API rate limit exceeded
```
Solution: Upgrade API plan or enable caching

## ⚠️ Important Notes

1. **API Key Security**
   - Never commit `.env` file to Git
   - Keep API keys confidential

2. **Investment Disclaimer**
   - This tool is for educational and research purposes
   - Always do your own due diligence before investing
   - Past performance doesn't guarantee future results

3. **API Limitations**
   - 300 requests/minute rate limit
   - 5 concurrent connections maximum

4. **Data Accuracy**
   - Uses daily closing prices, not real-time data
   - Historical data uses adjusted close prices

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📜 License

MIT License - Free to use, modify, and distribute

## 📞 Support

For issues or questions:
1. Check [Issues](https://github.com/ksw6895/stockscreener/issues) page
2. Submit detailed error reports

## 🚦 Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] Git installed (optional)
- [ ] Project cloned/downloaded
- [ ] Virtual environment created and activated
- [ ] Dependencies installed
- [ ] FMP API key obtained
- [ ] `.env` file created with API key
- [ ] First run with GUI or CLI
- [ ] Backtesting executed (optional)

Ready to analyze stocks! 🎉