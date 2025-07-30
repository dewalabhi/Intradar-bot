#!/usr/bin/env python3
"""
🎯 PAPER TRADING MANAGER
============================================================
Advanced paper trading system with comprehensive logging and analytics
Integrates with Fyers broker for realistic simulation
"""

import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import csv
from dataclasses import dataclass, asdict

from .fyers_broker import FyersBroker, Order, OrderSide, OrderType, ProductType

@dataclass
class TradeLog:
    """Individual trade log entry"""
    timestamp: str
    order_id: str
    symbol: str
    side: str
    qty: int
    price: float
    order_value: float
    pnl: float = 0.0
    cumulative_pnl: float = 0.0
    strategy: str = "Unknown"
    reason: str = ""
    
@dataclass
class PerformanceMetrics:
    """Trading performance metrics"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    average_profit: float = 0.0
    average_loss: float = 0.0
    max_profit: float = 0.0
    max_loss: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    
class PaperTradingManager:
    """
    🎯 Complete Paper Trading Management System
    
    Features:
    - Trade execution simulation
    - Comprehensive logging
    - Performance analytics  
    - Risk management
    - Portfolio tracking
    - Strategy validation
    """
    
    def __init__(self, 
                 broker: FyersBroker,
                 initial_capital: float = 100000.0,
                 log_directory: str = "data/paper_trading"):
        """
        Initialize paper trading manager
        
        Args:
            broker: Fyers broker instance (must be in paper trading mode)
            initial_capital: Starting capital amount
            log_directory: Directory to save logs and reports
        """
        if not broker.paper_trading:
            raise ValueError("Broker must be in paper trading mode")
            
        self.broker = broker
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # Trade tracking
        self.trade_logs: List[TradeLog] = []
        self.daily_pnl: Dict[str, float] = {}
        self.portfolio_history: List[Dict] = []
        
        # Performance tracking
        self.metrics = PerformanceMetrics()
        
        # Setup logging
        self.setup_logging()
        
        # Load existing logs if available
        self.load_existing_logs()
        
        self.logger.info(f"🎯 Paper Trading Manager initialized with ₹{initial_capital:,.2f}")
    
    def setup_logging(self):
        """Setup comprehensive logging system"""
        log_file = self.log_directory / f"paper_trading_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Create logger
        self.logger = logging.getLogger("PaperTradingManager")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def load_existing_logs(self):
        """Load existing trade logs from CSV"""
        trades_file = self.log_directory / "trade_history.csv"
        
        if trades_file.exists():
            try:
                df = pd.read_csv(trades_file)
                for _, row in df.iterrows():
                    trade_log = TradeLog(
                        timestamp=row['timestamp'],
                        order_id=row['order_id'],
                        symbol=row['symbol'],
                        side=row['side'],
                        qty=int(row['qty']),
                        price=float(row['price']),
                        order_value=float(row['order_value']),
                        pnl=float(row.get('pnl', 0.0)),
                        cumulative_pnl=float(row.get('cumulative_pnl', 0.0)),
                        strategy=row.get('strategy', 'Unknown'),
                        reason=row.get('reason', '')
                    )
                    self.trade_logs.append(trade_log)
                
                self.logger.info(f"📂 Loaded {len(self.trade_logs)} existing trade logs")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not load existing logs: {str(e)}")
    
    def place_order(self, 
                   symbol: str, 
                   qty: int, 
                   side: OrderSide, 
                   order_type: OrderType = OrderType.MARKET,
                   price: float = 0.0,
                   strategy: str = "Manual",
                   reason: str = "") -> Optional[str]:
        """
        🚀 Place order through paper trading system
        
        Args:
            symbol: Trading symbol
            qty: Quantity to trade
            side: BUY or SELL
            order_type: MARKET or LIMIT
            price: Price for limit orders
            strategy: Strategy name for tracking
            reason: Reason for the trade
            
        Returns:
            str: Order ID if successful
        """
        try:
            # Create order
            order = Order(
                symbol=symbol,
                qty=qty,
                side=side,
                order_type=order_type,
                product_type=ProductType.INTRADAY,
                limit_price=price if order_type == OrderType.LIMIT else 0.0
            )
            
            # Check available funds
            if not self._check_funds(order):
                self.logger.warning(f"⚠️ Insufficient funds for {symbol} {side.name} {qty}")
                return None
            
            # Place order through broker
            order_id = self.broker.place_order(order)
            
            if order_id:
                # Log the trade
                executed_price = order.avg_price
                order_value = qty * executed_price
                
                trade_log = TradeLog(
                    timestamp=datetime.now().isoformat(),
                    order_id=order_id,
                    symbol=symbol,
                    side=side.name,
                    qty=qty,
                    price=executed_price,
                    order_value=order_value,
                    strategy=strategy,
                    reason=reason
                )
                
                self.trade_logs.append(trade_log)
                self._save_trade_log(trade_log)
                self._update_metrics()
                
                # Update capital
                if side == OrderSide.BUY:
                    self.current_capital -= order_value
                else:
                    self.current_capital += order_value
                
                self.logger.info(
                    f"✅ Order executed: {order_id} | {strategy} | {side.name} {qty} {symbol} @ ₹{executed_price:.2f}"
                )
                
                return order_id
            else:
                self.logger.error(f"❌ Order failed for {symbol}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Place order error: {str(e)}")
            return None
    
    def _check_funds(self, order: Order) -> bool:
        """Check if sufficient funds available for the order"""
        funds = self.broker.get_funds()
        available = funds.get('availableBalance', 0.0)
        
        if order.side == OrderSide.BUY:
            required = order.qty * (order.limit_price if order.limit_price > 0 else self.broker.get_live_price(order.symbol))
            return available >= required
        
        # For sell orders, check if we have the position
        positions = self.broker.get_positions()
        for pos in positions:
            if pos['symbol'] == order.symbol and pos['netQty'] >= order.qty:
                return True
        
        return False
    
    def _save_trade_log(self, trade_log: TradeLog):
        """Save individual trade log to CSV"""
        trades_file = self.log_directory / "trade_history.csv"
        
        # Check if file exists and has header
        file_exists = trades_file.exists()
        
        with open(trades_file, 'a', newline='') as csvfile:
            fieldnames = ['timestamp', 'order_id', 'symbol', 'side', 'qty', 'price', 
                         'order_value', 'pnl', 'cumulative_pnl', 'strategy', 'reason']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(asdict(trade_log))
    
    def _update_metrics(self):
        """Update performance metrics"""
        if not self.trade_logs:
            return
        
        # Calculate basic metrics
        self.metrics.total_trades = len(self.trade_logs)
        
        # Group trades by symbol to calculate P&L
        symbol_trades = {}
        for trade in self.trade_logs:
            if trade.symbol not in symbol_trades:
                symbol_trades[trade.symbol] = []
            symbol_trades[trade.symbol].append(trade)
        
        # Calculate P&L for each symbol
        total_pnl = 0.0
        winning_trades = 0
        losing_trades = 0
        profits = []
        losses = []
        
        for symbol, trades in symbol_trades.items():
            buy_trades = [t for t in trades if t.side == 'BUY']
            sell_trades = [t for t in trades if t.side == 'SELL']
            
            # Simple P&L calculation (assuming FIFO)
            for sell_trade in sell_trades:
                remaining_qty = sell_trade.qty
                
                for buy_trade in buy_trades:
                    if remaining_qty <= 0:
                        break
                    
                    if buy_trade.qty > 0:  # Available quantity
                        matched_qty = min(remaining_qty, buy_trade.qty)
                        pnl = (sell_trade.price - buy_trade.price) * matched_qty
                        
                        total_pnl += pnl
                        
                        if pnl > 0:
                            winning_trades += 1
                            profits.append(pnl)
                        else:
                            losing_trades += 1
                            losses.append(abs(pnl))
                        
                        buy_trade.qty -= matched_qty
                        remaining_qty -= matched_qty
        
        # Update metrics
        self.metrics.winning_trades = winning_trades
        self.metrics.losing_trades = losing_trades
        self.metrics.total_pnl = total_pnl
        self.metrics.win_rate = (winning_trades / (winning_trades + losing_trades) * 100) if (winning_trades + losing_trades) > 0 else 0.0
        
        if profits:
            self.metrics.average_profit = sum(profits) / len(profits)
            self.metrics.max_profit = max(profits)
        
        if losses:
            self.metrics.average_loss = sum(losses) / len(losses)
            self.metrics.max_loss = max(losses)
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        📊 Get current portfolio summary
        
        Returns:
            Dict: Portfolio information
        """
        positions = self.broker.get_positions()
        funds = self.broker.get_funds()
        
        total_position_value = 0.0
        position_pnl = 0.0
        
        for pos in positions:
            total_position_value += abs(pos['netQty'] * pos['avgPrice'])
            position_pnl += pos.get('pnl', 0.0)
        
        portfolio_value = funds.get('availableBalance', 0.0) + total_position_value
        total_return = ((portfolio_value - self.initial_capital) / self.initial_capital) * 100
        
        summary = {
            'initial_capital': self.initial_capital,
            'current_cash': funds.get('availableBalance', 0.0),
            'position_value': total_position_value,
            'portfolio_value': portfolio_value,
            'total_return_pct': total_return,
            'total_return_amount': portfolio_value - self.initial_capital,
            'position_pnl': position_pnl,
            'active_positions': len(positions),
            'total_trades': len(self.trade_logs)
        }
        
        return summary
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        📈 Generate comprehensive performance report
        
        Returns:
            Dict: Performance metrics and analysis
        """
        self._update_metrics()
        portfolio = self.get_portfolio_summary()
        
        # Daily P&L calculation
        daily_returns = self._calculate_daily_returns()
        
        # Risk metrics
        if len(daily_returns) > 1:
            daily_returns_series = pd.Series(daily_returns)
            volatility = daily_returns_series.std() * (252 ** 0.5)  # Annualized
            self.metrics.sharpe_ratio = (daily_returns_series.mean() * 252) / volatility if volatility > 0 else 0.0
            
            # Max drawdown
            cumulative_returns = (1 + daily_returns_series).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            self.metrics.max_drawdown = drawdown.min() * 100
        
        report = {
            'portfolio_summary': portfolio,
            'performance_metrics': asdict(self.metrics),
            'trade_statistics': {
                'total_trades': self.metrics.total_trades,
                'winning_trades': self.metrics.winning_trades,
                'losing_trades': self.metrics.losing_trades,
                'win_rate': f"{self.metrics.win_rate:.2f}%",
                'avg_profit': f"₹{self.metrics.average_profit:.2f}",
                'avg_loss': f"₹{self.metrics.average_loss:.2f}",
                'max_profit': f"₹{self.metrics.max_profit:.2f}",
                'max_loss': f"₹{self.metrics.max_loss:.2f}",
                'profit_factor': (self.metrics.average_profit / self.metrics.average_loss) if self.metrics.average_loss > 0 else 0.0
            },
            'risk_metrics': {
                'sharpe_ratio': f"{self.metrics.sharpe_ratio:.3f}",
                'max_drawdown': f"{self.metrics.max_drawdown:.2f}%",
                'volatility': f"{volatility:.2f}%" if len(daily_returns) > 1 else "N/A"
            }
        }
        
        return report
    
    def _calculate_daily_returns(self) -> List[float]:
        """Calculate daily returns from trade logs"""
        if not self.trade_logs:
            return []
        
        # Group trades by date
        daily_pnl = {}
        for trade in self.trade_logs:
            date = trade.timestamp.split('T')[0]  # Extract date
            if date not in daily_pnl:
                daily_pnl[date] = 0.0
            # This is simplified - in reality, you'd calculate actual P&L
            daily_pnl[date] += trade.pnl
        
        # Convert to returns
        returns = []
        prev_capital = self.initial_capital
        
        for date, pnl in sorted(daily_pnl.items()):
            daily_return = pnl / prev_capital if prev_capital > 0 else 0.0
            returns.append(daily_return)
            prev_capital += pnl
        
        return returns
    
    def save_performance_report(self, filename: Optional[str] = None):
        """
        💾 Save performance report to file
        
        Args:
            filename: Optional custom filename
        """
        if filename is None:
            filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = self.get_performance_report()
        report_file = self.log_directory / filename
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"💾 Performance report saved: {report_file}")
    
    def print_summary(self):
        """Print trading summary to console"""
        report = self.get_performance_report()
        portfolio = report['portfolio_summary']
        metrics = report['performance_metrics']
        trade_stats = report['trade_statistics']
        
        print("\n" + "="*60)
        print("🎯 PAPER TRADING SUMMARY")
        print("="*60)
        
        print(f"\n💰 PORTFOLIO:")
        print(f"   Initial Capital: ₹{portfolio['initial_capital']:,.2f}")
        print(f"   Current Value:   ₹{portfolio['portfolio_value']:,.2f}")
        print(f"   Total Return:    ₹{portfolio['total_return_amount']:,.2f} ({portfolio['total_return_pct']:+.2f}%)")
        print(f"   Available Cash:  ₹{portfolio['current_cash']:,.2f}")
        print(f"   Position Value:  ₹{portfolio['position_value']:,.2f}")
        
        print(f"\n📊 TRADING STATISTICS:")
        print(f"   Total Trades:    {trade_stats['total_trades']}")
        print(f"   Win Rate:        {trade_stats['win_rate']}")
        print(f"   Winning Trades:  {trade_stats['winning_trades']}")
        print(f"   Losing Trades:   {trade_stats['losing_trades']}")
        print(f"   Average Profit:  {trade_stats['avg_profit']}")
        print(f"   Average Loss:    {trade_stats['avg_loss']}")
        
        print(f"\n⚡ RISK METRICS:")
        print(f"   Sharpe Ratio:    {report['risk_metrics']['sharpe_ratio']}")
        print(f"   Max Drawdown:    {report['risk_metrics']['max_drawdown']}")
        print(f"   Volatility:      {report['risk_metrics']['volatility']}")
        
        print("="*60)
    
    def export_trade_history(self, format: str = 'csv', filename: Optional[str] = None):
        """
        📤 Export trade history
        
        Args:
            format: Export format ('csv' or 'excel')
            filename: Optional custom filename
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"trade_history_{timestamp}.{format}"
        
        export_file = self.log_directory / filename
        
        if not self.trade_logs:
            self.logger.warning("⚠️ No trade logs to export")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame([asdict(trade) for trade in self.trade_logs])
        
        if format.lower() == 'csv':
            df.to_csv(export_file, index=False)
        elif format.lower() == 'excel':
            df.to_excel(export_file, index=False)
        else:
            self.logger.error(f"❌ Unsupported export format: {format}")
            return
        
        self.logger.info(f"📤 Trade history exported: {export_file}")
    
    def reset_session(self):
        """Reset paper trading session"""
        self.trade_logs.clear()
        self.daily_pnl.clear()
        self.portfolio_history.clear()
        self.current_capital = self.initial_capital
        self.metrics = PerformanceMetrics()
        
        # Reset broker's paper trading data
        self.broker.paper_orders.clear()
        self.broker.paper_positions.clear()
        self.broker.paper_holdings.clear()
        self.broker.paper_funds = {
            "fund_limit": self.initial_capital,
            "settlementBalance": self.initial_capital,
            "adhocMargin": 0.0,
            "notionalCash": self.initial_capital,
            "availableBalance": self.initial_capital,
            "utilized_amount": 0.0
        }
        
        self.logger.info("🔄 Paper trading session reset")

    def close_all_positions(self) -> bool:
        """
        🔒 Close all open positions
        
        Returns:
            bool: True if all positions closed successfully
        """
        positions = self.broker.get_positions()
        
        if not positions:
            self.logger.info("ℹ️ No positions to close")
            return True
        
        success_count = 0
        for position in positions:
            symbol = position['symbol']
            qty = abs(position['netQty'])
            side = OrderSide.SELL if position['netQty'] > 0 else OrderSide.BUY
            
            order_id = self.place_order(
                symbol=symbol,
                qty=qty,
                side=side,
                strategy="Position_Close",
                reason="Close all positions"
            )
            
            if order_id:
                success_count += 1
        
        self.logger.info(f"🔒 Closed {success_count}/{len(positions)} positions")
        return success_count == len(positions)
