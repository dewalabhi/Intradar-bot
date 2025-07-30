#!/usr/bin/env python3
import sys
sys.path.append('src')

import backtrader as bt
import yaml
from pathlib import Path

# Import strategies
from strategies.price_action_breakout import PriceActionBreakout
from data.providers.yfinance_provider import YFinanceProvider

def load_config():
    with open('config/config.yaml', 'r') as f:
        return yaml.safe_load(f)

def main():
    print("🤖 Price Action Trading Bot")
    print("=" * 40)
    
    # Load config
    config = load_config()
    
    # Setup Cerebro
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100000)
    cerebro.broker.setcommission(commission=0.001)
    
    # List of all strategy classes
    from strategies.aggressive_breakout import AggressiveBreakout
    from strategies.balanced_breakout import BalancedBreakout
    from strategies.dynamic_breakout import DynamicBreakout
    from strategies.fixed_breakout import FixedBreakout
    from strategies.improved_breakout import ImprovedBreakout
    from strategies.ma_crossover import MovingAverageCrossover
    from strategies.momentum_breakout import MomentumBreakout
    from strategies.optimized_breakout import OptimizedBreakout
    from strategies.price_action_breakout import PriceActionBreakout
    from strategies.rsi_mean_reversion import RSIMeanReversion
    from strategies.scaled_momentum import ScaledMomentum
    from strategies.simple_breakout import SimpleBreakout
    
    # New optimized strategies for intraday trading
    from strategies.optimized_intraday_breakout import OptimizedIntradayBreakout
    from strategies.optimized_momentum_strategy import OptimizedMomentumStrategy
    from strategies.hybrid_scalping_strategy import HybridScalpingStrategy
    from strategies.ultimate_intraday_strategy import UltimateIntradayStrategy

    strategies = [
        # Skip original poor-performing strategies for faster testing
        # AggressiveBreakout,
        # BalancedBreakout,
        # DynamicBreakout,
        # FixedBreakout,
        # ImprovedBreakout,
        # MovingAverageCrossover,
        # MomentumBreakout,
        # OptimizedBreakout,
        PriceActionBreakout,  # Keep the baseline
        # RSIMeanReversion,
        ScaledMomentum,       # Keep the other baseline
        # SimpleBreakout,
        
        # Focus on the optimized intraday strategies
        OptimizedIntradayBreakout,
        OptimizedMomentumStrategy,
        HybridScalpingStrategy,
        UltimateIntradayStrategy,  # The ultimate strategy
    ]

    provider = YFinanceProvider()
    symbols = [
        'AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B', 'JPM', 'V',
        'UNH', 'HD', 'MA', 'PG', 'LLY', 'XOM', 'MRK', 'ABBV', 'AVGO', 'COST',
        'PEP', 'ADBE', 'KO', 'CSCO', 'WMT', 'MCD', 'BAC', 'CRM', 'TMO', 'ACN'
    ]
    initial_cash = 100000
    commission_rupees = 40
    period = '10d'
    interval = '5m'

    all_results = []
    for strat in strategies:
        print(f"\n� Testing {strat.__name__} on all symbols")
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(initial_cash)
        cerebro.broker.setcommission(commission=commission_rupees, commtype=bt.CommInfoBase.COMM_FIXED)
        cerebro.addstrategy(strat)
        loaded_symbols = []
        for symbol in symbols:
            print(f"📡 Loading data for {symbol}...")
            data = provider.get_data(symbol, period=period, interval=interval)
            if data is not None and len(data) > 50:
                feed = bt.feeds.PandasData(dataname=data, name=symbol)
                cerebro.adddata(feed)
                loaded_symbols.append(symbol)
            else:
                print(f"❌ Failed to load data for {symbol}")
        initial_value = cerebro.broker.getvalue()
        cerebro.run()
        final_value = cerebro.broker.getvalue()
        total_return = (final_value / initial_value - 1) * 100
        all_results.append({
            'strategy': strat.__name__,
            'symbols': loaded_symbols,
            'start': initial_value,
            'end': final_value,
            'return': total_return
        })
        print(f"Result: {strat.__name__}: {total_return:+.2f}% | Final Value: ₹{final_value:,.2f}")

    print("\n" + "=" * 40)
    print("📊 STRATEGY COMPARISON RESULTS (₹)")
    print("=" * 40)
    # Find best strategy overall
    if all_results:
        best_overall = max(all_results, key=lambda x: x['return'])
        print("\n🏆 BEST OVERALL STRATEGY:")
        print(f"{best_overall['strategy']} with {best_overall['return']:+.2f}% (Final: ₹{best_overall['end']:,.2f})")
        print(f"Symbols traded: {', '.join(best_overall['symbols'])}")
        print("=" * 40)

if __name__ == "__main__":
    main()
