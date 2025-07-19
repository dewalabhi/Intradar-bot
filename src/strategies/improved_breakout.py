import backtrader as bt

class ImprovedBreakout(bt.Strategy):
    params = (
        ('lookback_period', 6),         # Even shorter for more signals
        ('volume_threshold', 0.7),      # Lower volume requirement
        ('atr_period', 8),
        ('stop_loss_atr', 1.0),         # Tighter stops
        ('take_profit_atr', 1.8),       # Closer targets for faster exits
        ('risk_per_trade', 0.015),      # 1.5% risk per trade
        ('min_breakout_pct', 0.03),     # 0.03% minimum breakout
        ('volume_ma_period', 10),
        ('max_hold_bars', 20),          # Force exit after 20 bars (100 minutes)
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
        
        self.rsi = bt.indicators.RSI(self.dataclose, period=8)
        self.ema_fast = bt.indicators.EMA(self.dataclose, period=3)
        self.ema_slow = bt.indicators.EMA(self.dataclose, period=8)
        
        self.order = None
        self.stop_order = None
        self.target_order = None
        self.entry_price = 0
        self.entry_bar = 0
        self.trade_count = 0
        self.wins = 0
        
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        time = self.datas[0].datetime.time(0)
        print(f'{dt} {time} | {txt}')
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'🟢 BUY - ${order.executed.price:.2f}, Size: {order.executed.size}')
                self.entry_price = order.executed.price
                self.entry_bar = len(self.data)
                self.set_exit_orders()
            elif order.issell():
                pnl = (order.executed.price - self.entry_price) * order.executed.size
                self.log(f'🔴 SELL - ${order.executed.price:.2f}, PnL: ${pnl:.2f}')
        
        if order in [self.order, self.stop_order, self.target_order]:
            if order == self.order:
                self.order = None
            elif order == self.stop_order:
                self.stop_order = None
            elif order == self.target_order:
                self.target_order = None
    
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.trade_count += 1
        if trade.pnl > 0:
            self.wins += 1
        pnl_pct = (trade.pnl / abs(trade.value)) * 100
        self.log(f'✅ TRADE #{self.trade_count} CLOSED - PnL: ${trade.pnl:.2f} ({pnl_pct:+.2f}%)')
    
    def set_exit_orders(self):
        if not self.position:
            return
            
        current_atr = self.atr[0]
        
        if self.position.size > 0:  # Long position
            stop_price = self.entry_price - (current_atr * self.params.stop_loss_atr)
            target_price = self.entry_price + (current_atr * self.params.take_profit_atr)
            
            self.stop_order = self.sell(exectype=bt.Order.Stop, price=stop_price, size=self.position.size)
            self.target_order = self.sell(exectype=bt.Order.Limit, price=target_price, size=self.position.size)
            
            self.log(f'🎯 Stop: ${stop_price:.2f}, Target: ${target_price:.2f}')
    
    def calculate_position_size(self, entry_price, stop_price):
        risk_per_share = abs(entry_price - stop_price)
        if risk_per_share == 0:
            return 1
        account_value = self.broker.get_value()
        risk_amount = account_value * self.params.risk_per_trade
        position_size = int(risk_amount / risk_per_share)
        return max(1, min(position_size, 800))  # Increased max size
    
    def next(self):
        if len(self.data) < self.params.lookback_period:
            return
        
        # Force exit after max hold time
        if self.position and (len(self.data) - self.entry_bar) >= self.params.max_hold_bars:
            if self.stop_order:
                self.cancel(self.stop_order)
            if self.target_order:
                self.cancel(self.target_order)
            self.order = self.close()
            self.log(f'⏰ FORCE EXIT after {self.params.max_hold_bars} bars')
            return
        
        # Skip if we have position or pending order
        if self.position or self.order:
            return
        
        current_close = self.dataclose[0]
        current_volume = self.datavolume[0]
        resistance_level = self.resistance[-1]
        support_level = self.support[-1]
        
        volume_ok = current_volume > (self.volume_ma[0] * self.params.volume_threshold)
        
        # Long signal
        if (current_close > resistance_level and 
            volume_ok and 
            self.rsi[0] < 70 and
            self.ema_fast[0] > self.ema_slow[0]):
            
            breakout_strength = ((current_close - resistance_level) / resistance_level) * 100
            if breakout_strength >= self.params.min_breakout_pct:
                stop_price = current_close - (self.atr[0] * self.params.stop_loss_atr)
                size = self.calculate_position_size(current_close, stop_price)
                
                self.order = self.buy(size=size)
                self.log(f'🔥 LONG BREAKOUT - Level: ${resistance_level:.2f}, Strength: {breakout_strength:.3f}%')
        
        # Short signal
        elif (current_close < support_level and 
              volume_ok and 
              self.rsi[0] > 30 and
              self.ema_fast[0] < self.ema_slow[0]):
            
            breakout_strength = ((support_level - current_close) / support_level) * 100
            if breakout_strength >= self.params.min_breakout_pct:
                stop_price = current_close + (self.atr[0] * self.params.stop_loss_atr)
                size = self.calculate_position_size(current_close, stop_price)
                
                self.order = self.sell(size=size)
                self.log(f'🔥 SHORT BREAKOUT - Level: ${support_level:.2f}, Strength: {breakout_strength:.3f}%')
    
    def stop(self):
        win_rate = (self.wins / self.trade_count * 100) if self.trade_count > 0 else 0
        final_value = self.broker.get_value()
        total_return = ((final_value / 100000) - 1) * 100
        
        print(f"\n🏁 IMPROVED STRATEGY RESULTS:")
        print(f"💰 Return: {total_return:+.2f}%")
        print(f"🎯 Trades: {self.trade_count}")
        print(f"✅ Win Rate: {win_rate:.1f}%")
        
        # Calculate daily return
        if self.trade_count > 0:
            daily_return = total_return / 5  # 5 days of data
            print(f"📊 Avg Daily Return: {daily_return:+.2f}%")