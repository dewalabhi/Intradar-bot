#!/usr/bin/env python3
"""
🎯 SIMPLE PAPER TRADING DEMO
============================
Quick demo to show paper trading in action
"""

import sys
import os
sys.path.append('/workspaces/Intradar-bot')

import backtrader as bt
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

class SimplePaperTradingStrategy(bt.Strategy):
    """Simple strategy for paper trading demo"""
    
    params = (
        ('period', 14),
        ('stop_loss', 0.02),  # 2% stop loss
        ('take_profit', 0.03),  # 3% take profit
    )
    
    def __init__(self):
        # Simple moving average crossover
        self.sma_short = bt.indicators.SimpleMovingAverage(self.data.close, period=5)
        self.sma_long = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.period)
        self.crossover = bt.indicators.CrossOver(self.sma_short, self.sma_long)
        
        # Track orders and trades
        self.order = None
        self.trade_count = 0
        
    def next(self):
        # Check if we have an order pending
        if self.order:
            return
        
        # Check if we are in the market
        if not self.position:
            # Not in the market, look for buy signal
            if self.crossover > 0:  # Short MA crosses above Long MA
                # Calculate position size (risk 2% of capital)
                price = self.data.close[0]
                risk_amount = self.broker.getcash() * 0.02
                stop_loss_price = price * (1 - self.params.stop_loss)
                risk_per_share = price - stop_loss_price
                
                if risk_per_share > 0:
                    size = int(risk_amount / risk_per_share)
                    if size > 0:
                        self.order = self.buy(size=size)
                        self.log(f'BUY ORDER: {size} shares at ₹{price:.2f}')
        else:
            # In the market, check exit conditions
            current_price = self.data.close[0]
            entry_price = self.position.price
            
            # Calculate profit/loss percentage
            pnl_pct = (current_price - entry_price) / entry_price
            
            # Take profit condition
            if pnl_pct >= self.params.take_profit:
                self.order = self.close()
                self.log(f'TAKE PROFIT: Closing position at ₹{current_price:.2f} (+{pnl_pct*100:.2f}%)')
            
            # Stop loss condition
            elif pnl_pct <= -self.params.stop_loss:
                self.order = self.close()
                self.log(f'STOP LOSS: Closing position at ₹{current_price:.2f} ({pnl_pct*100:.2f}%)')
            
            # Crossover exit (trend reversal)
            elif self.crossover < 0:
                self.order = self.close()
                self.log(f'TREND EXIT: Closing position at ₹{current_price:.2f} ({pnl_pct*100:.2f}%)')
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED: {order.executed.size} shares at ₹{order.executed.price:.2f}')
            elif order.issell():
                self.log(f'SELL EXECUTED: {order.executed.size} shares at ₹{order.executed.price:.2f}')
                self.trade_count += 1
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'ORDER FAILED: {order.status}')
        
        self.order = None
    
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        
        self.log(f'TRADE CLOSED: Profit/Loss ₹{trade.pnl:.2f} ({trade.pnlcomm:.2f}% ROI)')
    
    def log(self, txt):
        """Logging function with timestamp"""
        dt = self.datas[0].datetime.datetime(0)
        print(f'[{dt.strftime("%Y-%m-%d %H:%M")}] {txt}')

def run_paper_trading_demo():
    """Run the paper trading demonstration"""
    print("🚀 PAPER TRADING DEMO")
    print("=" * 40)
    print("Fetching market data...")
    
    # Get market data for RELIANCE (NSE)
    try:
        ticker = "RELIANCE.NS"
        data = yf.download(ticker, period="30d", interval="1h")
        
        if data.empty:
            print("❌ No data received. Trying backup ticker...")
            ticker = "AAPL"  # Fallback to Apple
            data = yf.download(ticker, period="30d", interval="1h")
        
        if data.empty:
            print("❌ Unable to fetch market data. Check internet connection.")
            return
        
        # Fix column names if they are MultiIndex
        if hasattr(data.columns, 'levels'):
            data.columns = [col[0].lower() for col in data.columns]
        else:
            data.columns = [col.lower() for col in data.columns]
        
        print(f"✅ Data fetched for {ticker}: {len(data)} bars")
        print(f"📊 Date range: {data.index[0]} to {data.index[-1]}")
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return
    
    # Initialize Backtrader
    cerebro = bt.Cerebro()
    
    # Add strategy
    cerebro.addstrategy(SimplePaperTradingStrategy)
    
    # Create data feed
    # Column names should already be fixed above
    data_feed = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(data_feed)
    
    # Set initial capital
    initial_cash = 100000  # ₹1,00,000
    cerebro.broker.setcash(initial_cash)
    
    # Set commission (0.1% per trade)
    cerebro.broker.setcommission(commission=0.001)
    
    print(f"💰 Starting capital: ₹{initial_cash:,.2f}")
    print(f"📈 Running strategy on {ticker}...")
    print("-" * 40)
    
    # Run the backtest
    result = cerebro.run()
    
    # Final results
    final_value = cerebro.broker.getvalue()
    total_return = ((final_value - initial_cash) / initial_cash) * 100
    
    print("-" * 40)
    print("📊 PAPER TRADING RESULTS")
    print("=" * 40)
    print(f"💰 Starting Capital: ₹{initial_cash:,.2f}")
    print(f"💰 Final Value: ₹{final_value:,.2f}")
    print(f"📈 Total Return: {total_return:.2f}%")
    print(f"💵 Profit/Loss: ₹{final_value - initial_cash:,.2f}")
    
    if total_return > 0:
        print("✅ Paper trading was PROFITABLE! 🎉")
    else:
        print("⚠️  Paper trading showed losses. Review strategy parameters.")
    
    print("\n🔍 Key Takeaways:")
    print("- This is a SIMULATION - no real money was used")
    print("- Results depend on market conditions and strategy parameters")
    print("- Test with different stocks and time periods")
    print("- Optimize parameters before live trading")
    
    print(f"\n🚀 Ready to trade live? Configure Fyers credentials in config.yaml")
    
    return final_value, total_return

if __name__ == "__main__":
    try:
        run_paper_trading_demo()
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped by user")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("💡 Try running: python system_check.py first")
