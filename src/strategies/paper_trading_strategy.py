#!/usr/bin/env python3
"""
🎯 NIFTY 50 PAPER TRADING STRATEGY
============================================================
Enhanced BalancedBreakout strategy with paper trading integration
Logs all trades without actual execution for risk-free validation
"""

import backtrader as bt
from datetime import datetime, time
import sys
import os

# Add paper trading engine to path
sys.path.append('/workspaces/Intradar-bot/src')
from paper_trading.paper_trader import PaperTradingEngine


class PaperTradingBalancedBreakout(bt.Strategy):
    """
    Enhanced Nifty 50 strategy with paper trading integration
    All trades are logged but not executed
    """
    
    params = (
        ("lookback_period", 5),
        ("volume_threshold", 0.3),
        ("stop_loss_pct", 0.15),
        ("take_profit_pct", 0.20),
        ("max_hold_bars", 8),
        ("min_breakout_pct", 0.003),
        ("position_size", 1500),
        ("trade_start_hour", 9),
        ("trade_end_hour", 15),
        ("min_rsi_spread", 10),
        ("volume_spike_threshold", 1.3),
        ("paper_trading", True),  # Enable paper trading mode
    )
    
    def __init__(self):
        # Initialize indicators (same as original strategy)
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume
        
        self.resistance = bt.indicators.Highest(self.datahigh, period=self.params.lookback_period)
        self.support = bt.indicators.Lowest(self.datalow, period=self.params.lookback_period)
        self.volume_ma = bt.indicators.SMA(self.datavolume, period=8)
        self.rsi = bt.indicators.RSI(self.dataclose, period=4)
        self.price_ma = bt.indicators.SMA(self.dataclose, period=3)
        self.volume_ratio = self.datavolume / self.volume_ma
        self.atr = bt.indicators.ATR(self.datas[0], period=8)
        
        # Trade tracking
        self.order = None
        self.entry_price = 0
        self.entry_bar = 0
        self.trade_count = 0
        self.wins = 0
        self.total_pnl = 0
        
        # Paper trading integration
        if self.params.paper_trading:
            self.paper_engine = PaperTradingEngine(
                initial_capital=100000.0,
                log_directory="/workspaces/Intradar-bot/data/paper_trading"
            )
            self.paper_trades = {}  # trade_id -> paper_trade mapping
            
        # Nifty 50 optimized parameters
        self.nifty50_params = {
            'base_position_size': 50000,
            'volatility_threshold': 0.0006,
            'volume_multiplier': 0.8,
            'stop_loss_mult': 0.9,
            'circuit_risk_low': True,
            'optimal_trading_window': (9.5, 15.0),
        }
        
    def is_nifty50_stock(self, symbol):
        """Check if symbol is in Nifty 50"""
        nifty50_stocks = [
            'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'HINDUNILVR',
            'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK', 'LT', 'HCLTECH',
            'AXISBANK', 'ASIANPAINT', 'MARUTI', 'TITAN', 'WIPRO', 'ULTRACEMCO',
            'NESTLEIND', 'BAJFINANCE', 'POWERGRID', 'M&M', 'NTPC', 'ONGC',
            'SUNPHARMA', 'TECHM', 'TATAMOTORS', 'BAJAJFINSV', 'DRREDDY',
            'EICHERMOT', 'GRASIM', 'BRITANNIA', 'JSWSTEEL', 'COALINDIA',
            'TATASTEEL', 'HINDALCO', 'CIPLA', 'HEROMOTOCO', 'SHREECEM',
            'DIVISLAB', 'APOLLOHOSP', 'ADANIPORTS', 'TATACONSUM', 'UPL',
            'BAJAJ-AUTO', 'BPCL', 'IOC', 'INDUSINDBK', 'SBILIFE', 'HDFCLIFE'
        ]
        
        # Remove .NS suffix if present
        clean_symbol = symbol.replace('.NS', '')
        return clean_symbol in nifty50_stocks
        
    def log(self, txt):
        """Enhanced logging with paper trading info"""
        dt = self.datas[0].datetime.datetime(0)
        symbol = getattr(self.datas[0], '_name', 'UNKNOWN')
        prefix = "📝 PAPER" if self.params.paper_trading else "🔥 LIVE"
        print(f'{prefix} [{dt}] [{symbol}] {txt}')
        
    def get_current_symbol(self):
        """Get the current symbol being processed"""
        return getattr(self.datas[0], '_name', 'UNKNOWN')
        
    def is_market_hours(self):
        """Check if current time is within trading hours"""
        try:
            current_time = self.datas[0].datetime.time(0)
            start_time = time(self.params.trade_start_hour, 30)
            end_time = time(self.params.trade_end_hour, 0)
            return start_time <= current_time <= end_time
        except:
            return True  # Default to allowing trades if time check fails
            
    def should_trade_symbol(self):
        """Enhanced symbol validation for Nifty 50 focus"""
        symbol = self.get_current_symbol()
        
        # Must be Nifty 50 stock
        if not self.is_nifty50_stock(symbol):
            return False, "NOT_NIFTY50"
            
        # Must be within market hours
        if not self.is_market_hours():
            return False, "OUTSIDE_HOURS"
            
        return True, "VALID"
        
    def generate_strategy_signal(self, action: str) -> dict:
        """Generate detailed strategy signal data"""
        current_price = self.dataclose[0]
        resistance_level = self.resistance[0]
        support_level = self.support[0]
        volume_ratio = self.volume_ratio[0]
        rsi_value = self.rsi[0]
        
        if action == "BUY":
            breakout_strength = (current_price - resistance_level) / resistance_level
        else:
            breakout_strength = (support_level - current_price) / support_level
            
        return {
            'resistance': resistance_level,
            'support': support_level,
            'volume_ratio': volume_ratio,
            'rsi': rsi_value,
            'breakout_strength': abs(breakout_strength),
            'current_price': current_price,
            'atr': self.atr[0]
        }
        
    def execute_paper_trade(self, action: str, reason: str) -> str:
        """Execute paper trade instead of real trade"""
        symbol = self.get_current_symbol()
        current_price = self.dataclose[0]
        
        # Generate strategy data
        strategy_data = self.generate_strategy_signal(action)
        
        # Create trade signal
        signal = self.paper_engine.generate_trade_signal(symbol, current_price, strategy_data)
        
        if signal:
            # Override with our specific signal
            signal['action'] = action
            signal['strategy_signal'] = reason
            
            # Execute paper trade
            trade_id = self.paper_engine.execute_paper_trade(signal)
            
            # Store for exit tracking
            self.paper_trades[len(self.paper_trades)] = {
                'trade_id': trade_id,
                'entry_price': current_price,
                'entry_bar': len(self),
                'action': action,
                'symbol': symbol
            }
            
            # Update our tracking
            self.entry_price = current_price
            self.entry_bar = len(self)
            self.trade_count += 1
            
            return trade_id
        
        return None
        
    def check_exit_conditions(self, paper_trade_info: dict) -> tuple:
        """Check if we should exit the paper trade"""
        current_price = self.dataclose[0]
        entry_price = paper_trade_info['entry_price']
        entry_bar = paper_trade_info['entry_bar']
        action = paper_trade_info['action']
        
        hold_bars = len(self) - entry_bar
        
        # Time-based exit
        if hold_bars >= self.params.max_hold_bars:
            return True, "TIME_EXIT", current_price
            
        # Profit/Loss exits
        if action == "BUY":
            # Long position exits
            profit_pct = (current_price - entry_price) / entry_price
            if profit_pct >= self.params.take_profit_pct / 100:
                return True, "TAKE_PROFIT", current_price
            elif profit_pct <= -self.params.stop_loss_pct / 100:
                return True, "STOP_LOSS", current_price
        else:
            # Short position exits  
            profit_pct = (entry_price - current_price) / entry_price
            if profit_pct >= self.params.take_profit_pct / 100:
                return True, "TAKE_PROFIT", current_price
            elif profit_pct <= -self.params.stop_loss_pct / 100:
                return True, "STOP_LOSS", current_price
                
        return False, "", current_price
        
    def next(self):
        """Main strategy logic with paper trading"""
        
        # Skip if insufficient data
        if len(self.data) < max(self.params.lookback_period, 8):
            return
            
        # Validate trading conditions
        can_trade, reason = self.should_trade_symbol()
        if not can_trade:
            return
            
        # Check exits for open paper trades
        for key, paper_trade_info in list(self.paper_trades.items()):
            should_exit, exit_reason, exit_price = self.check_exit_conditions(paper_trade_info)
            
            if should_exit:
                # Close paper trade
                pnl = self.paper_engine.close_paper_trade(
                    paper_trade_info['trade_id'], 
                    exit_price, 
                    exit_reason
                )
                
                # Update our stats
                self.total_pnl += pnl
                if pnl > 0:
                    self.wins += 1
                    
                # Remove from active trades
                del self.paper_trades[key]
                
                self.log(f"🚪 EXIT: {exit_reason} | P&L: ₹{pnl:+,.2f}")
                
        # Skip if we already have open paper trades (single position strategy)
        if self.paper_trades:
            return
            
        # Entry logic
        current_price = self.dataclose[0]
        current_volume = self.datavolume[0]
        resistance_level = self.resistance[0]
        support_level = self.support[0]
        volume_ratio = self.volume_ratio[0]
        rsi_value = self.rsi[0]
        
        # Volume validation
        volume_threshold_mult = 1.5 if self.is_nifty50_stock(self.get_current_symbol()) else 2.0
        base_volume_threshold = 0.8 * volume_threshold_mult
        volume_ok = current_volume > (self.volume_ma[0] * base_volume_threshold)
        
        # LONG ENTRY
        if (current_price > resistance_level and volume_ok and 
            30 < rsi_value < 70):
            
            breakout_strength = (current_price - resistance_level) / resistance_level * 100
            
            if breakout_strength >= self.params.min_breakout_pct:
                reason = (f"🟢 LONG BREAKOUT: ₹{current_price:.2f} > R:₹{resistance_level:.2f} "
                         f"({breakout_strength:.2f}%) | Vol:{volume_ratio:.1f}x | RSI:{rsi_value:.1f}")
                
                trade_id = self.execute_paper_trade("BUY", reason)
                if trade_id:
                    self.log(reason)
                    
        # SHORT ENTRY
        elif (current_price < support_level and volume_ok and 
              30 < rsi_value < 70):
            
            breakdown_strength = (support_level - current_price) / support_level * 100
            
            if breakdown_strength >= self.params.min_breakout_pct:
                reason = (f"🔴 SHORT BREAKDOWN: ₹{current_price:.2f} < S:₹{support_level:.2f} "
                         f"({breakdown_strength:.2f}%) | Vol:{volume_ratio:.1f}x | RSI:{rsi_value:.1f}")
                
                trade_id = self.execute_paper_trade("SELL", reason)
                if trade_id:
                    self.log(reason)
                    
    def stop(self):
        """Strategy finished - print paper trading summary"""
        symbol = self.get_current_symbol()
        
        if self.params.paper_trading:
            self.log(f"📊 PAPER TRADING COMPLETE for {symbol}")
            self.log(f"🎯 Total Trades: {self.trade_count}")
            self.log(f"💰 Total P&L: ₹{self.total_pnl:+,.2f}")
            self.log(f"✅ Win Rate: {(self.wins/max(1, self.trade_count)*100):.1f}%")
            
            # Print live summary
            self.paper_engine.print_live_summary()
        else:
            self.log(f"🔥 LIVE TRADING COMPLETE for {symbol}")
            self.log(f"🎯 Total Trades: {self.trade_count}")
            
    def get_paper_trading_summary(self):
        """Get comprehensive paper trading summary"""
        if self.params.paper_trading and hasattr(self, 'paper_engine'):
            return self.paper_engine.get_performance_summary()
        return None
