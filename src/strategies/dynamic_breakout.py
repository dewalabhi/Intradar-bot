import backtrader as bt

class DynamicBreakout(bt.Strategy):
    params = (
        ("lookback_period", 8),
        ("volume_threshold", 0.9),
        ("atr_period", 10),
        ("stop_atr_mult", 1.2),         # Dynamic: 1.2x ATR for stops
        ("target_atr_mult", 2.4),       # Dynamic: 2.4x ATR for targets (2:1 ratio)
        ("max_hold_bars", 20),
        ("min_breakout_pct", 0.1),
        ("position_size", 1200),        # Larger size
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume
        
        # Indicators
        self.resistance = bt.indicators.Highest(self.datahigh, period=self.params.lookback_period)
        self.support = bt.indicators.Lowest(self.datalow, period=self.params.lookback_period)
        self.volume_ma = bt.indicators.SMA(self.datavolume, period=15)
        self.rsi = bt.indicators.RSI(self.dataclose, period=10)
        
        # DYNAMIC VOLATILITY MEASURE
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)
        
        # Trade tracking
        self.order = None
        self.entry_price = 0
        self.entry_bar = 0
        self.stop_price = 0
        self.target_price = 0
        self.trade_count = 0
        self.wins = 0
        self.total_pnl = 0
        
    def log(self, txt):
        print(f"{txt}")
        
    def next(self):
        if len(self.data) < max(self.params.lookback_period, self.params.atr_period):
            return
            
        # Manage existing position with DYNAMIC stops
        if self.position:
            current_price = self.dataclose[0]
            hold_time = len(self.data) - self.entry_bar
            
            # DYNAMIC STOP/TARGET CALCULATION
            current_atr = self.atr[0]
            
            if self.position.size > 0:  # Long position
                # Dynamic stops based on current ATR
                dynamic_stop = self.entry_price - (current_atr * self.params.stop_atr_mult)
                dynamic_target = self.entry_price + (current_atr * self.params.target_atr_mult)
                
                if current_price <= dynamic_stop:
                    self.order = self.close()
                    atr_pct = (current_atr / self.entry_price) * 100
                    self.log(f"🛑 DYNAMIC STOP: {current_price:.2f} (ATR: {current_atr:.2f}, {atr_pct:.1f}%)")
                    return
                elif current_price >= dynamic_target:
                    self.order = self.close()
                    self.log(f"🎯 DYNAMIC TARGET: {current_price:.2f}")
                    return
                elif hold_time >= self.params.max_hold_bars:
                    self.order = self.close()
                    self.log(f"⏰ TIME: {current_price:.2f}")
                    return
            
            elif self.position.size < 0:  # Short position
                dynamic_stop = self.entry_price + (current_atr * self.params.stop_atr_mult)
                dynamic_target = self.entry_price - (current_atr * self.params.target_atr_mult)
                
                if current_price >= dynamic_stop:
                    self.order = self.close()
                    self.log(f"🛑 SHORT DYNAMIC STOP: {current_price:.2f}")
                    return
                elif current_price <= dynamic_target:
                    self.order = self.close()
                    self.log(f"🎯 SHORT DYNAMIC TARGET: {current_price:.2f}")
                    return
                elif hold_time >= self.params.max_hold_bars:
                    self.order = self.close()
                    self.log(f"⏰ SHORT TIME: {current_price:.2f}")
                    return
                    
        # Skip if we have position or pending order
        if self.position or self.order:
            return
            
        # Entry logic
        current_close = self.dataclose[0]
        current_volume = self.datavolume[0]
        current_atr = self.atr[0]
        resistance_level = self.resistance[-1]
        support_level = self.support[-1]
        
        # Volume check
        volume_ok = current_volume > (self.volume_ma[0] * self.params.volume_threshold)
        
        # LONG ENTRY with dynamic risk calculation
        if (current_close > resistance_level and volume_ok and 
            25 < self.rsi[0] < 75):  # Wider RSI range
            
            breakout_strength = ((current_close - resistance_level) / resistance_level * 100)
            if breakout_strength >= self.params.min_breakout_pct:
                
                # Calculate what our dynamic stops will be
                future_stop = current_close - (current_atr * self.params.stop_atr_mult)
                future_target = current_close + (current_atr * self.params.target_atr_mult)
                risk_reward = (future_target - current_close) / (current_close - future_stop)
                
                self.order = self.buy(size=self.params.position_size)
                self.entry_price = current_close
                self.entry_bar = len(self.data)
                vol_ratio = current_volume / self.volume_ma[0]
                atr_pct = (current_atr / current_close) * 100
                
                self.log(f"🟢 LONG: {current_close:.2f} | ATR: {current_atr:.2f} ({atr_pct:.1f}%) | R:R {risk_reward:.1f}:1 | Vol: {vol_ratio:.1f}x")
            
        # SHORT ENTRY with dynamic risk calculation
        elif (current_close < support_level and volume_ok and 
              25 < self.rsi[0] < 75):
            
            breakdown_strength = ((support_level - current_close) / support_level * 100)
            if breakdown_strength >= self.params.min_breakout_pct:
                
                future_stop = current_close + (current_atr * self.params.stop_atr_mult)
                future_target = current_close - (current_atr * self.params.target_atr_mult)
                risk_reward = (current_close - future_target) / (future_stop - current_close)
                
                self.order = self.sell(size=self.params.position_size)
                self.entry_price = current_close
                self.entry_bar = len(self.data)
                vol_ratio = current_volume / self.volume_ma[0]
                atr_pct = (current_atr / current_close) * 100
                
                self.log(f"🔴 SHORT: {current_close:.2f} | ATR: {current_atr:.2f} ({atr_pct:.1f}%) | R:R {risk_reward:.1f}:1 | Vol: {vol_ratio:.1f}x")
            
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
        
        print(f"\n🏁 DYNAMIC BREAKOUT RESULTS:")
        print(f"💰 Total Return: {total_return:+.2f}%")
        print(f"📈 Daily Average: {daily_return:+.2f}%")
        print(f"🎯 Total Trades: {self.trade_count}")
        print(f"✅ Win Rate: {win_rate:.1f}%")
        print(f"💵 Total PnL: ${self.total_pnl:.2f}")
        
        if self.trade_count > 0:
            avg_trade = self.total_pnl / self.trade_count
            print(f"📊 Average trade: ${avg_trade:.2f}")
        
        if daily_return >= 1.0:
            print("🎯 TARGET ACHIEVED!")
        else:
            print(f"🔧 Need ${(1000 - (total_return * 100)):.0f} more profit for 1% daily")

