# 🚀 Paper Trading Bot Startup Guide

## Overview
This guide will help you start the trading bot in paper trading mode to test the system before live market deployment.

## Prerequisites

### 1. Configure Python Environment
```bash
cd /workspaces/Intradar-bot
pip install -r requirements.txt
```

### 2. Verify Configuration
Check your configuration file at `config/config.yaml`. The key settings for paper trading:

```yaml
trading:
  mode: "paper"  # Set to "paper" for paper trading
  initial_capital: 100000
  commission: 0.001

symbols:
  primary: 
    - 'RELIANCE.NS'
    - 'TCS.NS'
    - 'HDFCBANK.NS'
    - 'INFY.NS'
    - 'HINDUNILVR.NS'
```

## Starting Paper Trading Bot

### Option 1: Quick Demo (Recommended for First Time)
```bash
cd /workspaces/Intradar-bot
python demo_paper_trading.py
```

This will run a 5-minute demo with relaxed parameters to show how the system works.

### Option 2: Full Paper Trading Session
```bash
cd /workspaces/Intradar-bot
python test_paper_trading.py
```

This runs the complete paper trading system with Nifty 50 stocks.

### Option 3: Production Runner (Advanced)
```bash
cd /workspaces/Intradar-bot
python main_runner.py --mode paper --config config/config.yaml
```

## What to Expect

### 1. System Initialization
- ✅ Loading configuration
- ✅ Initializing paper trading manager
- ✅ Setting up data providers
- ✅ Loading Nifty 50 strategy

### 2. Market Data Loading
- Fetching recent market data for selected stocks
- Calculating technical indicators
- Setting up trading signals

### 3. Trading Simulation
- **Buy Signals**: When breakout conditions are met
- **Sell Signals**: Stop loss or take profit triggered
- **Position Management**: Track open positions
- **Risk Management**: Position sizing and risk limits

### 4. Real-time Monitoring
You'll see output like:
```
[2024-01-15 09:30:15] 📊 Paper Trading Started - Capital: ₹100,000
[2024-01-15 09:35:22] 🔍 Scanning: RELIANCE.NS - Price: ₹2,450.75
[2024-01-15 09:42:18] 📈 BUY SIGNAL: TCS.NS at ₹3,520.50 (Breakout detected)
[2024-01-15 10:15:33] 💰 PROFIT: TCS.NS sold at ₹3,555.25 (+0.99% profit)
[2024-01-15 11:30:45] 📊 Current P&L: +₹2,450 (+2.45%)
```

## Output Files

### Trading Logs
- `data/logs/paper_trading_YYYY-MM-DD.log` - Detailed trading log
- `data/backtests/paper_results_YYYY-MM-DD.json` - Trade results summary

### Performance Reports
- `data/backtests/performance_report.html` - Visual performance report
- `data/backtests/trades_summary.csv` - All trades in CSV format

## Monitoring Your Paper Trading

### 1. Check Trade Performance
```bash
tail -f data/logs/paper_trading_$(date +%Y-%m-%d).log
```

### 2. View Real-time Stats
The bot displays:
- Current portfolio value
- Open positions
- Profit/Loss for the day
- Number of trades executed
- Win rate and average profit per trade

### 3. Stop the Bot
Press `Ctrl+C` to gracefully stop the bot. It will:
- Close all open positions
- Save final results
- Generate performance report

## Understanding the Strategy

### Entry Conditions (BUY)
- Price breaks above recent resistance level
- Volume surge (1.5x average volume)
- RSI between 40-70 (not overbought)
- Market hours: 9:30 AM - 3:00 PM IST

### Exit Conditions (SELL)
- **Take Profit**: +1.5% gain
- **Stop Loss**: -1.0% loss
- **Time Exit**: End of trading day
- **Technical Exit**: Momentum reversal

### Risk Management
- Maximum 2% risk per trade
- Maximum 5 open positions
- Daily loss limit: 5% of capital
- Position size based on volatility (ATR)

## Configuration Optimization

### For Conservative Trading
```yaml
strategy:
  balanced_breakout:
    stop_loss_pct: 0.8      # Tighter stop loss
    take_profit_pct: 1.2    # Lower take profit
    risk_per_trade: 0.015   # Lower risk per trade
    max_positions: 3        # Fewer positions
```

### For Aggressive Trading
```yaml
strategy:
  balanced_breakout:
    stop_loss_pct: 1.5      # Wider stop loss
    take_profit_pct: 2.5    # Higher take profit
    risk_per_trade: 0.025   # Higher risk per trade
    max_positions: 8        # More positions
```

## Troubleshooting

### Common Issues

1. **"No data available"**
   ```bash
   # Check internet connection and try:
   python -c "import yfinance; print(yfinance.download('RELIANCE.NS', period='1d'))"
   ```

2. **"Module not found"**
   ```bash
   # Ensure you're in the right directory:
   cd /workspaces/Intradar-bot
   export PYTHONPATH=$PYTHONPATH:/workspaces/Intradar-bot
   ```

3. **"No trading signals"**
   - Market might be ranging (no breakouts)
   - Try running during market hours (9:30 AM - 3:30 PM IST)
   - Check if selected stocks have sufficient volume

### Getting Help
```bash
python main_runner.py --help
python demo_paper_trading.py --help
```

## Next Steps

### After Successful Paper Trading:
1. **Analyze Results**: Review the generated reports
2. **Optimize Parameters**: Adjust strategy parameters based on performance
3. **Extended Testing**: Run for multiple days to validate consistency
4. **Prepare for Live**: Set up Fyers broker credentials for live trading

### Performance Benchmarks:
- **Target Daily Return**: 0.5% - 2.0%
- **Win Rate**: > 55%
- **Maximum Drawdown**: < 5%
- **Sharpe Ratio**: > 1.5

## Ready to Start?

Run this command to begin paper trading:
```bash
cd /workspaces/Intradar-bot
python demo_paper_trading.py
```

The system will guide you through the process and show real-time results! 🚀
