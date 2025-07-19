#!/usr/bin/env python3
import sys
sys.path.append("src")
import backtrader as bt
from strategies.momentum_breakout import MomentumBreakout
from data.providers.yfinance_provider import YFinanceProvider

def main():
    print("🚀 Testing MOMENTUM Breakout Strategy (More Selective)")
    
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100000)
    cerebro.broker.setcommission(commission=0.001)
    
    cerebro.addstrategy(MomentumBreakout)
    
    provider = YFinanceProvider()
    data = provider.get_data("SOXL", period="10d", interval="5m")
    
    if data is not None:
        feed = bt.feeds.PandasData(dataname=data, name="SOXL")
        cerebro.adddata(feed)
        
        print(f"📊 Testing SOXL with {len(data)} bars")
        
        results = cerebro.run()

if __name__ == "__main__":
    main()

