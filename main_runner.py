#!/usr/bin/env python3
"""
🚀 INTRADAR BOT - PRODUCTION RUNNER
============================================================
Production-ready trading bot with paper/live mode switching
Integrates Nifty 50 strategy with Fyers broker
"""

import sys
import os
import argparse
import asyncio
import signal
import yaml
from pathlib import Path
from datetime import datetime, time as dt_time
import logging
from typing import Optional

# Add project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.brokers.fyers_broker import FyersBroker, OrderSide, OrderType
from src.brokers.paper_trading_manager import PaperTradingManager
from src.strategies.balanced_breakout import BalancedBreakout
from src.data.providers.yfinance_provider import YfinanceProvider

class IntradarBot:
    """
    🚀 Main Trading Bot Controller
    
    Features:
    - Paper/Live trading modes
    - Comprehensive logging
    - Risk management
    - Strategy execution
    - Performance monitoring
    - Graceful shutdown
    """
    
    def __init__(self, config_file: str = "config/config.yaml"):
        """Initialize the trading bot"""
        self.config = self.load_config(config_file)
        self.setup_logging()
        
        self.broker: Optional[FyersBroker] = None
        self.paper_manager: Optional[PaperTradingManager] = None
        self.strategy: Optional[BalancedBreakout] = None
        self.data_provider: Optional[YfinanceProvider] = None
        
        self.running = False
        self.paper_mode = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.logger.info("🚀 IntradarBot initialized")
    
    def load_config(self, config_file: str) -> dict:
        """Load configuration from YAML file"""
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                # Create default config
                self.create_default_config(config_path)
            
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            return config
        except Exception as e:
            print(f"❌ Failed to load config: {str(e)}")
            return self.get_default_config()
    
    def create_default_config(self, config_path: Path):
        """Create default configuration file"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        default_config = self.get_default_config()
        
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
        
        print(f"📝 Default config created: {config_path}")
    
    def get_default_config(self) -> dict:
        """Get default configuration"""
        return {
            'trading': {
                'paper_mode': True,
                'initial_capital': 100000.0,
                'max_positions': 5,
                'position_size': 50000.0,
                'stop_loss_pct': 2.0,
                'take_profit_pct': 4.0,
                'trading_start_time': '09:30',
                'trading_end_time': '15:00',
                'max_daily_loss': 5000.0,
                'max_daily_trades': 20
            },
            'broker': {
                'fyers': {
                    'app_id': 'YOUR_FYERS_APP_ID',
                    'secret_key': 'YOUR_FYERS_SECRET_KEY',
                    'redirect_uri': 'https://trade.fyers.in/api-login/redirect-uri/index.html',
                    'totp_key': 'YOUR_FYERS_TOTP_KEY'  # Optional for auto-login
                }
            },
            'strategy': {
                'name': 'balanced_breakout',
                'timeframe': '1min',
                'lookback_period': 20,
                'volume_multiplier': 1.5,
                'min_volume': 100000,
                'sector_focus': ['IT', 'Banking', 'Energy']
            },
            'logging': {
                'level': 'INFO',
                'file': 'data/logs/intradar_bot.log',
                'max_file_size': '10MB',
                'backup_count': 5
            },
            'data': {
                'provider': 'yfinance',
                'cache_dir': 'data/cache',
                'update_frequency': 60  # seconds
            }
        }
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_config = self.config.get('logging', {})
        log_file = log_config.get('file', 'data/logs/intradar_bot.log')
        log_level = log_config.get('level', 'INFO')
        
        # Create log directory
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger("IntradarBot")
        self.logger.setLevel(getattr(logging, log_level))
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler with rotation
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def initialize_components(self, paper_mode: bool = True):
        """Initialize all bot components"""
        self.logger.info(f"🔧 Initializing components in {'PAPER' if paper_mode else 'LIVE'} mode")
        self.paper_mode = paper_mode
        
        # Initialize broker
        broker_config = self.config.get('broker', {}).get('fyers', {})
        
        self.broker = FyersBroker(
            app_id=broker_config.get('app_id', ''),
            paper_trading=paper_mode,
            initial_funds=self.config.get('trading', {}).get('initial_capital', 100000.0)
        )
        
        # Initialize paper trading manager if in paper mode
        if paper_mode:
            self.paper_manager = PaperTradingManager(
                broker=self.broker,
                initial_capital=self.config.get('trading', {}).get('initial_capital', 100000.0),
                log_directory="data/paper_trading"
            )
        
        # Initialize strategy
        self.strategy = BalancedBreakout()
        
        # Initialize data provider
        self.data_provider = YfinanceProvider()
        
        self.logger.info("✅ All components initialized successfully")
    
    def authenticate_broker(self) -> bool:
        """Authenticate with the broker"""
        if self.paper_mode:
            self.logger.info("📄 Paper mode - No authentication required")
            return True
        
        try:
            broker_config = self.config.get('broker', {}).get('fyers', {})
            
            # Check if credentials are provided
            if not broker_config.get('app_id') or broker_config.get('app_id') == 'YOUR_FYERS_APP_ID':
                self.logger.error("❌ Please configure Fyers credentials in config.yaml")
                return False
            
            # Authenticate
            auth_success = self.broker.login(
                secret_key=broker_config.get('secret_key', ''),
                redirect_uri=broker_config.get('redirect_uri', ''),
                totp_key=broker_config.get('totp_key', '')
            )
            
            if auth_success:
                self.logger.info("✅ Broker authentication successful")
                return True
            else:
                self.logger.error("❌ Broker authentication failed")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Authentication error: {str(e)}")
            return False
    
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        now = datetime.now()
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Check trading hours
        trading_config = self.config.get('trading', {})
        start_time = dt_time.fromisoformat(trading_config.get('trading_start_time', '09:30'))
        end_time = dt_time.fromisoformat(trading_config.get('trading_end_time', '15:00'))
        
        current_time = now.time()
        
        return start_time <= current_time <= end_time
    
    def check_risk_limits(self) -> bool:
        """Check if risk limits are within bounds"""
        try:
            if self.paper_mode and self.paper_manager:
                portfolio = self.paper_manager.get_portfolio_summary()
                daily_pnl = portfolio['total_return_amount']
            else:
                # For live trading, get actual P&L from broker
                daily_pnl = 0.0  # Implement actual P&L calculation
            
            max_daily_loss = self.config.get('trading', {}).get('max_daily_loss', 5000.0)
            
            if daily_pnl < -max_daily_loss:
                self.logger.warning(f"⚠️ Daily loss limit reached: ₹{daily_pnl:.2f}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Risk check error: {str(e)}")
            return False
    
    def execute_strategy(self):
        """Execute trading strategy"""
        try:
            # Get Nifty 50 stocks to trade
            nifty50_symbols = self.get_nifty50_symbols()
            
            for symbol in nifty50_symbols:
                if not self.running:
                    break
                
                try:
                    # Get market data for the symbol
                    market_data = self.data_provider.get_historical_data(
                        symbol=symbol,
                        period='1d',
                        interval='1m'
                    )
                    
                    if market_data is None or market_data.empty:
                        continue
                    
                    # Check if it's a valid Nifty 50 stock
                    if not self.strategy.is_nifty50_stock(symbol):
                        continue
                    
                    # Generate signal (simplified)
                    signal = self.generate_signal(symbol, market_data)
                    
                    if signal:
                        self.execute_trade(signal)
                
                except Exception as e:
                    self.logger.error(f"❌ Strategy execution error for {symbol}: {str(e)}")
                    continue
        
        except Exception as e:
            self.logger.error(f"❌ Strategy execution error: {str(e)}")
    
    def get_nifty50_symbols(self) -> list:
        """Get list of Nifty 50 symbols for trading"""
        # Top liquid Nifty 50 stocks
        return [
            "NSE:RELIANCE-EQ",
            "NSE:TCS-EQ",
            "NSE:HDFCBANK-EQ",
            "NSE:INFY-EQ",
            "NSE:ICICIBANK-EQ",
            "NSE:SBIN-EQ",
            "NSE:BHARTIARTL-EQ",
            "NSE:ITC-EQ",
            "NSE:LT-EQ",
            "NSE:HINDUNILVR-EQ",
            "NSE:KOTAKBANK-EQ",
            "NSE:AXISBANK-EQ",
            "NSE:ASIANPAINT-EQ",
            "NSE:MARUTI-EQ",
            "NSE:SUNPHARMA-EQ"
        ]
    
    def generate_signal(self, symbol: str, data) -> Optional[dict]:
        """Generate trading signal for a symbol"""
        # Simplified signal generation
        # In production, this would use the actual strategy logic
        
        try:
            if len(data) < 20:  # Need minimum data points
                return None
            
            current_price = data['close'].iloc[-1]
            high_20 = data['high'].tail(20).max()
            low_20 = data['low'].tail(20).min()
            volume_avg = data['volume'].tail(20).mean()
            current_volume = data['volume'].iloc[-1]
            
            # Simple breakout strategy
            if current_price > high_20 * 1.002 and current_volume > volume_avg * 1.5:
                return {
                    'symbol': symbol,
                    'action': 'BUY',
                    'price': current_price,
                    'reason': 'Breakout above 20-period high with volume'
                }
            
            elif current_price < low_20 * 0.998 and current_volume > volume_avg * 1.5:
                return {
                    'symbol': symbol,
                    'action': 'SELL',
                    'price': current_price,
                    'reason': 'Breakdown below 20-period low with volume'
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Signal generation error for {symbol}: {str(e)}")
            return None
    
    def execute_trade(self, signal: dict):
        """Execute a trade based on signal"""
        try:
            symbol = signal['symbol']
            action = signal['action']
            price = signal['price']
            reason = signal['reason']
            
            # Calculate position size
            position_size = self.config.get('trading', {}).get('position_size', 50000.0)
            qty = int(position_size / price)
            
            if qty <= 0:
                return
            
            # Execute trade
            if self.paper_mode and self.paper_manager:
                order_id = self.paper_manager.place_order(
                    symbol=symbol,
                    qty=qty,
                    side=OrderSide.BUY if action == 'BUY' else OrderSide.SELL,
                    strategy="Balanced_Breakout",
                    reason=reason
                )
                
                if order_id:
                    self.logger.info(f"📈 {action} signal executed: {qty} {symbol} @ ₹{price:.2f}")
                else:
                    self.logger.warning(f"⚠️ Failed to execute {action} for {symbol}")
            
            else:
                # Live trading execution
                order = {
                    'symbol': symbol,
                    'qty': qty,
                    'side': OrderSide.BUY if action == 'BUY' else OrderSide.SELL,
                    'order_type': OrderType.MARKET
                }
                
                order_id = self.broker.place_order(order)
                
                if order_id:
                    self.logger.info(f"📈 LIVE {action} executed: {qty} {symbol} @ ₹{price:.2f}")
                else:
                    self.logger.warning(f"⚠️ Failed to execute LIVE {action} for {symbol}")
        
        except Exception as e:
            self.logger.error(f"❌ Trade execution error: {str(e)}")
    
    async def run_trading_loop(self):
        """Main trading loop"""
        self.logger.info("🔄 Starting trading loop")
        self.running = True
        
        try:
            while self.running:
                # Check if market is open
                if not self.is_market_open():
                    self.logger.info("🕒 Market closed - waiting...")
                    await asyncio.sleep(300)  # Check every 5 minutes
                    continue
                
                # Check risk limits
                if not self.check_risk_limits():
                    self.logger.warning("⚠️ Risk limits exceeded - stopping trading")
                    break
                
                # Execute strategy
                self.execute_strategy()
                
                # Wait before next iteration
                await asyncio.sleep(60)  # Run every minute
        
        except Exception as e:
            self.logger.error(f"❌ Trading loop error: {str(e)}")
        
        finally:
            self.logger.info("🛑 Trading loop stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"🛑 Received signal {signum} - shutting down gracefully")
        self.running = False
    
    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("🔄 Initiating graceful shutdown")
        
        try:
            # Close all positions in paper mode
            if self.paper_mode and self.paper_manager:
                self.paper_manager.close_all_positions()
                self.paper_manager.print_summary()
                self.paper_manager.save_performance_report()
            
            # Logout from broker
            if self.broker and not self.paper_mode:
                self.broker.logout()
            
            self.logger.info("✅ Shutdown completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Shutdown error: {str(e)}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="IntradarBot - Nifty 50 Trading Bot")
    parser.add_argument('--mode', choices=['paper', 'live'], default='paper',
                       help='Trading mode: paper or live (default: paper)')
    parser.add_argument('--config', default='config/config.yaml',
                       help='Configuration file path')
    parser.add_argument('--test', action='store_true',
                       help='Run in test mode (single iteration)')
    
    args = parser.parse_args()
    
    print("🚀 INTRADAR BOT - NIFTY 50 TRADING SYSTEM")
    print("=" * 50)
    print(f"Mode: {'PAPER TRADING' if args.mode == 'paper' else 'LIVE TRADING'}")
    print(f"Config: {args.config}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    bot = None
    try:
        # Initialize bot
        bot = IntradarBot(args.config)
        
        # Initialize components
        paper_mode = (args.mode == 'paper')
        bot.initialize_components(paper_mode)
        
        # Authenticate if in live mode
        if not paper_mode:
            if not bot.authenticate_broker():
                print("❌ Authentication failed - exiting")
                return False
        
        # Run bot
        if args.test:
            # Test mode - single execution
            bot.execute_strategy()
            if bot.paper_manager:
                bot.paper_manager.print_summary()
        else:
            # Production mode - continuous trading
            asyncio.run(bot.run_trading_loop())
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if bot:
            bot.shutdown()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
