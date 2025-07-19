#!/usr/bin/env python3
import sys
sys.path.append("src")
import backtrader as bt
from strategies.fixed_breakout import FixedBreakout
from data.providers.yfinance_provider import YFinanceProvider

def main():
    print("🚀 Testing Fixed Breakout Strategy")
    
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100000)
    cerebro.broker.setcommission(commission=0.001)
    
    cerebro.addstrategy(FixedBreakout)
    
    provider = YFinanceProvider()
    data = provider.get_data("SOXL", period="10d", interval="5m")
    
    if data is not None:
        feed = bt.feeds.PandasData(dataname=data, name="SOXL")
        cerebro.adddata(feed)
        
        print(f"📊 Testing SOXL with {len(data)} bars")
        initial_value = cerebro.broker.getvalue()
        
        results = cerebro.run()
        
        final_value = cerebro.broker.getvalue()
        total_return = (final_value / initial_value - 1) * 100
        daily_return = total_return / 10
        
        print(f"📊 FINAL RESULTS:")
        print(f"💰 Total Return: {total_return:+.2f}%")
        print(f"📈 Daily Avg: {daily_return:+.2f}%")
        
        if daily_return >= 1.0:
            print("🎯 TARGET ACHIEVED! 1%+ daily return!")
        elif daily_return >= 0.5:
            print("📈 Good progress, need optimization")
        else:
            print("📉 Need parameter tuning")

if __name__ == "__main__":
    main()

