"""
Professional Price Action Breakout Strategy
"""

import backtrader as bt
from datetime import time


class PriceActionBreakout(bt.Strategy):
    """Price Action Breakout Strategy for Intraday Trading"""
    
    params = (
        ('lookback_bars', 20),
        ('volume_threshold', 1.5),
        ('breakout_buffer', 0.1),
        ('min_range_pct', 0.3),
        ('enabled', True),
    )
    
    def __init__(self):
        # Support/Resistance levels
        self.high_n = bt.indicators.Highest(self.data.high, period=self.params.lookback_bars)
        self.low_n = bt.indicators.Lowest(self.data.low, period=self.params.lookback_bars)
        
        # Volume confirmation
        self.volume_ma = bt.indicators.SimpleMovingAverage(self.data.volume, period=20)
        
        # Volatility
        self.atr = bt.indicators.AverageTrueRange(period=14)
        
        # State tracking
        self.order = None
        self.trade_count = 0
        self.resistance_level = 0
        self.support_level = 0
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.datetime(0)
        symbol = self.data._name if hasattr(self.data, '_name') else 'Unknown'
        print(f'{dt.strftime("%H:%M")} [{symbol}] {txt}')
    
    def is_market_hours(self):
        current_time = self.data.datetime.time(0)
        return time(9, 30) <= current_time <= time(16, 0)
    
    def is_breakout_time(self):
        """Best times for breakouts"""
        current_time = self.data.datetime.time(0)
        return (time(9, 30) <= current_time <= time(11, 30) or 
                time(14, 30) <= current_time <= time(15, 30))
    
    def has_volume_surge(self):
        """Check for volume confirmation"""
        if self.volume_ma[0] == 0:
            return False
        volume_ratio = self.data.volume[0] / self.volume_ma[0]
        return volume_ratio >= self.params.volume_threshold
    
    def is_breakout_candle(self):
        """Detect bullish breakout candle"""
        current_price = self.data.close[0]
        current_high = self.data.high[0]
        current_open = self.data.open[0]
        
        # Bullish candle
        is_bullish = current_price > current_open
        
        # Breaking resistance
        breakout_level = self.resistance_level * (1 + self.params.breakout_buffer/100)
        resistance_break = current_high > breakout_level
        
        # Strong body (momentum)
        body_size = abs(current_price - current_open)
        candle_size = self.data.high[0] - self.data.low[0]
        strong_body = body_size >= (candle_size * 0.6) if candle_size > 0 else False
        
        return is_bullish and resistance_break and strong_body
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'🚀 BREAKOUT BUY: ${order.executed.price:.2f} (Size: {order.executed.size})')
            else:
                self.log(f'✅ BREAKOUT SELL: ${order.executed.price:.2f}')
        self.order = None
    
    def notify_trade(self, trade):
        if trade.isclosed:
            self.trade_count += 1
            hold_time = len(trade.history) * 5
            self.log(f'📈 BREAKOUT TRADE #{self.trade_count}: P&L ${trade.pnl:.2f} | {hold_time}min')
    
    def next(self):
        # Skip if order pending or outside market hours
        if self.order or not self.is_market_hours():
            return
        
        # Update S/R levels
        self.resistance_level = self.high_n[0]
        self.support_level = self.low_n[0]
        
        # Check minimum range
        range_pct = ((self.resistance_level - self.support_level) / self.data.close[0]) * 100
        if range_pct < self.params.min_range_pct:
            return
        
        current_price = self.data.close[0]
        
        # Debug every 30 minutes
        if len(self.data) % 6 == 0:
            self.log(f'📊 Price: ${current_price:.2f} | Resistance: ${self.resistance_level:.2f} | Support: ${self.support_level:.2f}')
        
        # ENTRY: Look for breakout during prime time
        if (not self.position and 
            self.is_breakout_time() and
            self.has_volume_surge() and
            self.is_breakout_candle()):
            
            available_cash = self.broker.getcash()
            size = int((available_cash * 0.8) / current_price)
            
            if size > 0:
                self.order = self.buy(size=size)
                vol_ratio = self.data.volume[0] / self.volume_ma[0]
                self.log(f'🔥 BREAKOUT ENTRY: Volume {vol_ratio:.1f}x | Breaking ${self.resistance_level:.2f}')
        
        # EXIT: Profit target or stop loss
        elif self.position:
            current_time = self.data.datetime.time(0)
            
            # Take profit if 1% gain
            profit_target = current_price > (self.position.price * 1.01)
            
            # Stop loss if below support
            stop_loss = current_price < (self.support_level * 0.998)
            
            # Time exit before market close
            time_exit = current_time >= time(15, 45)
            
            # Max hold 2 hours
            bars_held = len(self.data) - getattr(self, 'entry_bar', 0)
            max_time = bars_held >= 24  # 24 bars = 2 hours
            
            if profit_target:
                self.log(f'🎯 PROFIT TARGET: Taking 1% gain')
                self.order = self.close()
            elif stop_loss:
                self.log(f'🛑 STOP LOSS: Below support')
                self.order = self.close()
            elif time_exit or max_time:
                self.log(f'⏰ TIME EXIT: End of day/max hold')
                self.order = self.close()
