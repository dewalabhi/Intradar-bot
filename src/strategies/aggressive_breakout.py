import backtrader as bt
import numpy as np

class AggressiveBreakout(bt.Strategy):
    """More aggressive breakout strategy to generate trades"""
    
    params = (
        ('lookback_period', 8),         # Shorter lookback = more signals
        ('volume_threshold', 0.8),      # Accept lower volume (80% of average)
        ('atr_period', 10),
        ('stop_loss_atr', 1.2),         # Tighter stops
        ('take_profit_atr', 2.0),       # Closer targets
        ('risk_per_trade', 0.01),       # Smaller risk per trade
        ('min_breakout_pct', 0.05),     # Very small breakout requirement (0.05%)
        ('volume_ma_period', 15),
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume
        
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)
        self.volume_ma = bt.indicators.SMA(self.datavolume, period=self.params.volume_ma_period)
        self.resistance = bt.indicators.Highest(self.datahigh, period=self.params.lookback_period)
        self.support = bt.indicators.Lowest(self.datalow, period=self.params.lookback_period)
        
        # Momentum indicators
        self.rsi = bt.indicators.RSI(self.dataclose, period=10)
        self.ema_fast = bt.indicators.EMA(self.dataclose, period=5)
        self.ema_slow = bt.indicators.EMA(self.dataclose, period=10)
        
        self.order = None
        self.entry_price = 0
        self.trade_count = 0
        self.wins = 0
        
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        time = self.datas[0].datetime.time(0)
        print(f'{dt} {time} | {txt}')
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'🟢 BUY - Price: ${order.executed.price:.2f}, Size: {order.executed.size}')
                self.entry_price = order.executed.price
            elif order.issell():
                pnl = (order.executed.price - self.entry_price) * order.executed.size
                self.log(f'🔴 SELL - Price: ${order.executed.price:.2f}, PnL: ${pnl:.2f}')
        self.order = None
    
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.trade_count += 1
        if trade.pnl > 0:
            self.wins += 1
        pnl_pct = (trade.pnl / abs(trade.value)) * 100
        self.log(f'✅ TRADE #{self.trade_count} - PnL: ${trade.pnl:.2f} ({pnl_pct:+.2f}%)')
    
    def calculate_position_size(self, entry_price, stop_price):
        risk_per_share = abs(entry_price - stop_price)
        if risk_per_share == 0:
            return 1
        account_value = self.broker.get_value()
        risk_amount = account_value * self.params.risk_per_trade
        position_size = int(risk_amount / risk_per_share)
        return max(1, min(position_size, 500))
    
    def next(self):
        if len(self.data) < self.params.lookback_period:
            return
        
        # Skip if we have position or pending order
        if self.position or self.order:
            return
        
        current_close = self.dataclose[0]
        current_volume = self.datavolume[0]
        resistance_level = self.resistance[-1]  # Previous resistance
        support_level = self.support[-1]        # Previous support
        
        # More relaxed volume check
        volume_ok = current_volume > (self.volume_ma[0] * self.params.volume_threshold)
        
        # Breakout detection with lower requirements
        # Long signal: Close above recent resistance
        if (current_close > resistance_level and 
            volume_ok and 
            self.rsi[0] < 75 and  # Not too overbought
            self.ema_fast[0] > self.ema_slow[0]):
            
            breakout_strength = ((current_close - resistance_level) / resistance_level) * 100
            if breakout_strength >= self.params.min_breakout_pct:
                stop_price = current_close - (self.atr[0] * self.params.stop_loss_atr)
                size = self.calculate_position_size(current_close, stop_price)
                
                self.order = self.buy(size=size)
                self.log(f'🔥 LONG BREAKOUT - Level: ${resistance_level:.2f}, Strength: {breakout_strength:.2f}%')
        
        # Short signal: Close below recent support  
        elif (current_close < support_level and 
              volume_ok and 
              self.rsi[0] > 25 and  # Not too oversold
              self.ema_fast[0] < self.ema_slow[0]):
            
            breakout_strength = ((support_level - current_close) / support_level) * 100
            if breakout_strength >= self.params.min_breakout_pct:
                stop_price = current_close + (self.atr[0] * self.params.stop_loss_atr)
                size = self.calculate_position_size(current_close, stop_price)
                
                self.order = self.sell(size=size)
                self.log(f'🔥 SHORT BREAKOUT - Level: ${support_level:.2f}, Strength: {breakout_strength:.2f}%')
        
        # Debug every 100 bars
        if len(self.data) % 100 == 0:
            vol_ratio = current_volume / self.volume_ma[0] if self.volume_ma[0] > 0 else 0
            self.log(f'📊 Close: ${current_close:.2f}, R: ${resistance_level:.2f}, '
                    f'S: ${support_level:.2f}, Vol: {vol_ratio:.1f}x')
    
    def stop(self):
        win_rate = (self.wins / self.trade_count * 100) if self.trade_count > 0 else 0
        final_value = self.broker.get_value()
        total_return = ((final_value / 100000) - 1) * 100
        
        print(f"\n🏁 AGGRESSIVE STRATEGY RESULTS:")
        print(f"💰 Return: {total_return:+.2f}%")
        print(f"🎯 Trades: {self.trade_count}")
        print(f"✅ Win Rate: {win_rate:.1f}%")