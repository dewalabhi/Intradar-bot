import backtrader as bt

class FixedBreakout(bt.Strategy):
    params = (
        ('lookback_period', 6),
        ('volume_threshold', 0.7),
        ('risk_per_trade', 0.015),
        ('max_hold_bars', 20),
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume
        self.resistance = bt.indicators.Highest(self.datahigh, period=self.params.lookback_period)
        self.volume_ma = bt.indicators.SMA(self.datavolume, period=20)
        self.order = None
        self.entry_bar = 0
        self.trade_count = 0
        
    def next(self):
        if len(self.data) < self.params.lookback_period:
            return
            
        if self.position and (len(self.data) - self.entry_bar) >= self.params.max_hold_bars:
            self.order = self.close()
            return
            
        if self.position or self.order:
            return
            
        current_close = self.dataclose[0]
        resistance_level = self.resistance[-1]
        volume_ok = self.datavolume[0] > (self.volume_ma[0] * self.params.volume_threshold)
        
        if current_close > resistance_level and volume_ok:
            self.order = self.buy(size=500)
            self.entry_bar = len(self.data)
            print(f'LONG at {current_close:.2f}')
            
    def notify_order(self, order):
        if order.status in [order.Completed]:
            self.trade_count += 1
            print(f'Order executed: {order.executed.price:.2f}')
        self.order = None
        
    def stop(self):
        final_value = self.broker.get_value()
        total_return = ((final_value / 100000) - 1) * 100
        daily_return = total_return / 10
        print(f'Return: {total_return:+.2f}%, Daily: {daily_return:+.2f}%, Trades: {self.trade_count}')

