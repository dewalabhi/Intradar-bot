"""
Moving Average Crossover Strategy
A classic trend-following strategy using dual moving averages.
"""

import backtrader as bt


class MovingAverageCrossover(bt.Strategy):
    """Simple Moving Average Crossover Strategy"""
    
    params = (
        ('fast_period', 10),
        ('slow_period', 30),
        ('ma_type', 'EMA'),
        ('enabled', True),
    )
    
    def __init__(self):
        """Initialize strategy indicators"""
        
        # Create moving averages based on type
        if self.params.ma_type == 'EMA':
            self.fast_ma = bt.indicators.ExponentialMovingAverage(
                self.data.close, period=self.params.fast_period
            )
            self.slow_ma = bt.indicators.ExponentialMovingAverage(
                self.data.close, period=self.params.slow_period
            )
        else:  # SMA
            self.fast_ma = bt.indicators.SimpleMovingAverage(
                self.data.close, period=self.params.fast_period
            )
            self.slow_ma = bt.indicators.SimpleMovingAverage(
                self.data.close, period=self.params.slow_period
            )
        
        # Create crossover signal
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        
        # Track orders and trades
        self.order = None
        self.trade_count = 0
    
    def log(self, txt, dt=None):
        """Logging function for strategy events"""
        dt = dt or self.datas[0].datetime.date(0)
        symbol = self.data._name if hasattr(self.data, '_name') else 'Unknown'
        print(f'{dt.isoformat()} [{symbol}] {txt}')
    
    def notify_order(self, order):
        """Handle order notifications"""
        if order.status in [order.Submitted, order.Accepted]:
            # Order submitted/accepted - nothing to do
            return

        # Check if order is completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED: Price: {order.executed.price:.2f}, '
                        f'Size: {order.executed.size}, '
                        f'Cost: {order.executed.value:.2f}, '
                        f'Comm: {order.executed.comm:.2f}')
            else:
                self.log(f'SELL EXECUTED: Price: {order.executed.price:.2f}, '
                        f'Size: {order.executed.size}, '
                        f'Cost: {order.executed.value:.2f}, '
                        f'Comm: {order.executed.comm:.2f}')

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'Order Canceled/Margin/Rejected: {order.status}')

        # Reset order
        self.order = None

    def notify_trade(self, trade):
        """Handle trade notifications"""
        if not trade.isclosed:
            return

        self.trade_count += 1
        pnl_pct = (trade.pnl / trade.price) * 100 if trade.price != 0 else 0
        
        self.log(f'TRADE #{self.trade_count} CLOSED: '
                f'PnL: ${trade.pnl:.2f} ({pnl_pct:.2f}%), '
                f'Gross: ${trade.pnlcomm:.2f}')

    def next(self):
        """Main strategy logic - called for each bar"""
        
        # Skip if we have a pending order
        if self.order:
            return

        # Check if we're in the market
        if not self.position:
            # Look for buy signal: fast MA crosses above slow MA
            if self.crossover > 0:
                self.log(f'BUY SIGNAL: Fast MA crosses above Slow MA')
                self.log(f'Fast MA: {self.fast_ma[0]:.2f}, Slow MA: {self.slow_ma[0]:.2f}')
                
                # Calculate position size (use 95% of available cash)
                available_cash = self.broker.getcash()
                price = self.data.close[0]
                size = int((available_cash * 0.95) / price)
                
                if size > 0:
                    self.order = self.buy(size=size)
        else:
            # Look for sell signal: fast MA crosses below slow MA
            if self.crossover < 0:
                self.log(f'SELL SIGNAL: Fast MA crosses below Slow MA')
                self.log(f'Fast MA: {self.fast_ma[0]:.2f}, Slow MA: {self.slow_ma[0]:.2f}')
                
                # Close position
                self.order = self.close()

    def stop(self):
        """Called when strategy stops"""
        self.log(f'Strategy finished with {self.trade_count} trades')
        final_value = self.broker.getvalue()
        self.log(f'Final Portfolio Value: ${final_value:,.2f}')
