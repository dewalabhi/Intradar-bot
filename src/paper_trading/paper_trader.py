#!/usr/bin/env python3
"""
🎯 NIFTY 50 PAPER TRADING ENGINE
============================================================
Complete paper trading system for Nifty 50 strategy validation
Logs all trades without actual execution for risk-free testing
"""

import json
import csv
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd


class PaperTrade:
    """Represents a single paper trade"""
    
    def __init__(self, trade_id: str, symbol: str, action: str, price: float, 
                 quantity: int, timestamp: datetime, strategy_signal: str):
        self.trade_id = trade_id
        self.symbol = symbol
        self.action = action  # 'BUY' or 'SELL'
        self.price = price
        self.quantity = quantity
        self.timestamp = timestamp
        self.strategy_signal = strategy_signal
        self.exit_price = None
        self.exit_timestamp = None
        self.pnl = 0.0
        self.status = 'OPEN'  # 'OPEN', 'CLOSED', 'CANCELLED'
        self.hold_duration = None
        
    def close_trade(self, exit_price: float, exit_timestamp: datetime):
        """Close the paper trade and calculate P&L"""
        self.exit_price = exit_price
        self.exit_timestamp = exit_timestamp
        self.hold_duration = exit_timestamp - self.timestamp
        
        if self.action == 'BUY':
            self.pnl = (exit_price - self.price) * self.quantity
        else:  # SELL
            self.pnl = (self.price - exit_price) * self.quantity
            
        self.status = 'CLOSED'
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert trade to dictionary for logging"""
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'action': self.action,
            'entry_price': self.price,
            'exit_price': self.exit_price,
            'quantity': self.quantity,
            'entry_timestamp': self.timestamp.isoformat(),
            'exit_timestamp': self.exit_timestamp.isoformat() if self.exit_timestamp else None,
            'pnl': round(self.pnl, 2),
            'status': self.status,
            'strategy_signal': self.strategy_signal,
            'hold_duration_seconds': self.hold_duration.total_seconds() if self.hold_duration else None
        }


class PaperTradingEngine:
    """
    🎯 Nifty 50 Paper Trading Engine
    Simulates live trading without actual execution
    """
    
    def __init__(self, initial_capital: float = 100000.0, 
                 log_directory: str = "/workspaces/Intradar-bot/data/paper_trading"):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.log_directory = log_directory
        self.trades: Dict[str, PaperTrade] = {}
        self.positions: Dict[str, int] = {}  # symbol -> quantity
        self.trade_counter = 0
        
        # Create log directory
        os.makedirs(log_directory, exist_ok=True)
        
        # Initialize log files
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.trade_log_file = os.path.join(log_directory, f"paper_trades_{self.session_id}.json")
        self.csv_log_file = os.path.join(log_directory, f"paper_trades_{self.session_id}.csv")
        self.performance_file = os.path.join(log_directory, f"performance_{self.session_id}.json")
        
        # Performance tracking
        self.performance_stats = {
            'session_start': datetime.now().isoformat(),
            'initial_capital': initial_capital,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'peak_capital': initial_capital,
            'sectors_traded': set(),
            'symbols_traded': set(),
            'avg_hold_time': None,
            'largest_win': 0.0,
            'largest_loss': 0.0
        }
        
        print(f"🎯 PAPER TRADING INITIALIZED")
        print(f"📁 Session ID: {self.session_id}")
        print(f"💰 Initial Capital: ₹{initial_capital:,.2f}")
        print(f"📊 Logs: {log_directory}")
        
    def generate_trade_signal(self, symbol: str, current_price: float, 
                            strategy_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        🎯 Generate trade signal based on Nifty 50 strategy
        This would be called by your strategy to check if a trade should be executed
        """
        
        # Example strategy logic (you can customize this)
        signal = None
        
        # Check if we have position in this symbol
        current_position = self.positions.get(symbol, 0)
        
        # Extract strategy indicators from your BalancedBreakout strategy
        resistance = strategy_data.get('resistance', 0)
        support = strategy_data.get('support', 0)
        volume_ratio = strategy_data.get('volume_ratio', 0)
        rsi = strategy_data.get('rsi', 50)
        breakout_strength = strategy_data.get('breakout_strength', 0)
        
        # BUY Signal Logic
        if (current_position <= 0 and  # No long position
            current_price > resistance and
            volume_ratio > 1.2 and
            breakout_strength >= 0.003 and
            30 < rsi < 70):
            
            position_size = self.calculate_position_size(symbol, current_price)
            signal = {
                'action': 'BUY',
                'symbol': symbol,
                'price': current_price,
                'quantity': position_size,
                'strategy_signal': f'BREAKOUT_LONG: R:{resistance:.2f}, Vol:{volume_ratio:.1f}x, RSI:{rsi:.1f}',
                'confidence': min(volume_ratio * breakout_strength * 100, 100)
            }
            
        # SELL Signal Logic  
        elif (current_position >= 0 and  # No short position
              current_price < support and
              volume_ratio > 1.2 and
              breakout_strength >= 0.003 and
              30 < rsi < 70):
            
            position_size = self.calculate_position_size(symbol, current_price)
            signal = {
                'action': 'SELL',
                'symbol': symbol,
                'price': current_price,
                'quantity': position_size,
                'strategy_signal': f'BREAKDOWN_SHORT: S:{support:.2f}, Vol:{volume_ratio:.1f}x, RSI:{rsi:.1f}',
                'confidence': min(volume_ratio * breakout_strength * 100, 100)
            }
        
        return signal
        
    def calculate_position_size(self, symbol: str, price: float) -> int:
        """Calculate position size based on Nifty 50 standards"""
        # Standard ₹50,000 position for Nifty 50 stocks
        target_value = 50000
        position_size = int(target_value / price)
        
        # Ensure we don't exceed available capital
        max_affordable = int(self.current_capital * 0.95 / price)  # Use 95% of capital
        position_size = min(position_size, max_affordable)
        
        return max(1, position_size)  # At least 1 share
        
    def execute_paper_trade(self, signal: Dict[str, Any]) -> str:
        """
        📝 Execute a paper trade (logging only, no actual execution)
        Returns trade_id for tracking
        """
        
        self.trade_counter += 1
        trade_id = f"PT_{self.session_id}_{self.trade_counter:04d}"
        
        # Create paper trade
        paper_trade = PaperTrade(
            trade_id=trade_id,
            symbol=signal['symbol'],
            action=signal['action'],
            price=signal['price'],
            quantity=signal['quantity'],
            timestamp=datetime.now(),
            strategy_signal=signal['strategy_signal']
        )
        
        # Update positions
        if signal['action'] == 'BUY':
            self.positions[signal['symbol']] = self.positions.get(signal['symbol'], 0) + signal['quantity']
        else:  # SELL
            self.positions[signal['symbol']] = self.positions.get(signal['symbol'], 0) - signal['quantity']
            
        # Store trade
        self.trades[trade_id] = paper_trade
        
        # Update stats
        self.performance_stats['total_trades'] += 1
        self.performance_stats['symbols_traded'].add(signal['symbol'])
        
        # Calculate sector (basic mapping for Nifty 50)
        sector = self.get_nifty50_sector(signal['symbol'])
        self.performance_stats['sectors_traded'].add(sector)
        
        # Log the trade
        self.log_trade(paper_trade)
        
        # Update available capital (simulate margin usage)
        trade_value = signal['price'] * signal['quantity']
        if signal['action'] == 'BUY':
            self.current_capital -= trade_value * 0.2  # 20% margin
        else:
            self.current_capital -= trade_value * 0.25  # 25% margin for short
            
        print(f"📝 PAPER TRADE EXECUTED:")
        print(f"   🎯 ID: {trade_id}")
        print(f"   📊 {signal['action']} {signal['quantity']} {signal['symbol']} @ ₹{signal['price']:.2f}")
        print(f"   💡 Signal: {signal['strategy_signal']}")
        print(f"   💰 Available Capital: ₹{self.current_capital:,.2f}")
        print(f"   📈 Confidence: {signal.get('confidence', 0):.1f}%")
        
        return trade_id
        
    def close_paper_trade(self, trade_id: str, exit_price: float, exit_reason: str) -> float:
        """
        🚪 Close a paper trade and calculate P&L
        Returns the P&L of the closed trade
        """
        
        if trade_id not in self.trades:
            print(f"❌ Trade ID {trade_id} not found")
            return 0.0
            
        paper_trade = self.trades[trade_id]
        
        if paper_trade.status != 'OPEN':
            print(f"❌ Trade {trade_id} is already {paper_trade.status}")
            return 0.0
            
        # Close the trade
        paper_trade.close_trade(exit_price, datetime.now())
        
        # Update positions
        if paper_trade.action == 'BUY':
            self.positions[paper_trade.symbol] -= paper_trade.quantity
        else:  # SELL
            self.positions[paper_trade.symbol] += paper_trade.quantity
            
        # Update capital
        trade_value = exit_price * paper_trade.quantity
        if paper_trade.action == 'BUY':
            self.current_capital += trade_value  # Get money back + P&L
            self.current_capital += paper_trade.entry_price * paper_trade.quantity * 0.2  # Release margin
        else:
            self.current_capital += paper_trade.entry_price * paper_trade.quantity - trade_value
            self.current_capital += paper_trade.entry_price * paper_trade.quantity * 0.25  # Release margin
            
        # Update performance stats
        self.performance_stats['total_pnl'] += paper_trade.pnl
        
        if paper_trade.pnl > 0:
            self.performance_stats['winning_trades'] += 1
            self.performance_stats['largest_win'] = max(self.performance_stats['largest_win'], paper_trade.pnl)
        else:
            self.performance_stats['losing_trades'] += 1
            self.performance_stats['largest_loss'] = min(self.performance_stats['largest_loss'], paper_trade.pnl)
            
        # Update drawdown
        if self.current_capital > self.performance_stats['peak_capital']:
            self.performance_stats['peak_capital'] = self.current_capital
        else:
            drawdown = (self.performance_stats['peak_capital'] - self.current_capital) / self.performance_stats['peak_capital'] * 100
            self.performance_stats['max_drawdown'] = max(self.performance_stats['max_drawdown'], drawdown)
            
        # Log the closure
        self.log_trade_closure(paper_trade, exit_reason)
        
        print(f"🚪 PAPER TRADE CLOSED:")
        print(f"   🎯 ID: {trade_id}")
        print(f"   📊 {paper_trade.symbol}: ₹{paper_trade.price:.2f} → ₹{exit_price:.2f}")
        print(f"   💰 P&L: ₹{paper_trade.pnl:+,.2f}")
        print(f"   ⏱️ Duration: {paper_trade.hold_duration}")
        print(f"   💡 Reason: {exit_reason}")
        print(f"   🏆 Total P&L: ₹{self.performance_stats['total_pnl']:+,.2f}")
        
        return paper_trade.pnl
        
    def get_nifty50_sector(self, symbol: str) -> str:
        """Map Nifty 50 symbols to sectors"""
        sector_mapping = {
            'RELIANCE.NS': 'Energy',
            'TCS.NS': 'IT Services',
            'HDFCBANK.NS': 'Banking',
            'INFY.NS': 'IT Services',
            'ICICIBANK.NS': 'Banking',
            'HINDUNILVR.NS': 'FMCG',
            'SBIN.NS': 'Banking',
            'BHARTIARTL.NS': 'Telecom',
            'ITC.NS': 'FMCG',
            'KOTAKBANK.NS': 'Banking',
            'LT.NS': 'Engineering',
            'HCLTECH.NS': 'IT Services',
            'AXISBANK.NS': 'Banking',
            'ASIANPAINT.NS': 'Paints',
            'MARUTI.NS': 'Automotive',
            'TITAN.NS': 'Consumer Durables',
            'WIPRO.NS': 'IT Services',
            'ULTRACEMCO.NS': 'Cement',
            'NESTLEIND.NS': 'FMCG',
            'BAJFINANCE.NS': 'Financial Services',
        }
        return sector_mapping.get(symbol, 'Other')
        
    def log_trade(self, trade: PaperTrade):
        """Log trade to files"""
        # JSON log
        trade_data = trade.to_dict()
        
        try:
            if os.path.exists(self.trade_log_file):
                with open(self.trade_log_file, 'r') as f:
                    trades = json.load(f)
            else:
                trades = []
                
            trades.append(trade_data)
            
            with open(self.trade_log_file, 'w') as f:
                json.dump(trades, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error logging to JSON: {e}")
            
        # CSV log
        try:
            file_exists = os.path.exists(self.csv_log_file)
            with open(self.csv_log_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=trade_data.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(trade_data)
        except Exception as e:
            print(f"❌ Error logging to CSV: {e}")
            
    def log_trade_closure(self, trade: PaperTrade, reason: str):
        """Update logs when trade is closed"""
        # Update JSON log
        try:
            with open(self.trade_log_file, 'r') as f:
                trades = json.load(f)
                
            # Find and update the trade
            for t in trades:
                if t['trade_id'] == trade.trade_id:
                    t.update(trade.to_dict())
                    t['exit_reason'] = reason
                    break
                    
            with open(self.trade_log_file, 'w') as f:
                json.dump(trades, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error updating JSON log: {e}")
            
    def get_performance_summary(self) -> Dict[str, Any]:
        """Generate comprehensive performance summary"""
        
        # Calculate additional metrics
        total_trades = self.performance_stats['total_trades']
        winning_trades = self.performance_stats['winning_trades']
        losing_trades = self.performance_stats['losing_trades']
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        total_return = (self.current_capital / self.initial_capital - 1) * 100
        
        # Calculate average hold time
        closed_trades = [t for t in self.trades.values() if t.status == 'CLOSED' and t.hold_duration]
        if closed_trades:
            avg_hold_seconds = sum(t.hold_duration.total_seconds() for t in closed_trades) / len(closed_trades)
            avg_hold_time = str(timedelta(seconds=int(avg_hold_seconds)))
        else:
            avg_hold_time = "N/A"
            
        summary = {
            'session_summary': {
                'session_id': self.session_id,
                'session_start': self.performance_stats['session_start'],
                'session_end': datetime.now().isoformat(),
                'total_duration': str(datetime.now() - datetime.fromisoformat(self.performance_stats['session_start']))
            },
            'capital_analysis': {
                'initial_capital': self.initial_capital,
                'current_capital': self.current_capital,
                'total_pnl': self.performance_stats['total_pnl'],
                'total_return_pct': round(total_return, 2),
                'max_drawdown_pct': round(self.performance_stats['max_drawdown'], 2),
                'peak_capital': self.performance_stats['peak_capital']
            },
            'trading_stats': {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate_pct': round(win_rate, 1),
                'avg_trade_pnl': round(self.performance_stats['total_pnl'] / total_trades, 2) if total_trades > 0 else 0,
                'largest_win': self.performance_stats['largest_win'],
                'largest_loss': self.performance_stats['largest_loss'],
                'avg_hold_time': avg_hold_time
            },
            'market_coverage': {
                'symbols_traded': list(self.performance_stats['symbols_traded']),
                'sectors_traded': list(self.performance_stats['sectors_traded']),
                'total_symbols': len(self.performance_stats['symbols_traded']),
                'total_sectors': len(self.performance_stats['sectors_traded'])
            },
            'current_positions': dict(self.positions),
            'open_trades': len([t for t in self.trades.values() if t.status == 'OPEN'])
        }
        
        return summary
        
    def save_performance_summary(self):
        """Save performance summary to file"""
        summary = self.get_performance_summary()
        
        try:
            with open(self.performance_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            print(f"📊 Performance summary saved: {self.performance_file}")
        except Exception as e:
            print(f"❌ Error saving performance summary: {e}")
            
    def print_live_summary(self):
        """Print live performance summary to console"""
        summary = self.get_performance_summary()
        
        print("\n" + "="*60)
        print("📊 LIVE PAPER TRADING SUMMARY")
        print("="*60)
        
        # Capital Analysis
        cap = summary['capital_analysis']
        print(f"\n💰 CAPITAL ANALYSIS:")
        print(f"   Initial:     ₹{cap['initial_capital']:,.2f}")
        print(f"   Current:     ₹{cap['current_capital']:,.2f}")
        print(f"   P&L:         ₹{cap['total_pnl']:+,.2f}")
        print(f"   Return:      {cap['total_return_pct']:+.2f}%")
        print(f"   Max DD:      -{cap['max_drawdown_pct']:.2f}%")
        
        # Trading Stats
        stats = summary['trading_stats']
        print(f"\n📈 TRADING STATISTICS:")
        print(f"   Total Trades: {stats['total_trades']}")
        print(f"   Win Rate:     {stats['win_rate_pct']:.1f}%")
        print(f"   Avg P&L:      ₹{stats['avg_trade_pnl']:+,.2f}")
        print(f"   Best Trade:   ₹{stats['largest_win']:+,.2f}")
        print(f"   Worst Trade:  ₹{stats['largest_loss']:+,.2f}")
        print(f"   Avg Hold:     {stats['avg_hold_time']}")
        
        # Market Coverage
        market = summary['market_coverage']
        print(f"\n🎯 MARKET COVERAGE:")
        print(f"   Symbols:     {market['total_symbols']} ({', '.join(list(market['symbols_traded'])[:5])}{'...' if len(market['symbols_traded']) > 5 else ''})")
        print(f"   Sectors:     {market['total_sectors']} ({', '.join(market['sectors_traded'])})")
        
        # Current Status
        print(f"\n📊 CURRENT STATUS:")
        print(f"   Open Trades:  {summary['open_trades']}")
        active_positions = {k: v for k, v in summary['current_positions'].items() if v != 0}
        print(f"   Positions:    {len(active_positions)} active")
        for symbol, qty in list(active_positions.items())[:3]:
            print(f"                {symbol}: {qty:+d}")
            
        print("="*60)
        
    def cleanup_session(self):
        """Clean up and save final results"""
        print(f"\n🎯 PAPER TRADING SESSION ENDING...")
        
        # Close any remaining open trades (simulate market close)
        open_trades = [t for t in self.trades.values() if t.status == 'OPEN']
        for trade in open_trades:
            # Simulate closing at last known price
            self.close_paper_trade(trade.trade_id, trade.price, "SESSION_END")
            
        # Save final performance summary
        self.save_performance_summary()
        
        # Print final summary
        self.print_live_summary()
        
        print(f"\n✅ Paper trading session completed!")
        print(f"📁 All logs saved to: {self.log_directory}")
        print(f"🎯 Session ID: {self.session_id}")
