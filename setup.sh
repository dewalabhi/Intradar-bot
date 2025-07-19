#!/bin/bash

echo "🚀 Setting up Professional Trading Bot..."

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p config/strategies
mkdir -p src/{bot,strategies,data/{providers,storage},brokers,utils,analysis}
mkdir -p tests scripts data/{historical,backtests,logs} docs .github/workflows

# Create requirements.txt
echo "📦 Creating requirements.txt..."
cat > requirements.txt << 'EOF'
# Core trading and data libraries
backtrader==1.9.78.123
yfinance==0.2.18
alpaca-trade-api==3.1.1
pandas==2.0.3
numpy==1.24.3

# Configuration and utilities
PyYAML==6.0.1
python-dotenv==1.0.0

# Visualization and analysis
matplotlib==3.7.2

# Development and testing
pytest==7.4.0
EOF

# Create main configuration
echo "⚙️ Creating configuration files..."
cat > config/config.yaml << 'EOF'
# Trading Bot Configuration
trading:
  mode: paper  # paper, live, backtest
  initial_cash: 100000
  symbols:
    - AAPL
    - MSFT
    - GOOGL
    - TSLA
    - SPY
  max_positions: 5
  risk_per_trade: 0.02  # 2% risk per trade

data:
  provider: yfinance
  timeframe: 1d  # Daily bars
  history_days: 252

strategies:
  ma_crossover:
    enabled: true
    fast_period: 10
    slow_period: 30
    ma_type: EMA
    
  rsi_mean_reversion:
    enabled: false
    rsi_period: 14
    oversold: 30
    overbought: 70

logging:
  level: INFO
  file: data/logs/trading_bot.log
EOF

# Create __init__.py files
echo "🐍 Creating Python package files..."
touch src/__init__.py
touch src/strategies/__init__.py
touch src/data/__init__.py
touch src/data/providers/__init__.py
touch src/brokers/__init__.py
touch src/utils/__init__.py

# Create Moving Average Crossover Strategy
echo "📈 Creating MA Crossover Strategy..."
cat > src/strategies/ma_crossover.py << 'EOF'
"""
Moving Average Crossover Strategy
A classic trend-following strategy using dual moving averages.
"""

import backtrader as bt


class MovingAverageCrossover(bt.Strategy):
    """Simple Moving Average Crossover Strategy"""
    
    params = (
        ('fast_period', 10),
        ('slow_period', 30),
        ('ma_type', 'EMA'),
        ('enabled', True),
    )
    
    def __init__(self):
        """Initialize strategy indicators"""
        
        # Create moving averages based on type
        if self.params.ma_type == 'EMA':
            self.fast_ma = bt.indicators.ExponentialMovingAverage(
                self.data.close, period=self.params.fast_period
            )
            self.slow_ma = bt.indicators.ExponentialMovingAverage(
                self.data.close, period=self.params.slow_period
            )
        else:  # SMA
            self.fast_ma = bt.indicators.SimpleMovingAverage(
                self.data.close, period=self.params.fast_period
            )
            self.slow_ma = bt.indicators.SimpleMovingAverage(
                self.data.close, period=self.params.slow_period
            )
        
        # Create crossover signal
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        
        # Track orders and trades
        self.order = None
        self.trade_count = 0
    
    def log(self, txt, dt=None):
        """Logging function for strategy events"""
        dt = dt or self.datas[0].datetime.date(0)
        symbol = self.data._name if hasattr(self.data, '_name') else 'Unknown'
        print(f'{dt.isoformat()} [{symbol}] {txt}')
    
    def notify_order(self, order):
        """Handle order notifications"""
        if order.status in [order.Submitted, order.Accepted]:
            # Order submitted/accepted - nothing to do
            return

        # Check if order is completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED: Price: {order.executed.price:.2f}, '
                        f'Size: {order.executed.size}, '
                        f'Cost: {order.executed.value:.2f}, '
                        f'Comm: {order.executed.comm:.2f}')
            else:
                self.log(f'SELL EXECUTED: Price: {order.executed.price:.2f}, '
                        f'Size: {order.executed.size}, '
                        f'Cost: {order.executed.value:.2f}, '
                        f'Comm: {order.executed.comm:.2f}')

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'Order Canceled/Margin/Rejected: {order.status}')

        # Reset order
        self.order = None

    def notify_trade(self, trade):
        """Handle trade notifications"""
        if not trade.isclosed:
            return

        self.trade_count += 1
        pnl_pct = (trade.pnl / trade.price) * 100 if trade.price != 0 else 0
        
        self.log(f'TRADE #{self.trade_count} CLOSED: '
                f'PnL: ${trade.pnl:.2f} ({pnl_pct:.2f}%), '
                f'Gross: ${trade.pnlcomm:.2f}')

    def next(self):
        """Main strategy logic - called for each bar"""
        
        # Skip if we have a pending order
        if self.order:
            return

        # Check if we're in the market
        if not self.position:
            # Look for buy signal: fast MA crosses above slow MA
            if self.crossover > 0:
                self.log(f'BUY SIGNAL: Fast MA crosses above Slow MA')
                self.log(f'Fast MA: {self.fast_ma[0]:.2f}, Slow MA: {self.slow_ma[0]:.2f}')
                
                # Calculate position size (use 95% of available cash)
                available_cash = self.broker.getcash()
                price = self.data.close[0]
                size = int((available_cash * 0.95) / price)
                
                if size > 0:
                    self.order = self.buy(size=size)
        else:
            # Look for sell signal: fast MA crosses below slow MA
            if self.crossover < 0:
                self.log(f'SELL SIGNAL: Fast MA crosses below Slow MA')
                self.log(f'Fast MA: {self.fast_ma[0]:.2f}, Slow MA: {self.slow_ma[0]:.2f}')
                
                # Close position
                self.order = self.close()

    def stop(self):
        """Called when strategy stops"""
        self.log(f'Strategy finished with {self.trade_count} trades')
        final_value = self.broker.getvalue()
        self.log(f'Final Portfolio Value: ${final_value:,.2f}')
