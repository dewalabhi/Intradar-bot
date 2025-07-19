# 🤖 Professional Trading Bot

A comprehensive Python trading bot with multiple strategies, risk management, and professional-grade backtesting.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run a backtest:**
   ```bash
   python src/main.py --mode backtest
   ```

3. **Test with specific symbols:**
   ```bash
   python src/main.py --mode backtest --symbols AAPL MSFT GOOGL
   ```

## 📊 Strategies Included

- **Moving Average Crossover**: Classic trend-following strategy
- **RSI Mean Reversion**: Contrarian approach for range-bound markets

## ⚙️ Configuration

Edit `config/config.yaml` to customize:
- Trading symbols
- Strategy parameters
- Risk management settings
- Initial capital

## 📈 Features

- Multiple trading strategies
- Professional backtesting with Backtrader
- Comprehensive performance analytics
- Risk management and position sizing
- Real-time data via Yahoo Finance
- Detailed logging and reporting

## 📋 Requirements

- Python 3.8+
- All dependencies in `requirements.txt`

## ⚠️ Disclaimer

This is for educational purposes only. Never risk money you cannot afford to lose.
