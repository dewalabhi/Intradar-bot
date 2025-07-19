#!/usr/bin/env python3
import sys
sys.path.append('src')
import backtrader as bt
from strategies.aggressive_breakout import AggressiveBreakout
from data.providers.yfinance_provider import YFinanceProvider

def main():
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100000)
    cerebro.broker.setcommission(commission=0.001)
    
    cerebro.addstrategy(AggressiveBreakout)
    
    provider = YFinanceProvider()
    # Test SOXL (highest volatility)
    data = provider.get_data('SOXL', period='5d', interval='5m')
    
    if data is not None:
        feed = bt.feeds.PandasData(dataname=data, name='SOXL')
        cerebro.adddata(feed)
        
        print(f"🚀 Testing SOXL with {len(data)} bars")
        initial_value = cerebro.broker.getvalue()
        
        results = cerebro.run()
        
        final_value = cerebro.broker.getvalue()
        total_return = (final_value / initial_value - 1) * 100
        print(f"📊 FINAL: ${final_value:,.2f} ({total_return:+.2f}%)")

if __name__ == "__main__":
    main()
