#!/usr/bin/env python3
import sys
sys.path.append('src')
import backtrader as bt
import yaml
from pathlib import Path
from strategies.price_action_breakout import PriceActionBreakout
from data.providers.yfinance_provider import YFinanceProvider

# Modified strategy with looser parameters
class DebugBreakout(PriceActionBreakout):
    params = (
        ('lookback_period', 10),        # Shorter lookback
        ('volume_threshold', 1.1),      # Lower volume requirement
        ('atr_period', 14),
        ('stop_loss_atr', 1.5),
        ('take_profit_atr', 2.0),       # Closer target
        ('risk_per_trade', 0.02),
        ('min_breakout_pct', 0.1),      # Much lower breakout requirement
        ('pull_back_bars', 3),
        ('volume_ma_period', 20),
    )
    
    def next(self):
        # Add debug prints
        if len(self.data) < self.params.lookback_period:
            return
            
        current_time = self.data.datetime.time(0)
        if (current_time.hour == 9 and current_time.minute < 60) or current_time.hour >= 15:
            return
            
        if self.position or self.order:
            return
            
        # Debug breakout detection
        direction, level = self.detect_breakout()
        if len(self.data) % 50 == 0:  # Print every 50 bars
            print(f"Time: {current_time}, Close: {self.dataclose[0]:.2f}, "
                  f"Resistance: {self.resistance[0]:.2f}, Support: {self.support[0]:.2f}, "
                  f"Volume: {self.datavolume[0]:.0f}, Volume MA: {self.volume_ma[0]:.0f}")
        
        if direction != 0:
            print(f"�� BREAKOUT DETECTED! Direction: {direction}, Level: {level}")
            super().next()
        
def main():
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100000)
    cerebro.broker.setcommission(commission=0.001)
    
    cerebro.addstrategy(DebugBreakout)
    
    provider = YFinanceProvider()
    data = provider.get_data('TSLA', period='5d', interval='5m')
    
    if data is not None and len(data) > 50:
        feed = bt.feeds.PandasData(dataname=data, name='TSLA')
        cerebro.adddata(feed)
        print(f"✅ Testing with {len(data)} bars")
        
        results = cerebro.run()
        
        final_value = cerebro.broker.getvalue()
        print(f"Final Value: ${final_value:,.2f}")

if __name__ == "__main__":
    main()
