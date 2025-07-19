import backtrader as bt

class BalancedBreakout(bt.Strategy):
    params = (
        ("lookback_period", 8),          # Medium lookback
        ("volume_threshold", 0.9),       # Moderate volume requirement  
        ("stop_loss_pct", 0.7),         # 0.7% stop loss
        ("take_profit_pct", 1.4),       # 1.4% target (2:1 ratio)
        ("max_hold_bars", 15),          # 75 minutes max
        ("min_breakout_pct", 0.1),      # Lower breakout threshold
        ("position_size", 1000),        # Fixed larger size
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume
        
        # Simple but effective indicators
        self.resistance = bt.indicators.Highest(self.datahigh, period=self.params.lookback_period)
        self.support = bt.indicators.Lowest(self.datalow, period=self.params.lookback_period)
        self.volume_ma = bt.indicators.SMA(self.datavolume, period=15)
        self.rsi = bt.indicators.RSI(self.dataclose, period=10)
        
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
            
        # Manage existing position with strict exits
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
            
        # Simplified entry logic - focus on the essentials
        current_close = self.dataclose[0]
        current_volume = self.datavolume[0]
        resistance_level = self.resistance[-1]
        support_level = self.support[-1]
        
        # Basic volume check
        volume_ok = current_volume > (self.volume_ma[0] * self.params.volume_threshold)
        
        # LONG ENTRY: Simple breakout above resistance
        if (current_close > resistance_level and volume_ok and 
            30 < self.rsi[0] < 70):  # Avoid extreme RSI
            
            breakout_strength = ((current_close - resistance_level) / resistance_level * 100)
            if breakout_strength >= self.params.min_breakout_pct:
                self.order = self.buy(size=self.params.position_size)
                self.entry_price = current_close
                self.entry_bar = len(self.data)
                vol_ratio = current_volume / self.volume_ma[0]
                self.log(f"🟢 LONG: {current_close:.2f} | Strength: {breakout_strength:.2f}% | Vol: {vol_ratio:.1f}x | RSI: {self.rsi[0]:.1f}")
            
        # SHORT ENTRY: Simple breakdown below support
        elif (current_close < support_level and volume_ok and 
              30 < self.rsi[0] < 70):  # Avoid extreme RSI
            
            breakdown_strength = ((support_level - current_close) / support_level * 100)
            if breakdown_strength >= self.params.min_breakout_pct:
                self.order = self.sell(size=self.params.position_size)
                self.entry_price = current_close
                self.entry_bar = len(self.data)
                vol_ratio = current_volume / self.volume_ma[0]
                self.log(f"�� SHORT: {current_close:.2f} | Strength: {breakdown_strength:.2f}% | Vol: {vol_ratio:.1f}x | RSI: {self.rsi[0]:.1f}")
            
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
                        status = "WIN ✅"
                    else:
                        status = "LOSS ❌"
                        
                    self.log(f"EXIT: {order.executed.price:.2f} | PnL: ${pnl:.2f} ({pnl_pct:+.2f}%) | {status}")
                    self.entry_price = 0
                    
        self.order = None
        
    def stop(self):
        win_rate = (self.wins / self.trade_count * 100) if self.trade_count > 0 else 0
        final_value = self.broker.get_value()
        total_return = ((final_value / 100000) - 1) * 100
        daily_return = total_return / 10
        
        print(f"\n🏁 BALANCED BREAKOUT RESULTS:")
        print(f"💰 Total Return: {total_return:+.2f}%")
        print(f"📈 Daily Average: {daily_return:+.2f}%")
        print(f"🎯 Total Trades: {self.trade_count}")
        print(f"✅ Win Rate: {win_rate:.1f}%")
        print(f"💵 Total PnL: ${self.total_pnl:.2f}")
        
        if self.trade_count > 0:
            avg_trade = self.total_pnl / self.trade_count
            print(f"📊 Average trade: ${avg_trade:.2f}")
            
            # Estimate what we need for 1% daily
            needed_daily = 1000  # $1000 per day for 1%
            needed_per_trade = needed_daily / (self.trade_count / 10)  # trades per day
            print(f"🎯 Need ${needed_per_trade:.2f} per trade for 1% daily target")
        
        if daily_return >= 1.0:
            print("🎯 TARGET ACHIEVED!")
        elif daily_return >= 0.5:
            print("📈 Close to target - minor tweaks needed!")
        elif daily_return >= 0.2:
            print("🔧 Good base - optimize position sizing")
        else:
            print("📉 Need strategy refinement")

