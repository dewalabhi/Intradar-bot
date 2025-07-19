#!/usr/bin/env python3
"""
Quick test script for the trading bot
"""

from src.main import TradingBot

def main():
    print("🧪 Testing Trading Bot...")
    
    # Create bot
    bot = TradingBot()
    
    # Test with a single symbol
    print("📊 Running quick test with AAPL...")
    bot.run_backtest(symbols=['AAPL'])

if __name__ == "__main__":
    main()
