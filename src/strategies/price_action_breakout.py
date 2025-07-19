import backtrader as bt
import numpy as np

class PriceActionBreakout(bt.Strategy):
    """
    Price Action Breakout Strategy for Intraday Trading
    
    Logic:
    - Identifies support/resistance levels using pivot points
    - Enters on breakouts with volume confirmation
    - Uses ATR for dynamic stop loss and take profit
    - Risk management with position sizing
    """
    
    params = (
        ('lookback_period', 20),        # Period for S/R levels
        ('volume_threshold', 1.3),      # Volume multiplier for confirmation
        ('atr_period', 14),             # ATR period for stops
        ('stop_loss_atr', 1.5),         # Stop loss in ATR multiples
        ('take_profit_atr', 2.5),       # Take profit in ATR multiples
        ('risk_per_trade', 0.02),       # Risk 2% per trade
        ('min_breakout_pct', 0.3),      # Minimum breakout % of daily range
        ('pullback_bars', 3),           # Bars to wait for pullback entry
        ('volume_ma_period', 20),       # Volume moving average period
    )
    
    def __init__(self):
        # Data references
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume
        self.dataopen = self.datas[0].open
        
        # Technical indicators
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)
        self.volume_ma = bt.indicators.SMA(self.datavolume, period=self.params.volume_ma_period)
        
        # Support and Resistance levels
        self.resistance = bt.indicators.Highest(self.datahigh, period=self.params.lookback_period)
        self.support = bt.indicators.Lowest(self.datalow, period=self.params.lookback_period)
        
        # Additional indicators for confirmation
        self.rsi = bt.indicators.RSI(self.dataclose, period=14)
        self.ema_fast = bt.indicators.EMA(self.dataclose, period=8)
        self.ema_slow = bt.indicators.EMA(self.dataclose, period=21)
        
        # Trade management
        self.order = None
        self.stop_order = None
        self.target_order = None
        self.entry_price = 0
        self.stop_price = 0
        self.target_price = 0
        
        # Performance tracking
        self.trade_count = 0
        self.wins = 0
        self.losses = 0
        
        # State tracking
        self.breakout_level = 0
        self.breakout_direction = 0  # 1 for long, -1 for short
        self.bars_since_breakout = 0
        self.daily_high = 0
        self.daily_low = float('inf')
        
        print("🚀 Price Action Breakout Strategy Initialized")
        print(f"📊 Parameters: Lookback={self.params.lookback_period}, "
              f"Volume Threshold={self.params.volume_threshold}x, "
              f"Risk={self.params.risk_per_trade*100}%")
    
    def log(self, txt, dt=None):
        """Enhanced logging function"""
        dt = dt or self.datas[0].datetime.date(0)
        time = self.datas[0].datetime.time(0)
        print(f'{dt} {time} | {txt}')
    
    def notify_order(self, order):
        """Handle order notifications"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'🟢 LONG ENTRY - Price: ${order.executed.price:.2f}, '
                        f'Size: {order.executed.size}, Value: ${order.executed.value:.2f}')
                self.entry_price = order.executed.price
                
                # Set stop loss and take profit
                self.set_stop_and_target()
                
            elif order.issell():
                if self.position.size > 0:  # Closing long position
                    pnl = (order.executed.price - self.entry_price) * order.executed.size
                    self.log(f'🔴 LONG EXIT - Price: ${order.executed.price:.2f}, '
                            f'PnL: ${pnl:.2f}')
                else:  # Short entry
                    self.log(f'🟡 SHORT ENTRY - Price: ${order.executed.price:.2f}, '
                            f'Size: {order.executed.size}')
                    self.entry_price = order.executed.price
                    self.set_stop_and_target()
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'❌ Order {order.status}: {order}')
            
        # Reset order reference
        if order == self.order:
            self.order = None
        elif order == self.stop_order:
            self.stop_order = None
        elif order == self.target_order:
            self.target_order = None
    
    def notify_trade(self, trade):
        """Handle trade notifications and track performance"""
        if not trade.isclosed:
            return
        
        self.trade_count += 1
        pnl = trade.pnl
        pnl_pct = (trade.pnl / abs(trade.value)) * 100 if trade.value else 0
        
        if pnl > 0:
            self.wins += 1
            self.log(f'✅ TRADE #{self.trade_count} WIN - PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)')
        else:
            self.losses += 1
            self.log(f'❌ TRADE #{self.trade_count} LOSS - PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)')
        
        # Calculate win rate
        win_rate = (self.wins / self.trade_count) * 100 if self.trade_count > 0 else 0
        self.log(f'📊 Win Rate: {win_rate:.1f}% ({self.wins}W/{self.losses}L)')
    
    def calculate_position_size(self, entry_price, stop_price):
        """Calculate position size based on risk management"""
        if entry_price <= 0 or stop_price <= 0:
            return 0
            
        risk_per_share = abs(entry_price - stop_price)
        if risk_per_share == 0:
            return 0
            
        account_value = self.broker.get_value()
        risk_amount = account_value * self.params.risk_per_trade
        
        position_size = int(risk_amount / risk_per_share)
        return max(1, min(position_size, 1000))  # Cap at 1000 shares
    
    def set_stop_and_target(self):
        """Set stop loss and take profit orders"""
        if not self.position:
            return
            
        current_atr = self.atr[0]
        
        if self.position.size > 0:  # Long position
            self.stop_price = self.entry_price - (current_atr * self.params.stop_loss_atr)
            self.target_price = self.entry_price + (current_atr * self.params.take_profit_atr)
            
            self.stop_order = self.sell(exectype=bt.Order.Stop, price=self.stop_price, size=self.position.size)
            self.target_order = self.sell(exectype=bt.Order.Limit, price=self.target_price, size=self.position.size)
            
        else:  # Short position
            self.stop_price = self.entry_price + (current_atr * self.params.stop_loss_atr)
            self.target_price = self.entry_price - (current_atr * self.params.take_profit_atr)
            
            self.stop_order = self.buy(exectype=bt.Order.Stop, price=self.stop_price, size=abs(self.position.size))
            self.target_order = self.buy(exectype=bt.Order.Limit, price=self.target_price, size=abs(self.position.size))
        
        self.log(f'🎯 Stop: ${self.stop_price:.2f}, Target: ${self.target_price:.2f}')
    
    def detect_breakout(self):
        """Detect valid breakouts with multiple confirmations"""
        current_close = self.dataclose[0]
        current_high = self.datahigh[0]
        current_low = self.datalow[0]
        current_volume = self.datavolume[0]
        
        # Update daily range
        if current_high > self.daily_high:
            self.daily_high = current_high
        if current_low < self.daily_low:
            self.daily_low = current_low
            
        daily_range = self.daily_high - self.daily_low
        
        # Volume confirmation
        volume_confirmed = current_volume > (self.volume_ma[0] * self.params.volume_threshold)
        
        # Resistance breakout (Long signal)
        if (current_close > self.resistance[-1] and 
            current_close > self.resistance[0] and
            volume_confirmed and 
            self.rsi[0] < 70 and  # Not overbought
            self.ema_fast[0] > self.ema_slow[0]):  # Uptrend
            
            breakout_strength = (current_close - self.resistance[-1]) / daily_range * 100
            if breakout_strength >= self.params.min_breakout_pct:
                return 1, self.resistance[-1]  # Long breakout
        
        # Support breakdown (Short signal) 
        if (current_close < self.support[-1] and 
            current_close < self.support[0] and
            volume_confirmed and 
            self.rsi[0] > 30 and  # Not oversold
            self.ema_fast[0] < self.ema_slow[0]):  # Downtrend
            
            breakout_strength = (self.support[-1] - current_close) / daily_range * 100
            if breakout_strength >= self.params.min_breakout_pct:
                return -1, self.support[-1]  # Short breakout
        
        return 0, 0
    
    def next(self):
        """Main strategy logic executed on each bar"""
        
        # Skip if insufficient data
        if len(self.data) < self.params.lookback_period:
            return
            
        # Reset daily levels at market open (9:30 AM)
        current_time = self.data.datetime.time(0)
        if current_time.hour == 9 and current_time.minute == 30:
            self.daily_high = self.datahigh[0]
            self.daily_low = self.datalow[0]
        
        # Don't trade in first/last 30 minutes of session
        if (current_time.hour == 9 and current_time.minute < 60) or current_time.hour >= 15:
            return
        
        # If we have a position, manage it
        if self.position:
            self.manage_position()
            return
        
        # If we have pending orders, skip
        if self.order:
            return
        
        # Look for breakout signals
        direction, level = self.detect_breakout()
        
        if direction != 0:
            self.breakout_level = level
            self.breakout_direction = direction
            self.bars_since_breakout = 0
            
            # Enter trade immediately on strong breakout
            current_atr = self.atr[0]
            
            if direction == 1:  # Long breakout
                stop_price = self.dataclose[0] - (current_atr * self.params.stop_loss_atr)
                position_size = self.calculate_position_size(self.dataclose[0], stop_price)
                
                if position_size > 0:
                    self.order = self.buy(size=position_size)
                    self.log(f'🔥 LONG BREAKOUT Signal - Level: ${level:.2f}, Size: {position_size}')
            
            elif direction == -1:  # Short breakout  
                stop_price = self.dataclose[0] + (current_atr * self.params.stop_loss_atr)
                position_size = self.calculate_position_size(self.dataclose[0], stop_price)
                
                if position_size > 0:
                    self.order = self.sell(size=position_size)
                    self.log(f'🔥 SHORT BREAKOUT Signal - Level: ${level:.2f}, Size: {position_size}')
    
    def manage_position(self):
        """Manage existing positions with trailing stops and early exits"""
        current_close = self.dataclose[0]
        current_atr = self.atr[0]
        
        if self.position.size > 0:  # Long position
            # Trailing stop
            new_stop = current_close - (current_atr * self.params.stop_loss_atr)
            if new_stop > self.stop_price:
                if self.stop_order:
                    self.cancel(self.stop_order)
                self.stop_price = new_stop
                self.stop_order = self.sell(exectype=bt.Order.Stop, price=self.stop_price, size=self.position.size)
                
        elif self.position.size < 0:  # Short position
            # Trailing stop
            new_stop = current_close + (current_atr * self.params.stop_loss_atr)
            if new_stop < self.stop_price:
                if self.stop_order:
                    self.cancel(self.stop_order)
                self.stop_price = new_stop
                self.stop_order = self.buy(exectype=bt.Order.Stop, price=self.stop_price, size=abs(self.position.size))
    
    def stop(self):
        """Called when strategy ends - print final performance"""
        account_value = self.broker.get_value()
        total_return = ((account_value / 100000) - 1) * 100
        
        print("\n" + "="*50)
        print("🏁 STRATEGY PERFORMANCE SUMMARY")
        print("="*50)
        print(f"💰 Final Value: ${account_value:,.2f}")
        print(f"📈 Total Return: {total_return:+.2f}%")
        print(f"🎯 Total Trades: {self.trade_count}")
        if self.trade_count > 0:
            win_rate = (self.wins / self.trade_count) * 100
            print(f"✅ Win Rate: {win_rate:.1f}% ({self.wins}W/{self.losses}L)")
            avg_win = self.wins / self.trade_count if self.trade_count > 0 else 0
            print(f"📊 Average Trade: {total_return/self.trade_count:.2f}%" if self.trade_count > 0 else "📊 No trades executed")
        print("="*50)