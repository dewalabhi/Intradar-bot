#!/bin/bash
# 🚀 PAPER TRADING STARTUP SCRIPT
# Quick and easy way to start paper trading

set -e  # Exit on any error

echo "🚀 INTRADAR BOT - PAPER TRADING STARTUP"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Please run this script from the /workspaces/Intradar-bot directory"
    exit 1
fi

echo "📂 Current directory: $(pwd)"

# Check Python environment
echo "🐍 Checking Python environment..."
python3 --version || {
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
}

# Install dependencies if needed
if [ ! -d "venv" ] && [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Check if config file exists
if [ ! -f "config/config.yaml" ]; then
    echo "❌ Configuration file not found at config/config.yaml"
    echo "Creating default config..."
    mkdir -p config
    # You would create a default config here
fi

echo ""
echo "🎯 PAPER TRADING OPTIONS:"
echo "========================"
echo "1. Quick Demo (5 minutes, relaxed parameters)"
echo "2. Full Paper Trading Session (live simulation)"
echo "3. Production Runner (advanced mode)"
echo "4. View existing logs"
echo "5. Exit"
echo ""

while true; do
    read -p "Select option (1-5): " choice
    case $choice in
        1)
            echo "🎮 Starting Quick Demo..."
            echo "This will run a 5-minute demo with relaxed parameters"
            echo "Press Ctrl+C to stop anytime"
            sleep 2
            python3 demo_paper_trading.py
            break
            ;;
        2)
            echo "📊 Starting Full Paper Trading Session..."
            echo "This will run the complete Nifty 50 paper trading system"
            echo "Press Ctrl+C to stop anytime"
            sleep 2
            python3 test_paper_trading.py
            break
            ;;
        3)
            echo "🚀 Starting Production Runner..."
            echo "Advanced mode with full configuration control"
            echo "Press Ctrl+C to stop anytime"
            sleep 2
            python3 main_runner.py --mode paper --config config/config.yaml
            break
            ;;
        4)
            echo "📋 Recent Paper Trading Logs:"
            echo "============================"
            ls -la data/logs/ 2>/dev/null || echo "No logs found yet"
            ls -la data/backtests/ 2>/dev/null || echo "No backtest results found yet"
            echo ""
            ;;
        5)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please select 1-5."
            ;;
    esac
done

echo ""
echo "✅ Paper trading session completed!"
echo ""
echo "📊 Check your results:"
echo "- Logs: data/logs/"
echo "- Results: data/backtests/"
echo ""
echo "📖 For more help, read: PAPER_TRADING_STARTUP_GUIDE.md"
echo ""
echo "🔥 Ready for live trading? Update config to 'live' mode and add Fyers credentials!"
