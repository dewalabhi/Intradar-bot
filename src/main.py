#!/usr/bin/env python3
import sys
sys.path.append('src')

import backtrader as bt
import yaml
from pathlib import Path

# Import strategies
from strategies.price_action_breakout import PriceActionBreakout
from data.providers.yfinance_provider import YFinanceProvider

def load_config():
    with open('config/config.yaml', 'r') as f:
        return yaml.safe_load(f)

def main():
    print("🤖 Price Action Trading Bot")
    print("=" * 40)
    
    # Load config
    config = load_config()
    
    # Setup Cerebro
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100000)
    cerebro.broker.setcommission(commission=0.001)
    
    # Add Price Action strategy
    cerebro.addstrategy(PriceActionBreakout)
    print("🔥 Added Price Action Breakout strategy")
    
    # Get data
    provider = YFinanceProvider()
    symbol = 'TSLA'
    
    print(f"📡 Loading data for {symbol}...")
    data = provider.get_data(symbol, period='10d', interval='5m')
    
    if data is not None and len(data) > 50:
        feed = bt.feeds.PandasData(dataname=data, name=symbol)
        cerebro.adddata(feed)
        print(f"✅ Added {len(data)} bars for {symbol}")
        
        # Run backtest
        initial_value = cerebro.broker.getvalue()
        print(f"💰 Starting: ${initial_value:,.2f}")
        print("🔄 Running backtest...\n")
        
        results = cerebro.run()
        
        final_value = cerebro.broker.getvalue()
        total_return = (final_value / initial_value - 1) * 100
        
        print("\n" + "=" * 40)
        print("📊 RESULTS")
        print("=" * 40)
        print(f"Starting Value: ${initial_value:,.2f}")
        print(f"Final Value:    ${final_value:,.2f}")
        print(f"Total Return:   {total_return:+.2f}%")
        print("=" * 40)
        
    else:
        print("❌ Failed to load data")

if __name__ == "__main__":
    main()