EOF

# Create RSI Mean Reversion Strategy
echo "📊 Creating RSI Mean Reversion Strategy..."
cat > src/strategies/rsi_mean_reversion.py << 'EOF'
"""
RSI Mean Reversion Strategy
Buys when RSI is oversold and sells when RSI is overbought.
"""

import backtrader as bt


class RSIMeanReversion(bt.Strategy):
    """RSI Mean Reversion Strategy"""
    
    params = (
        ('rsi_period', 14),
        ('oversold', 30),
        ('overbought', 70),
        ('enabled', True),
    )
    
    def __init__(self):
        """Initialize strategy indicators"""
        
        # RSI indicator
        self.rsi = bt.indicators.RelativeStrengthIndex(
            self.data.close, period=self.params.rsi_period
        )
        
        # Track orders
        self.order = None
        self.trade_count = 0
    
    def log(self, txt, dt=None):
        """Logging function"""
        dt = dt or self.datas[0].datetime.date(0)
        symbol = self.data._name if hasattr(self.data, '_name') else 'Unknown'
        print(f'{dt.isoformat()} [{symbol}] {txt}')
    
    def notify_order(self, order):
        """Handle order notifications"""
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED: Price: {order.executed.price:.2f}')
            else:
                self.log(f'SELL EXECUTED: Price: {order.executed.price:.2f}')
        
        self.order = None
    
    def notify_trade(self, trade):
        """Handle trade notifications"""
        if trade.isclosed:
            self.trade_count += 1
            self.log(f'TRADE CLOSED: PnL: ${trade.pnl:.2f}')
    
    def next(self):
        """Main strategy logic"""
        
        if self.order:
            return
        
        current_rsi = self.rsi[0]
        
        if not self.position:
            # Buy when RSI is oversold
            if current_rsi < self.params.oversold:
                self.log(f'BUY SIGNAL: RSI Oversold ({current_rsi:.1f})')
                
                available_cash = self.broker.getcash()
                price = self.data.close[0]
                size = int((available_cash * 0.95) / price)
                
                if size > 0:
                    self.order = self.buy(size=size)
        
        else:
            # Sell when RSI is overbought
            if current_rsi > self.params.overbought:
                self.log(f'SELL SIGNAL: RSI Overbought ({current_rsi:.1f})')
                self.order = self.close()
EOF

