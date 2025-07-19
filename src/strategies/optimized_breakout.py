#!/usr/bin/env python3
import sys
sys.path.append("src")
import backtrader as bt
from strategies.dynamic_breakout import DynamicBreakout
from data.providers.yfinance_provider import YFinanceProvider

class OptimizedBreakout(bt.Strategy):
    params = (
        ("lookback_period", 8),
        ("volume_threshold", 0.9),
        ("atr_period", 10),
        ("stop_atr_mult", 1.0),         # Tighter stops: 1.0x ATR
        ("target_atr_mult", 3.5),       # Better R:R: 3.5x ATR (3.5:1 ratio)
        ("max_hold_bars", 25),          # Longer holds for bigger moves
        ("min_breakout_pct", 0.15),
        ("position_size", 600),         # Moderate size per trade
        ("trailing_stop_pct", 0.4),     # 0.4% trailing stop
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
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)
        
        # Trade tracking
        self.order = None
        self.entry_price = 0
        self.entry_bar = 0
        self.stop_price = 0
        self.highest_profit = 0  # For trailing stops
        self.trade_count = 0
        self.wins = 0
        self.total_pnl = 0
        
    def log(self, txt):
        print(f"{txt}")
        
    def next(self):
        if len(self.data) < max(self.params.lookback_period, self.params.atr_period):
            return
            
        # Enhanced position management with trailing stops
        if self.position:
            current_price = self.dataclose[0]
            hold_time = len(self.data) - self.entry_bar
            current_atr = self.atr[0]
            
            if self.position.size > 0:  # Long position
                # Calculate current profit
                current_profit = current_price - self.entry_price
                profit_pct = (current_profit / self.entry_price) * 100
                
                # Update highest profit for trailing stop
                if current_profit > self.highest_profit:
                    self.highest_profit = current_profit
                
                # Dynamic stop and target
                dynamic_stop = self.entry_price - (current_atr * self.params.stop_atr_mult)
                dynamic_target = self.entry_price + (current_atr * self.params.target_atr_mult)
                
                # Trailing stop: if profit > 1%, trail by 0.4%
                if profit_pct > 1.0:
                    trailing_stop = current_price * (1 - self.params.trailing_stop_pct / 100)
                    dynamic_stop = max(dynamic_stop, trailing_stop)
                
                # Exit conditions
                if current_price <= dynamic_stop:
                    self.order = self.close()
                    exit_type = "TRAIL" if profit_pct > 1.0 else "STOP"
                    self.log(f"🛑 {exit_type}: {current_price:.2f} | Profit: {profit_pct:+.2f}%")
                    self.highest_profit = 0
                    return
                elif current_price >= dynamic_target:
                    self.order = self.close()
                    self.log(f"🎯 TARGET: {current_price:.2f} | Profit: {profit_pct:+.2f}%")
                    self.highest_profit = 0
                    return
                elif hold_time >= self.params.max_hold_bars:
                    self.order = self.close()
                    self.log(f"⏰ TIME: {current_price:.2f} | Profit: {profit_pct:+.2f}%")
                    self.highest_profit = 0
                    return
            
            elif self.position.size < 0:  # Short position
                current_profit = self.entry_price - current_price
                profit_pct = (current_profit / self.entry_price) * 100
                
                if current_profit > self.highest_profit:
                    self.highest_profit = current_profit
                
                dynamic_stop = self.entry_price + (current_atr * self.params.stop_atr_mult)
                dynamic_target = self.entry_price - (current_atr * self.params.target_atr_mult)
                
                # Trailing stop for shorts
                if profit_pct > 1.0:
                    trailing_stop = current_price * (1 + self.params.trailing_stop_pct / 100)
                    dynamic_stop = min(dynamic_stop, trailing_stop)
                
                if current_price >= dynamic_stop:
                    self.order = self.close()
                    exit_type = "TRAIL" if profit_pct > 1.0 else "STOP"
                    self.log(f"🛑 SHORT {exit_type}: {current_price:.2f}")
                    self.highest_profit = 0
                    return
                elif current_price <= dynamic_target:
                    self.order = self.close()
                    self.log(f"🎯 SHORT TARGET: {current_price:.2f}")
                    self.highest_profit = 0
                    return
                elif hold_time >= self.params.max_hold_bars:
                    self.order = self.close()
                    self.log(f"⏰ SHORT TIME: {current_price:.2f}")
                    self.highest_profit = 0
                    return
                    
        if self.position or self.order:
            return
            
        # More selective entry criteria
        current_close = self.dataclose[0]
        current_volume = self.datavolume[0]
        current_atr = self.atr[0]
        resistance_level = self.resistance[-1]
        support_level = self.support[-1]
        
        # Enhanced volume confirmation
        volume_confirmed = current_volume > (self.volume_ma[0] * self.params.volume_threshold)
        
        # Better risk/reward calculation
        future_stop_long = current_close - (current_atr * self.params.stop_atr_mult)
        future_target_long = current_close + (current_atr * self.params.target_atr_mult)
        risk_reward_long = (future_target_long - current_close) / (current_close - future_stop_long)
        
        # LONG ENTRY - More selective
        if (current_close > resistance_level and 
            volume_confirmed and 
            30 < self.rsi[0] < 70 and
            risk_reward_long >= 3.0):  # Ensure 3:1 minimum
            
            breakout_strength = ((current_close - resistance_level) / resistance_level * 100)
            if breakout_strength >= self.params.min_breakout_pct:
                self.order = self.buy(size=self.params.position_size)
                self.entry_price = current_close
                self.entry_bar = len(self.data)
                vol_ratio = current_volume / self.volume_ma[0]
                self.log(f"🟢 LONG: {current_close:.2f} | R:R {risk_reward_long:.1f}:1 | Vol: {vol_ratio:.1f}x | RSI: {self.rsi[0]:.1f}")
        
        # SHORT ENTRY - More selective  
        elif (current_close < support_level and 
              volume_confirmed and 
              30 < self.rsi[0] < 70):
            
            future_stop_short = current_close + (current_atr * self.params.stop_atr_mult)
            future_target_short = current_close - (current_atr * self.params.target_atr_mult)
            risk_reward_short = (current_close - future_target_short) / (future_stop_short - current_close)
            
            if risk_reward_short >= 3.0:
                breakdown_strength = ((support_level - current_close) / support_level * 100)
                if breakdown_strength >= self.params.min_breakout_pct:
                    self.order = self.sell(size=self.params.position_size)
                    self.entry_price = current_close
                    self.entry_bar = len(self.data)
                    vol_ratio = current_volume / self.volume_ma[0]
                    self.log(f"�� SHORT: {current_close:.2f} | R:R {risk_reward_short:.1f}:1 | Vol: {vol_ratio:.1f}x")
            
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
        
        print(f"\n🏁 OPTIMIZED RESULTS:")
        print(f"💰 Total Return: {total_return:+.2f}%")
        print(f"📈 Daily Average: {daily_return:+.2f}%")
        print(f"🎯 Total Trades: {self.trade_count}")
        print(f"✅ Win Rate: {win_rate:.1f}%")
        print(f"💵 Total PnL: ${self.total_pnl:.2f}")
        
        if self.trade_count > 0:
            avg_trade = self.total_pnl / self.trade_count
            print(f"📊 Average trade: ${avg_trade:.2f}")

