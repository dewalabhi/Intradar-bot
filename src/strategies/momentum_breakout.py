import backtrader as bt

class MomentumBreakout(bt.Strategy):
    params = (
        ("lookback_period", 12),         # Longer lookback for stronger levels
        ("volume_threshold", 1.2),       # Higher volume requirement
        ("momentum_period", 3),          # Confirm momentum over 3 bars
        ("stop_loss_pct", 0.6),         # Tighter stop loss
        ("take_profit_pct", 1.8),       # Better risk/reward ratio
        ("max_hold_bars", 15),          # Medium hold time
        ("min_breakout_pct", 0.2),      # Minimum breakout strength
        ("rsi_oversold", 35),           # RSI levels
        ("rsi_overbought", 65),
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume
        
        # Indicators
        self.resistance = bt.indicators.Highest(self.datahigh, period=self.params.lookback_period)
        self.support = bt.indicators.Lowest(self.datalow, period=self.params.lookback_period)
        self.volume_ma = bt.indicators.SMA(self.datavolume, period=20)
        self.rsi = bt.indicators.RSI(self.dataclose, period=14)
        
        # Momentum indicators
        self.momentum = bt.indicators.Momentum(self.dataclose, period=self.params.momentum_period)
        self.ema9 = bt.indicators.EMA(self.dataclose, period=9)
        self.ema21 = bt.indicators.EMA(self.dataclose, period=21)
        
        # Trade tracking
        self.order = None
        self.entry_price = 0
        self.entry_bar = 0
        self.trade_count = 0
        self.wins = 0
        self.total_pnl = 0
        
    def log(self, txt):
        print(f"{txt}")
        
    def next(self):
        if len(self.data) < self.params.lookback_period:
            return
            
        # Manage existing position
        if self.position:
            current_price = self.dataclose[0]
            hold_time = len(self.data) - self.entry_bar
            
            if self.position.size > 0:  # Long position
                stop_price = self.entry_price * (1 - self.params.stop_loss_pct / 100)
                target_price = self.entry_price * (1 + self.params.take_profit_pct / 100)
                
                if current_price <= stop_price:
                    self.order = self.close()
                    self.log(f"🛑 STOP: {current_price:.2f}")
                    return
                elif current_price >= target_price:
                    self.order = self.close()
                    self.log(f"🎯 TARGET: {current_price:.2f}")
                    return
                elif hold_time >= self.params.max_hold_bars:
                    self.order = self.close()
                    self.log(f"⏰ TIME: {current_price:.2f}")
                    return
            
            elif self.position.size < 0:  # Short position
                stop_price = self.entry_price * (1 + self.params.stop_loss_pct / 100)
                target_price = self.entry_price * (1 - self.params.take_profit_pct / 100)
                
                if current_price >= stop_price:
                    self.order = self.close()
                    self.log(f"🛑 SHORT STOP: {current_price:.2f}")
                    return
                elif current_price <= target_price:
                    self.order = self.close()
                    self.log(f"🎯 SHORT TARGET: {current_price:.2f}")
                    return
                elif hold_time >= self.params.max_hold_bars:
                    self.order = self.close()
                    self.log(f"⏰ SHORT TIME: {current_price:.2f}")
                    return
                    
        # Skip if we have position or pending order
        if self.position or self.order:
            return
            
        # Entry conditions - MUCH MORE SELECTIVE
        current_close = self.dataclose[0]
        current_volume = self.datavolume[0]
        resistance_level = self.resistance[-2]  # Use previous resistance
        support_level = self.support[-2]        # Use previous support
        
        # Strong volume confirmation
        volume_confirmed = current_volume > (self.volume_ma[0] * self.params.volume_threshold)
        
        # Momentum confirmation
        momentum_positive = self.momentum[0] > 0
        trend_up = self.ema9[0] > self.ema21[0]
        trend_down = self.ema9[0] < self.ema21[0]
        
        # Position sizing - smaller, more conservative
        position_size = 300  # Fixed size for consistency
        
        # LONG ENTRY: Multiple confirmations required
        long_breakout = current_close > resistance_level
        long_strength = ((current_close - resistance_level) / resistance_level * 100) >= self.params.min_breakout_pct
        long_rsi_ok = self.rsi[0] < self.params.rsi_overbought
        long_momentum = momentum_positive and trend_up
        
        if (long_breakout and long_strength and volume_confirmed and 
            long_rsi_ok and long_momentum):
            
            self.order = self.buy(size=position_size)
            self.entry_price = current_close
            self.entry_bar = len(self.data)
            strength = ((current_close - resistance_level) / resistance_level * 100)
            self.log(f"🟢 LONG: {current_close:.2f} | Strength: {strength:.2f}% | RSI: {self.rsi[0]:.1f}")
            
        # SHORT ENTRY: Multiple confirmations required
        short_breakdown = current_close < support_level
        short_strength = ((support_level - current_close) / support_level * 100) >= self.params.min_breakout_pct
        short_rsi_ok = self.rsi[0] > self.params.rsi_oversold
        short_momentum = not momentum_positive and trend_down
        
        if (short_breakdown and short_strength and volume_confirmed and 
            short_rsi_ok and short_momentum):
            
            self.order = self.sell(size=position_size)
            self.entry_price = current_close
            self.entry_bar = len(self.data)
            strength = ((support_level - current_close) / support_level * 100)
            self.log(f"🔴 SHORT: {current_close:.2f} | Strength: {strength:.2f}% | RSI: {self.rsi[0]:.1f}")
            
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                pass  # Entry logged in next()
            elif order.issell():
                if self.entry_price > 0:
                    pnl = (order.executed.price - self.entry_price) * order.executed.size
                    self.total_pnl += pnl
                    pnl_pct = (pnl / (self.entry_price * abs(order.executed.size))) * 100
                    
                    self.trade_count += 1
                    if pnl > 0:
                        self.wins += 1
                        
                    self.log(f"EXIT: {order.executed.price:.2f} | PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)")
                    self.entry_price = 0
                    
        self.order = None
        
    def stop(self):
        win_rate = (self.wins / self.trade_count * 100) if self.trade_count > 0 else 0
        final_value = self.broker.get_value()
        total_return = ((final_value / 100000) - 1) * 100
        daily_return = total_return / 10
        
        print(f"\n🏁 MOMENTUM STRATEGY RESULTS:")
        print(f"💰 Total Return: {total_return:+.2f}%")
        print(f"📈 Daily Average: {daily_return:+.2f}%")
        print(f"🎯 Total Trades: {self.trade_count}")
        print(f"✅ Win Rate: {win_rate:.1f}%")
        print(f"💵 Total PnL: ${self.total_pnl:.2f}")
        
        if self.trade_count > 0:
            avg_win = (self.total_pnl / self.wins) if self.wins > 0 else 0
            avg_loss = (self.total_pnl / (self.trade_count - self.wins)) if (self.trade_count - self.wins) > 0 else 0
            print(f"📊 Avg Win: ${avg_win:.2f} | Avg Loss: ${avg_loss:.2f}")
        
        if daily_return >= 1.0:
            print("🎯 TARGET ACHIEVED!")
        elif daily_return >= 0.3:
            print("📈 Good progress!")
        else:
            print("📉 Need more refinement")

