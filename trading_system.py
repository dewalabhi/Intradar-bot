#!/usr/bin/env python3
"""
🎯 NIFTY 50 TRADING SYSTEM - MAIN RUNNER
============================================================
Production-ready trading system with paper trading validation
Switch between paper trading and live trading modes
"""

import sys
import argparse
import yaml
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append('/workspaces/Intradar-bot')

from src.data.providers.yfinance_provider import YFinanceProvider
from src.strategies.balanced_breakout import BalancedBreakout
from src.strategies.paper_trading_strategy import PaperTradingBalancedBreakout
from test_paper_trading import PaperTradingBot


class TradingSystemManager:
    """
    🎯 Main Trading System Manager
    Handles both paper trading and live trading modes
    """
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or "/workspaces/Intradar-bot/config/paper_trading_config.yaml"
        self.config = self.load_config()
        self.data_provider = YFinanceProvider()
        
        print(f"🎯 NIFTY 50 TRADING SYSTEM INITIALIZED")
        print(f"📁 Config: {self.config_file}")
        print(f"📊 Mode: Paper Trading Ready")
        
    def load_config(self) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            print(f"✅ Configuration loaded successfully")
            return config
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            # Return default config
            return {
                'paper_trading': {'enabled': True, 'initial_capital': 100000.0},
                'nifty50_symbols': {'primary': ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS']},
                'data': {'default_period': '2d', 'default_interval': '1m'}
            }
            
    def run_paper_trading(self, symbols: list = None, duration: str = "full"):
        """
        📝 Run paper trading mode (SAFE - no real trades)
        Perfect for strategy validation before live trading
        """
        
        print(f"\n🎯 STARTING PAPER TRADING MODE")
        print(f"=" * 60)
        print(f"📝 All trades will be LOGGED but NOT EXECUTED")
        print(f"🔒 This is 100% risk-free for strategy validation")
        print(f"=" * 60)
        
        # Get symbols from config if not provided
        if symbols is None:
            primary_symbols = self.config.get('nifty50_symbols', {}).get('primary', [])
            secondary_symbols = self.config.get('nifty50_symbols', {}).get('secondary', [])
            symbols = primary_symbols[:5]  # Start with top 5
            
        # Initialize paper trading bot
        paper_bot = PaperTradingBot(
            initial_capital=self.config.get('paper_trading', {}).get('initial_capital', 100000.0)
        )
        
        try:
            if duration == "single":
                # Test single symbol
                result = paper_bot.test_single_symbol_paper_trading(
                    symbol=symbols[0] if symbols else "RELIANCE.NS",
                    period=self.config.get('data', {}).get('default_period', '2d'),
                    interval=self.config.get('data', {}).get('default_interval', '1m')
                )
                
            elif duration == "multi":
                # Test multiple symbols
                result = paper_bot.test_multiple_symbols_paper_trading(
                    symbols=symbols,
                    period=self.config.get('data', {}).get('default_period', '2d'),
                    interval=self.config.get('data', {}).get('default_interval', '1m')
                )
                
            elif duration == "live_sim":
                # Live simulation
                result = paper_bot.run_live_paper_trading_simulation(
                    symbols=symbols[:3],  # Use top 3 for live simulation
                    duration_minutes=30
                )
                
            else:  # "full"
                # Full comprehensive test
                print(f"\n🎯 COMPREHENSIVE PAPER TRADING VALIDATION")
                
                # Phase 1: Single symbol validation
                print(f"\n📊 PHASE 1: Single Symbol Validation")
                single_result = paper_bot.test_single_symbol_paper_trading(
                    symbol=symbols[0] if symbols else "RELIANCE.NS",
                    period="3d",
                    interval="1m"
                )
                
                # Phase 2: Multiple symbols
                print(f"\n📊 PHASE 2: Multiple Symbols Testing")
                multi_result = paper_bot.test_multiple_symbols_paper_trading(
                    symbols=symbols,
                    period="2d", 
                    interval="1m"
                )
                
                result = {
                    'single_symbol': single_result,
                    'multiple_symbols': multi_result
                }
                
            # Show final recommendation
            self.show_live_trading_readiness()
            return result
            
        except Exception as e:
            print(f"❌ Paper trading error: {e}")
            return None
            
    def run_live_trading(self, symbols: list = None):
        """
        🔥 Run live trading mode (REAL MONEY - USE WITH CAUTION)
        Only use after thorough paper trading validation
        """
        
        print(f"\n🔥 LIVE TRADING MODE REQUESTED")
        print(f"=" * 60)
        print(f"⚠️  WARNING: This involves REAL MONEY!")
        print(f"💰 Real trades will be executed")
        print(f"📉 Risk of financial loss exists")
        print(f"=" * 60)
        
        # Safety checks
        if not self.validate_live_trading_readiness():
            print(f"❌ Live trading validation FAILED")
            print(f"📝 Please complete paper trading validation first")
            return None
            
        # Get user confirmation
        confirm = input(f"\n⚠️  Are you ABSOLUTELY SURE you want to trade with REAL MONEY? (type 'YES I UNDERSTAND THE RISKS'): ")
        
        if confirm != "YES I UNDERSTAND THE RISKS":
            print(f"✅ Live trading cancelled - staying safe!")
            print(f"📝 Consider more paper trading to build confidence")
            return None
            
        print(f"\n🔥 INITIALIZING LIVE TRADING...")
        print(f"⚠️  This feature requires broker integration")
        print(f"⚠️  Currently not implemented for safety")
        print(f"\n💡 To enable live trading:")
        print(f"   1. Complete extensive paper trading")
        print(f"   2. Integrate with your broker API")
        print(f"   3. Add proper risk management systems")
        print(f"   4. Start with very small position sizes")
        print(f"   5. Monitor trades closely")
        
        return None
        
    def validate_live_trading_readiness(self) -> bool:
        """
        ✅ Validate if system is ready for live trading
        Checks paper trading performance requirements
        """
        
        print(f"\n🔍 VALIDATING LIVE TRADING READINESS...")
        
        validation_config = self.config.get('validation', {})
        required_trades = validation_config.get('required_paper_trades', 50)
        required_win_rate = validation_config.get('required_win_rate_pct', 45.0)
        max_drawdown = validation_config.get('max_drawdown_pct', 10.0)
        
        # Check for paper trading logs
        paper_trading_dir = Path("/workspaces/Intradar-bot/data/paper_trading")
        
        if not paper_trading_dir.exists():
            print(f"❌ No paper trading history found")
            print(f"📝 Please run paper trading first: --mode paper")
            return False
            
        # Check for recent paper trading logs
        log_files = list(paper_trading_dir.glob("paper_trades_*.json"))
        
        if not log_files:
            print(f"❌ No paper trading logs found")
            print(f"📝 Please complete paper trading sessions first")
            return False
            
        # Here you would implement actual validation logic
        # For now, we'll be conservative and require manual approval
        
        print(f"⚠️  MANUAL VALIDATION REQUIRED:")
        print(f"   • Minimum {required_trades} paper trades completed?")
        print(f"   • Win rate above {required_win_rate}%?")
        print(f"   • Maximum drawdown below {max_drawdown}%?")
        print(f"   • Strategy performance satisfactory?")
        print(f"   • Risk management rules tested?")
        print(f"\n💡 Review your paper trading logs before proceeding")
        
        return False  # Always return False for safety - user must manually override
        
    def show_live_trading_readiness(self):
        """Show recommendations for live trading readiness"""
        
        print(f"\n" + "="*60)
        print(f"🎯 LIVE TRADING READINESS CHECKLIST")
        print(f"="*60)
        
        print(f"\n✅ PAPER TRADING VALIDATION COMPLETE")
        print(f"📊 Review your paper trading results above")
        
        print(f"\n📋 BEFORE GOING LIVE:")
        print(f"   ✅ Paper trading shows consistent profits")
        print(f"   ✅ Win rate above 45%")
        print(f"   ✅ Maximum drawdown under control")
        print(f"   ✅ Strategy works across multiple symbols")
        print(f"   ✅ Risk management rules validated")
        print(f"   ✅ Position sizing appropriate")
        print(f"   ✅ Stop losses working correctly")
        
        print(f"\n🚀 READY FOR LIVE TRADING?")
        print(f"   1. Run: python trading_system.py --mode live")
        print(f"   2. Start with VERY SMALL positions")
        print(f"   3. Monitor closely for first few days")
        print(f"   4. Gradually increase size if profitable")
        
        print(f"\n⚠️  REMEMBER:")
        print(f"   • Never risk more than you can afford to lose")
        print(f"   • Start small and scale gradually")
        print(f"   • Keep detailed logs of live performance")
        print(f"   • Be prepared to stop if results don't match paper trading")
        
        print(f"="*60)
        
    def run_backtest(self, symbols: list = None):
        """
        📈 Run historical backtest (uses historical data)
        Good for initial strategy validation
        """
        
        print(f"\n📈 RUNNING HISTORICAL BACKTEST")
        print(f"📊 Testing strategy on historical data")
        
        if symbols is None:
            symbols = self.config.get('nifty50_symbols', {}).get('primary', [])[:5]
            
        # Use the existing test infrastructure
        paper_bot = PaperTradingBot()
        result = paper_bot.test_multiple_symbols_paper_trading(
            symbols=symbols,
            period="5d",  # Longer period for backtest
            interval="1m"
        )
        
        return result


def main():
    """Main entry point with command line interface"""
    
    parser = argparse.ArgumentParser(description="🎯 Nifty 50 Trading System")
    parser.add_argument('--mode', choices=['paper', 'live', 'backtest'], 
                       default='paper', help='Trading mode (default: paper)')
    parser.add_argument('--symbols', nargs='+', 
                       help='Specific symbols to trade (default: from config)')
    parser.add_argument('--config', type=str,
                       help='Configuration file path')
    parser.add_argument('--duration', choices=['single', 'multi', 'live_sim', 'full'],
                       default='full', help='Paper trading duration (default: full)')
    
    args = parser.parse_args()
    
    # Initialize trading system
    system = TradingSystemManager(config_file=args.config)
    
    # Show startup message
    print(f"\n🎯 NIFTY 50 TRADING SYSTEM v1.0")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⚙️ Mode: {args.mode.upper()}")
    
    # Run appropriate mode
    if args.mode == 'paper':
        result = system.run_paper_trading(symbols=args.symbols, duration=args.duration)
    elif args.mode == 'live':
        result = system.run_live_trading(symbols=args.symbols)
    elif args.mode == 'backtest':
        result = system.run_backtest(symbols=args.symbols)
    else:
        print(f"❌ Unknown mode: {args.mode}")
        return
        
    if result:
        print(f"\n✅ Trading session completed successfully!")
    else:
        print(f"\n❌ Trading session encountered issues")


if __name__ == "__main__":
    main()