# Create YFinance Data Provider
echo "📡 Creating YFinance Data Provider..."
cat > src/data/providers/yfinance_provider.py << 'EOF'
"""
Yahoo Finance Data Provider
Provides historical and real-time stock market data using yfinance.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


class YFinanceProvider:
    """Yahoo Finance data provider for stock market data"""
    
    def __init__(self):
        self.name = "YFinance"
    
    def get_data(self, symbol, period='1y', interval='1d'):
        """
        Get historical data for a symbol
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            period (str): Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            interval (str): Data interval ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
        
        Returns:
            pandas.DataFrame: OHLCV data with standard column names
        """
        try:
            print(f"📊 Fetching data for {symbol}...")
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                print(f"❌ No data found for symbol: {symbol}")
                return None
            
            # Clean up the data
            data = data.dropna()
            
            # Ensure we have the required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in data.columns for col in required_columns):
                print(f"❌ Missing required columns for {symbol}")
                return None
            
            print(f"✅ Successfully fetched {len(data)} bars for {symbol}")
            return data
            
        except Exception as e:
            print(f"❌ Error fetching data for {symbol}: {e}")
            return None
    
    def get_real_time_price(self, symbol):
        """Get current price for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d', interval='1m')
            if not data.empty:
                return data['Close'].iloc[-1]
            return None
        except Exception as e:
            print(f"❌ Error fetching real-time price for {symbol}: {e}")
            return None
    
    def get_multiple_symbols(self, symbols, period='1y', interval='1d'):
        """Get data for multiple symbols"""
        results = {}
        for symbol in symbols:
            data = self.get_data(symbol, period, interval)
            if data is not None:
                results[symbol] = data
        return results
EOF

# Create main trading bot
echo "🤖 Creating main trading bot..."
cat > src/main.py << 'EOF'
#!/usr/bin/env python3
"""
Professional Trading Bot - Main Entry Point
A comprehensive intraday trading bot with multiple strategies and risk management.
"""

import sys
import yaml
import argparse
from pathlib import Path
import backtrader as bt

# Add src to Python path
sys.path.append(str(Path(__file__).parent))

# Import strategies
from strategies.ma_crossover import MovingAverageCrossover
from strategies.rsi_mean_reversion import RSIMeanReversion

# Import data providers
from data.providers.yfinance_provider import YFinanceProvider


