#!/usr/bin/env python3
import sys
sys.path.append("src")
import backtrader as bt
from strategies.simple_breakout import SimpleBreakout
from data.providers.yfinance_provider import YFinanceProvider

def test_fixed_strategy():
    print("🚀 Testing FIXED Strategy (No Division Errors)")
    
    symbols = ["SOXL", "TQQQ", "TNA", "LABU", "TSLA"]
    provider = YFinanceProvider()
    total_pnl = 0
    total_trades = 0
    
    for symbol in symbols:
        print(f"\n📊 Testing {symbol}...")
        
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(100000)
        cerebro.broker.setcommission(commission=0.001)
        cerebro.addstrategy(SimpleBreakout)
        
        data = provider.get_data(symbol, period="10d", interval="5m")
        
        if data is not None and len(data) > 50:
            feed = bt.feeds.PandasData(dataname=data, name=symbol)
            cerebro.adddata(feed)
            
            results = cerebro.run()
            strat = results[0]
            
            total_pnl += strat.total_pnl
            total_trades += strat.trade_count
            
            print(f"✅ {symbol}: ${strat.total_pnl:.2f} | {strat.trade_count} trades")
    
    daily_profit = total_pnl / 10
    daily_return = (total_pnl / (100000 * len(symbols))) * 100 / 10
    
    print(f"\n🏆 PORTFOLIO RESULTS:")
    print(f"💰 Daily Profit: ${daily_profit:.2f}")
    print(f"📈 Daily Return: {daily_return:+.2f}%")
    print(f"🎯 Total Trades: {total_trades}")

if __name__ == "__main__":
    test_fixed_strategy()

