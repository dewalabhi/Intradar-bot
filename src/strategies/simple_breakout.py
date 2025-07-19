import backtrader as bt

class SimpleBreakout(bt.Strategy):
    params = (
        ("lookback_period", 8),
        ("volume_threshold", 0.9),
        ("atr_period", 10),
        ("stop_atr_mult", 1.0),
        ("target_atr_mult", 3.0),
        ("position_size", 600),
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume
        
        self.resistance = bt.indicators.Highest(self.datahigh, period=self.params.lookback_period)
        self.support = bt.indicators.Lowest(self.datalow, period=self.params.lookback_period)
        self.volume_ma = bt.indicators.SMA(self.datavolume, period=15)
        self.rsi = bt.indicators.RSI(self.dataclose, period=10)
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)
        
        self.order = None
        self.entry_price = 0
        self.trade_count = 0
        self.wins = 0
        self.total_pnl = 0
        
    def next(self):
        if len(self.data) < max(self.params.lookback_period, self.params.atr_period):
            return
            
        # Simple exit management
        if self.position:
            current_price = self.dataclose[0]
            current_atr = self.atr[0]
            
            if self.position.size > 0:  # Long
                stop_price = self.entry_price - (current_atr * self.params.stop_atr_mult)
                target_price = self.entry_price + (current_atr * self.params.target_atr_mult)
                
                if current_price <= stop_price or current_price >= target_price:
                    self.order = self.close()
                    return
            
            elif self.position.size < 0:  # Short
                stop_price = self.entry_price + (current_atr * self.params.stop_atr_mult)
                target_price = self.entry_price - (current_atr * self.params.target_atr_mult)
                
                if current_price >= stop_price or current_price <= target_price:
                    self.order = self.close()
                    return
                    
        if self.position or self.order:
            return
            
        # Simple entry logic
        current_close = self.dataclose[0]
        current_volume = self.datavolume[0]
        resistance_level = self.resistance[-1]
        support_level = self.support[-1]
        
        volume_ok = current_volume > (self.volume_ma[0] * self.params.volume_threshold)
        
        # Long entry
        if (current_close > resistance_level and volume_ok and 30 < self.rsi[0] < 70):
            self.order = self.buy(size=self.params.position_size)
            self.entry_price = current_close
            print(f"LONG: {current_close:.2f}")
            
        # Short entry
        elif (current_close < support_level and volume_ok and 30 < self.rsi[0] < 70):
            self.order = self.sell(size=self.params.position_size)
            self.entry_price = current_close
            print(f"SHORT: {current_close:.2f}")
            
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.issell() and self.entry_price > 0:
                pnl = (order.executed.price - self.entry_price) * order.executed.size
                self.total_pnl += pnl
                self.trade_count += 1
                if pnl > 0:
                    self.wins += 1
                print(f"EXIT: {order.executed.price:.2f} | PnL: ${pnl:.2f}")
                self.entry_price = 0
        self.order = None
        
    def stop(self):
        win_rate = (self.wins / self.trade_count * 100) if self.trade_count > 0 else 0
        daily_return = (self.total_pnl / 100000) * 100 / 10
        
        print(f"Return: {daily_return:+.2f}% daily")
        print(f"Trades: {self.trade_count}")
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Total PnL: ${self.total_pnl:.2f}")

