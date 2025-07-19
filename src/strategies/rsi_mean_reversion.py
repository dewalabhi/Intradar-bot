"""
Fixed Intraday RSI Strategy
"""

import backtrader as bt
from datetime import time


class RSIMeanReversion(bt.Strategy):
    
    params = (
        ('rsi_period', 9),
        ('oversold', 40),
        ('overbought', 60),
        ('enabled', True),
    )
    
    def __init__(self):
        self.rsi = bt.indicators.RelativeStrengthIndex(
            self.data.close, period=self.params.rsi_period
        )
        self.order = None
        self.trade_count = 0
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.datetime(0)
        symbol = self.data._name if hasattr(self.data, '_name') else 'Unknown'
        print(f'{dt.strftime("%Y-%m-%d %H:%M")} [{symbol}] {txt}')
    
    def is_market_hours(self):
        """Check if current time is during market hours"""
        current_time = self.data.datetime.time(0)
        return time(9, 30) <= current_time <= time(16, 0)
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'✅ BUY EXECUTED: ${order.executed.price:.2f}')
            else:
                self.log(f'✅ SELL EXECUTED: ${order.executed.price:.2f}')
        self.order = None
    
    def notify_trade(self, trade):
        if trade.isclosed:
            self.trade_count += 1
            hold_bars = len(trade.history)
            hold_minutes = hold_bars * 5
            self.log(f'🎯 TRADE #{self.trade_count} CLOSED: PnL: ${trade.pnl:.2f} | {hold_minutes}min')
    
    def next(self):
        # Skip if order pending
        if self.order:
            return
            
        # ONLY process during market hours
        if not self.is_market_hours():
            return
        
        current_rsi = self.rsi[0]
        current_time = self.data.datetime.time(0)
        
        # Debug output during market hours only
        if len(self.data) % 30 == 0:
            self.log(f'📊 RSI: {current_rsi:.1f} at {current_time}')
        
        # Entry: Buy when oversold
        if not self.position and current_rsi < self.params.oversold:
            self.log(f'🔥 OVERSOLD BUY SIGNAL: RSI={current_rsi:.1f}')
            
            available_cash = self.broker.getcash()
            price = self.data.close[0]
            size = int((available_cash * 0.95) / price)
            
            if size > 0:
                self.order = self.buy(size=size)
            else:
                self.log(f'❌ BUY FAILED: Not enough cash')
        
        # Exit: Sell when overbought  
        elif self.position and current_rsi > self.params.overbought:
            self.log(f'🔥 OVERBOUGHT SELL SIGNAL: RSI={current_rsi:.1f}')
            self.order = self.close()
        
        # Force close 15 minutes before market close
        elif self.position and current_time >= time(15, 45):
            self.log(f'⏰ MARKET CLOSE: Force selling position')
            self.order = self.close()
