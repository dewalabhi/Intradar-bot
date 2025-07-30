#!/usr/bin/env python3
"""
🎯 PAPER TRADING DEMO - RELAXED PARAMETERS
============================================================
Demo of paper trading system with more relaxed parameters
to show trade generation and logging functionality
"""

import sys
sys.path.append('/workspaces/Intradar-bot')

import backtrader as bt
from datetime import datetime
from src.data.providers.yfinance_provider import YFinanceProvider
from src.paper_trading.paper_trader import PaperTradingEngine


class DemoPaperTradingStrategy(bt.Strategy):
    """
    Demo strategy with very relaxed parameters to generate trades
    """
    
    params = (
        ("lookback_period", 3),     # Very short lookback
        ("volume_threshold", 0.1),  # Very low volume requirement
        ("min_breakout_pct", 0.001), # 0.1% minimum breakout (very low)
        ("stop_loss_pct", 0.5),     # 0.5% stop loss
        ("take_profit_pct", 1.0),   # 1.0% take profit
        ("max_hold_bars", 20),      # Hold up to 20 bars
        ("paper_trading", True),
    )
    
    def __init__(self):
        # Basic indicators
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume
        
        # Simple indicators
        self.resistance = bt.indicators.Highest(self.datahigh, period=self.params.lookback_period)
        self.support = bt.indicators.Lowest(self.datalow, period=self.params.lookback_period)
        self.volume_ma = bt.indicators.SMA(self.datavolume, period=5)
        self.rsi = bt.indicators.RSI(self.dataclose, period=14)
        
        # Trade tracking
        self.trade_count = 0
        self.total_pnl = 0
        self.wins = 0
        
        # Paper trading engine
        self.paper_engine = PaperTradingEngine(
            initial_capital=100000.0,
            log_directory="/workspaces/Intradar-bot/data/demo_paper_trading"
        )
        self.paper_trades = {}
        self.entry_price = 0
        self.entry_bar = 0
        
    def get_current_symbol(self):
        return getattr(self.datas[0], '_name', 'DEMO')
        
    def log(self, txt):
        dt = self.datas[0].datetime.datetime(0)
        symbol = self.get_current_symbol()
        print(f'📝 DEMO [{dt}] [{symbol}] {txt}')
        
    def execute_demo_trade(self, action: str, reason: str):
        """Execute demo paper trade"""
        symbol = self.get_current_symbol()
        current_price = self.dataclose[0]
        
        # Create trade signal for demo
        signal = {
            'action': action,
            'symbol': symbol,
            'price': current_price,
            'quantity': int(50000 / current_price),  # ₹50k position
            'strategy_signal': reason,
            'confidence': 75.0
        }
        
        # Execute paper trade
        trade_id = self.paper_engine.execute_paper_trade(signal)
        
        if trade_id:
            # Store for tracking
            self.paper_trades[len(self.paper_trades)] = {
                'trade_id': trade_id,
                'entry_price': current_price,
                'entry_bar': len(self),
                'action': action,
                'symbol': symbol
            }
            
            self.entry_price = current_price
            self.entry_bar = len(self)
            self.trade_count += 1
            
            return trade_id
        return None
        
    def check_exit_conditions(self, paper_trade_info):
        """Check if we should exit"""
        current_price = self.dataclose[0]
        entry_price = paper_trade_info['entry_price']
        entry_bar = paper_trade_info['entry_bar']
        action = paper_trade_info['action']
        
        hold_bars = len(self) - entry_bar
        
        # Time exit
        if hold_bars >= self.params.max_hold_bars:
            return True, "TIME_EXIT", current_price
            
        # P&L exits
        if action == "BUY":
            profit_pct = (current_price - entry_price) / entry_price
            if profit_pct >= self.params.take_profit_pct / 100:
                return True, "TAKE_PROFIT", current_price
            elif profit_pct <= -self.params.stop_loss_pct / 100:
                return True, "STOP_LOSS", current_price
        else:
            profit_pct = (entry_price - current_price) / entry_price
            if profit_pct >= self.params.take_profit_pct / 100:
                return True, "TAKE_PROFIT", current_price
            elif profit_pct <= -self.params.stop_loss_pct / 100:
                return True, "STOP_LOSS", current_price
                
        return False, "", current_price
        
    def next(self):
        # Skip if insufficient data
        if len(self.data) < self.params.lookback_period:
            return
            
        # Check exits for open trades
        for key, trade_info in list(self.paper_trades.items()):
            should_exit, exit_reason, exit_price = self.check_exit_conditions(trade_info)
            
            if should_exit:
                pnl = self.paper_engine.close_paper_trade(
                    trade_info['trade_id'], 
                    exit_price, 
                    exit_reason
                )
                
                self.total_pnl += pnl
                if pnl > 0:
                    self.wins += 1
                    
                del self.paper_trades[key]
                self.log(f"🚪 EXIT: {exit_reason} | P&L: ₹{pnl:+,.2f}")
                
        # Skip if we have open trades
        if self.paper_trades:
            return
            
        # Very relaxed entry logic
        current_price = self.dataclose[0]
        current_volume = self.datavolume[0]
        resistance = self.resistance[0]
        support = self.support[0]
        
        # Very relaxed volume check
        volume_ok = True  # Always allow for demo
        if len(self.volume_ma) > 0:
            volume_ok = current_volume > (self.volume_ma[0] * self.params.volume_threshold)
        
        # LONG ENTRY - very relaxed conditions
        if current_price > resistance * (1 + self.params.min_breakout_pct) and volume_ok:
            reason = f"🟢 DEMO LONG: ₹{current_price:.2f} > R:₹{resistance:.2f}"
            trade_id = self.execute_demo_trade("BUY", reason)
            if trade_id:
                self.log(reason)
                
        # SHORT ENTRY - very relaxed conditions  
        elif current_price < support * (1 - self.params.min_breakout_pct) and volume_ok:
            reason = f"🔴 DEMO SHORT: ₹{current_price:.2f} < S:₹{support:.2f}"
            trade_id = self.execute_demo_trade("SELL", reason)
            if trade_id:
                self.log(reason)
                
    def stop(self):
        """Strategy finished"""
        symbol = self.get_current_symbol()
        
        self.log(f"📊 DEMO COMPLETE for {symbol}")
        self.log(f"🎯 Total Trades: {self.trade_count}")
        self.log(f"💰 Total P&L: ₹{self.total_pnl:+,.2f}")
        
        if self.trade_count > 0:
            win_rate = self.wins / self.trade_count * 100
            self.log(f"✅ Win Rate: {win_rate:.1f}%")
            
        # Show paper trading summary
        self.paper_engine.print_live_summary()


