# 🎯 Nifty 50 Intraday Trading Bot

A specialized Python trading bot optimized exclusively for **Nifty 50 stocks** with advanced intraday strategies, Indian market timing, and sector-wise optimization.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Nifty 50 strategy test:**
   ```bash
   python test_nifty50_strategy.py
   ```

3. **Live trading setup:**
   ```bash
   python src/main.py --mode live --market indian --focus nifty50
   ```

## 📊 Strategy: Balanced Breakout (Nifty 50 Optimized)

- **🎯 Focus**: Top 50 most liquid Indian stocks only
- **⏰ Timeframe**: 1-minute intraday scalping  
- **💰 Position Size**: Standardized ₹50,000 per trade
- **📊 Liquidity**: Optimized for high-volume Nifty 50 characteristics
- **🏛️ Market**: NSE (National Stock Exchange) with IST timing

## ⚙️ Nifty 50 Configuration

The strategy is pre-configured for optimal Nifty 50 trading:
- **Trading Window**: 9:30 AM - 3:00 PM IST
- **Volume Threshold**: 0.8x (high liquidity adjustment)
- **Stop Loss**: 0.9x multiplier (tighter stops)
- **Sectors**: IT, Banking, Energy, Auto, FMCG optimization
- **Circuit Risk**: Minimal for top 50 stocks

## 📈 Nifty 50 Advantages

- ✅ **Highest Liquidity**: Easy entry/exit, tight spreads
- ✅ **Lower Impact Cost**: Minimal slippage on trades  
- ✅ **Predictable Patterns**: Strong institutional following
- ✅ **Sector Diversification**: Balanced across sectors
- ✅ **Circuit Risk Minimal**: Top 50 stocks rarely hit limits
- ✅ **News Coverage**: Best information flow for analysis

## 🎯 Supported Nifty 50 Stocks

RELIANCE, TCS, HDFCBANK, BHARTIARTL, ICICIBANK, SBIN, ITC, HINDUNILVR, LT, HCLTECH, MARUTI, SUNPHARMA, INFY, WIPRO, and 36 more...

## 📋 Requirements

- Python 3.8+
- All dependencies in `requirements.txt`

## ⚠️ Disclaimer

This is for educational purposes only. Never risk money you cannot afford to lose.
