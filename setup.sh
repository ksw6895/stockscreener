#!/bin/bash

# Setup script for the Enhanced NASDAQ Stock Screener

echo "🚀 Setting up Enhanced NASDAQ Stock Screener..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file template..."
    cat > .env << EOL
# Financial Modeling Prep API Key
FMP_API_KEY=your_api_key_here

# Debug mode (true/false)
DEBUG=false
EOL
    echo "⚠️  Please edit .env file and add your FMP API key"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run the screener:"
echo "  GUI mode: python gui.py"
echo "  CLI mode: python stock_screener.py"
echo "  Backtest: python backtest.py"
echo ""
echo "Don't forget to add your FMP API key to the .env file!"