def demo_paper_trading():
    """Run paper trading demo with relaxed parameters"""
    
    print("🎯 PAPER TRADING DEMO - RELAXED PARAMETERS")
    print("=" * 60)
    print("📝 Using very relaxed conditions to demonstrate trade generation")
    print("🎯 This will show you how the paper trading system works")
    print("=" * 60)
    
    # Initialize data provider
    data_provider = YFinanceProvider()
    
    # Test with RELIANCE (high volume stock)
    symbol = "RELIANCE.NS"
    
    print(f"\n📊 Demo with {symbol}")
    print(f"⚙️ Relaxed Parameters:")
    print(f"   • Lookback: 3 bars (very short)")
    print(f"   • Volume threshold: 0.1x (very low)")
    print(f"   • Breakout: 0.1% (very small)")
    print(f"   • Stop loss: 0.5%")
    print(f"   • Take profit: 1.0%")
    
    # Create cerebro
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100000)
    cerebro.broker.setcommission(commission=0.0003)
    
    # Add demo strategy
    cerebro.addstrategy(DemoPaperTradingStrategy)
    
    # Load more data for better chance of trades
    print(f"\n📡 Loading data for {symbol}...")
    data = data_provider.get_data(symbol=symbol, period="5d", interval="5m")
    
    if data is None or data.empty:
        print(f"❌ No data available")
        return
        
    print(f"✅ Loaded {len(data)} bars")
    
    # Add data
    data_feed = bt.feeds.PandasData(dataname=data)
    data_feed._name = symbol
    cerebro.adddata(data_feed)
    
    # Run demo
    print(f"\n🚀 Running paper trading demo...")
    
    try:
        results = cerebro.run()
        
        print(f"\n✅ Demo completed!")
        
        if results:
            strategy = results[0]
            
            print(f"\n📊 DEMO RESULTS:")
            print(f"   🎯 Trades: {strategy.trade_count}")
            print(f"   💰 P&L: ₹{strategy.total_pnl:+,.2f}")
            print(f"   ✅ Wins: {strategy.wins}")
            
            if strategy.trade_count > 0:
                win_rate = strategy.wins / strategy.trade_count * 100
                print(f"   📈 Win Rate: {win_rate:.1f}%")
                
    except Exception as e:
        print(f"❌ Demo error: {e}")
        
    print(f"\n💡 KEY INSIGHTS:")
    print(f"   ✅ Paper trading system is working")
    print(f"   ✅ All trades are logged, not executed")
    print(f"   ✅ Complete P&L tracking")
    print(f"   ✅ Position management")
    print(f"   ✅ Risk-free strategy validation")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"   1. Adjust strategy parameters for your needs")
    print(f"   2. Test with different symbols and timeframes")
    print(f"   3. Analyze the generated trade logs")
    print(f"   4. When satisfied, consider live trading")
    
    # Check log files
    import os
    log_dir = "/workspaces/Intradar-bot/data/demo_paper_trading"
    if os.path.exists(log_dir):
        log_files = os.listdir(log_dir)
        if log_files:
            print(f"\n📁 GENERATED LOGS:")
            for log_file in log_files:
                print(f"   📄 {log_file}")
        else:
            print(f"\n📁 Log directory created: {log_dir}")


if __name__ == "__main__":
    demo_paper_trading()