class TradingBot:
    """Main trading bot orchestrator"""
    
    def __init__(self, config_path="config/config.yaml"):
        """Initialize the trading bot"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.cerebro = None
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            print(f"✅ Loaded configuration from {self.config_path}")
            return config
        except Exception as e:
            print(f"❌ Error loading configuration: {e}")
            sys.exit(1)
    
    def setup_cerebro(self):
        """Setup Backtrader Cerebro engine"""
        print("🧠 Setting up Cerebro engine...")
        
        self.cerebro = bt.Cerebro()
        
        # Set initial cash
        initial_cash = self.config['trading']['initial_cash']
        self.cerebro.broker.setcash(initial_cash)
        print(f"💰 Initial cash: ${initial_cash:,}")
        
        # Set commission (0.1% default)
        commission = self.config['trading'].get('commission', 0.001)
        self.cerebro.broker.setcommission(commission=commission)
        print(f"💸 Commission: {commission*100:.3f}%")
        
        # Add strategies
        strategies_added = 0
        
        # MA Crossover Strategy
        if self.config['strategies']['ma_crossover']['enabled']:
            strategy_params = {k: v for k, v in self.config['strategies']['ma_crossover'].items() 
                             if k != 'enabled'}
            self.cerebro.addstrategy(MovingAverageCrossover, **strategy_params)
            print("📈 Added Moving Average Crossover strategy")
            strategies_added += 1
            
        # RSI Mean Reversion Strategy
        if self.config['strategies']['rsi_mean_reversion']['enabled']:
            strategy_params = {k: v for k, v in self.config['strategies']['rsi_mean_reversion'].items() 
                             if k != 'enabled'}
            self.cerebro.addstrategy(RSIMeanReversion, **strategy_params)
            print("📊 Added RSI Mean Reversion strategy")
            strategies_added += 1
        
        if strategies_added == 0:
            print("❌ No strategies enabled in configuration!")
            sys.exit(1)
        
        # Add analyzers for performance metrics
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        
        print(f"✅ Cerebro setup complete with {strategies_added} strategies")
    
    def add_data(self, symbols):
        """Add data feeds for specified symbols"""
        print(f"📡 Adding data for symbols: {symbols}")
        
        provider = YFinanceProvider()
        data_feeds_added = 0
        
        for symbol in symbols:
            try:
                # Get historical data
                data = provider.get_data(
                    symbol=symbol,
                    period='2y',  # 2 years of data for better backtesting
                    interval='1d'  # Daily bars
                )
                
                if data is not None and len(data) > 100:  # Ensure sufficient data
                    # Convert to Backtrader data feed
                    data_feed = bt.feeds.PandasData(
                        dataname=data,
                        name=symbol,
                        plot=False  # Don't plot by default
                    )
                    self.cerebro.adddata(data_feed)
                    print(f"✅ Added {len(data)} bars for {symbol}")
                    data_feeds_added += 1
                else:
                    print(f"❌ Insufficient data for {symbol}")
                    
            except Exception as e:
                print(f"❌ Error adding data for {symbol}: {e}")
        
        if data_feeds_added == 0:
            print("❌ No data feeds added!")
            sys.exit(1)
        
        print(f"✅ Successfully added {data_feeds_added} data feeds")
        return data_feeds_added
    
    def run_backtest(self, symbols=None):
        """Run backtest with specified symbols"""
        print("🚀 Starting Trading Bot Backtest...")
        print("=" * 60)
        
        # Use symbols from config if not provided
        if symbols is None:
            symbols = self.config['trading']['symbols']
        
        # Setup Cerebro
        self.setup_cerebro()
        
        # Add data
        self.add_data(symbols)
        
        # Print starting info
        initial_value = self.cerebro.broker.getvalue()
        print(f"\n💰 Starting Portfolio Value: ${initial_value:,.2f}")
        print(f"📊 Symbols: {', '.join(symbols)}")
        print(f"📈 Strategies: {[k for k, v in self.config['strategies'].items() if v.get('enabled', False)]}")
        print("\n" + "=" * 60)
        print("🔄 Running backtest...\n")
        
        # Run the backtest
        try:
            results = self.cerebro.run()
            final_value = self.cerebro.broker.getvalue()
            
            print("\n" + "=" * 60)
            print(f"💰 Final Portfolio Value: ${final_value:,.2f}")
            
            # Print detailed results
            self.print_results(results[0], initial_value, final_value)
            
            return results
            
        except Exception as e:
            print(f"❌ Error during backtest: {e}")
            return None
    
    def print_results(self, result, initial_value, final_value):
        """Print comprehensive backtest results"""
        print("\n" + "=" * 60)
        print("📊 DETAILED BACKTEST RESULTS")
        print("=" * 60)
        
        # Basic Performance Metrics
        total_return = (final_value / initial_value - 1) * 100
        profit_loss = final_value - initial_value
        
        print(f"\n💵 PERFORMANCE SUMMARY")
        print(f"   Initial Value:     ${initial_value:,.2f}")
        print(f"   Final Value:       ${final_value:,.2f}")
        print(f"   Total Return:      {total_return:+.2f}%")
        print(f"   Profit/Loss:       ${profit_loss:+,.2f}")
        
        # Risk Metrics
        try:
            sharpe = result.analyzers.sharpe.get_analysis()
            sharpe_ratio = sharpe.get('sharperatio')
            if sharpe_ratio is not None:
                print(f"   Sharpe Ratio:      {sharpe_ratio:.2f}")
            else:
                print(f"   Sharpe Ratio:      N/A")
        except:
            print(f"   Sharpe Ratio:      N/A")
        
        try:
            drawdown = result.analyzers.drawdown.get_analysis()
            max_dd = drawdown.get('max', {}).get('drawdown', 0)
            print(f"   Max Drawdown:      {max_dd:.2f}%")
        except:
            print(f"   Max Drawdown:      N/A")
        
        # Trade Analysis
        try:
            trades = result.analyzers.trades.get_analysis()
            total_trades = trades.get('total', {}).get('total', 0)
            won_trades = trades.get('won', {}).get('total', 0)
            lost_trades = trades.get('lost', {}).get('total', 0)
            
            if total_trades > 0:
                win_rate = (won_trades / total_trades) * 100
                
                print(f"\n🎯 TRADING STATISTICS")
                print(f"   Total Trades:      {total_trades}")
                print(f"   Winning Trades:    {won_trades}")
                print(f"   Losing Trades:     {lost_trades}")
                print(f"   Win Rate:          {win_rate:.1f}%")
                
                # PnL Analysis
                avg_win = trades.get('won', {}).get('pnl', {}).get('average', 0)
                avg_loss = trades.get('lost', {}).get('pnl', {}).get('average', 0)
                
                if avg_win > 0:
                    print(f"   Average Win:       ${avg_win:.2f}")
                if avg_loss < 0:
                    print(f"   Average Loss:      ${avg_loss:.2f}")
                
                if avg_loss != 0:
                    profit_factor = abs(avg_win / avg_loss)
                    print(f"   Profit Factor:     {profit_factor:.2f}")
            else:
                print(f"\n🎯 TRADING STATISTICS")
                print(f"   No trades executed")
        except Exception as e:
            print(f"\n🎯 TRADING STATISTICS")
            print(f"   Error analyzing trades: {e}")
        
        # Performance Rating
        print(f"\n⭐ PERFORMANCE RATING")
        if total_return > 15:
            print(f"   Rating: ⭐⭐⭐⭐⭐ Excellent!")
        elif total_return > 10:
            print(f"   Rating: ⭐⭐⭐⭐ Very Good")
        elif total_return > 5:
            print(f"   Rating: ⭐⭐⭐ Good")
        elif total_return > 0:
            print(f"   Rating: ⭐⭐ Fair")
        else:
            print(f"   Rating: ⭐ Needs Improvement")
        
        print("\n" + "=" * 60)
    
    def run_paper_trading(self):
        """Run paper trading mode"""
        print("📝 Paper trading mode not yet implemented")
        print("This feature will be added in the next version!")
    
    def run_live_trading(self):
        """Run live trading mode"""
        print("⚠️  Live trading mode not yet implemented")
        print("Please test thoroughly with backtesting and paper trading first!")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Professional Trading Bot")
    parser.add_argument(
        '--mode', 
        choices=['backtest', 'paper', 'live'], 
        default='backtest',
        help='Trading mode (default: backtest)'
    )
    parser.add_argument(
        '--config', 
        default='config/config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--symbols',
        nargs='+',
        help='Symbols to trade (overrides config)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    print("🤖 Professional Trading Bot v1.0")
    print("=" * 60)
    
    # Parse arguments
    args = parse_arguments()
    
    # Create trading bot
    try:
        bot = TradingBot(config_path=args.config)
    except Exception as e:
        print(f"❌ Failed to initialize bot: {e}")
        return
    
    # Override symbols if provided
    symbols = args.symbols if args.symbols else None
    
    # Run based on mode
    if args.mode == 'backtest':
        bot.run_backtest(symbols=symbols)
    elif args.mode == 'paper':
        bot.run_paper_trading()
    elif args.mode == 'live':
        bot.run_live_trading()


if __name__ == "__main__":
    main()
EOF

# Create a simple test script
echo "🧪 Creating test script..."
cat > test_bot.py << 'EOF'
#!/usr/bin/env python3
"""
Quick test script for the trading bot
"""

from src.main import TradingBot

def main():
    print("🧪 Testing Trading Bot...")
    
    # Create bot
    bot = TradingBot()
    
    # Test with a single symbol
    print("📊 Running quick test with AAPL...")
    bot.run_backtest(symbols=['AAPL'])

if __name__ == "__main__":
    main()
EOF

# Create README
echo "📚 Creating README..."
cat > README.md << 'EOF'
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
EOF

# Make scripts executable
chmod +x src/main.py
chmod +x test_bot.py

echo ""
echo "🎉 Trading Bot Setup Complete!"
echo "="*50
echo ""
echo "✅ Project structure created"
echo "✅ Configuration files ready"
echo "✅ Trading strategies implemented"
echo "✅ Data providers configured"
echo "✅ Main bot application ready"
echo ""
echo "🚀 Next Steps:"
echo "1. Install dependencies: pip install -r requirements.txt"
echo "2. Run quick test: python test_bot.py"
echo "3. Run full backtest: python src/main.py"
echo ""
echo "💡 Tip: Edit config/config.yaml to customize your bot!"
echo ""
EOF

# Make the setup script executable
chmod +x setup.sh

echo "📋 Setup script created! Now run it:"
echo ""
echo "bash setup.sh"