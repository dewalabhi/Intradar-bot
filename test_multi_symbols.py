#!/usr/bin/env python3
import sys
sys.path.append("src")
import backtrader as bt
from strategies.dynamic_breakout import DynamicBreakout
from data.providers.yfinance_provider import YFinanceProvider

def test_multi_symbols():
    print("�� Testing MULTIPLE SYMBOLS for 1% Daily Target")
    print("=" * 60)
    
    # High volatility symbols for intraday trading
    symbols = [
        "SOXL",    # 3x Semiconductor ETF (known high volatility)
        "TQQQ",    # 3x NASDAQ ETF
        "SQQQ",    # 3x Inverse NASDAQ ETF  
        "SPXL",    # 3x S&P 500 ETF
        "TNA",     # 3x Small Cap ETF
        "LABU",    # 3x Biotech ETF
        "TECL",    # 3x Technology ETF
        "FAS",     # 3x Financial ETF
    ]
    
    provider = YFinanceProvider()
    results = []
    total_profit = 0
    total_trades = 0
    total_wins = 0
    
    for symbol in symbols:
        print(f"\n📊 Testing {symbol}...")
        
        # Create separate cerebro for each symbol
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(100000)
        cerebro.broker.setcommission(commission=0.001)
        
        # Add strategy
        cerebro.addstrategy(DynamicBreakout, position_size=800)  # Smaller size per symbol
        
        # Get data
        data = provider.get_data(symbol, period="10d", interval="5m")
        
        if data is not None and len(data) > 50:
            feed = bt.feeds.PandasData(dataname=data, name=symbol)
            cerebro.adddata(feed)
            
            # Run strategy
            strategy_results = cerebro.run()
            
            # Extract results
            final_value = cerebro.broker.getvalue()
            symbol_return = ((final_value / 100000) - 1) * 100
            daily_return = symbol_return / 10
            
            # Get strategy stats
            strat = strategy_results[0]
            trades = strat.trade_count if hasattr(strat, "trade_count") else 0
            wins = strat.wins if hasattr(strat, "wins") else 0
            pnl = strat.total_pnl if hasattr(strat, "total_pnl") else 0
            
            results.append({
                "symbol": symbol,
                "return": symbol_return,
                "daily": daily_return,
                "trades": trades,
                "wins": wins,
                "pnl": pnl
            })
            
            total_profit += pnl
            total_trades += trades
            total_wins += wins
            
            print(f"✅ {symbol}: {symbol_return:+.2f}% total, {daily_return:+.2f}% daily, {trades} trades, ${pnl:.2f} PnL")
        else:
            print(f"❌ {symbol}: No data available")
    
    # Summary
    print(f"\n" + "=" * 60)
    print("📊 MULTI-SYMBOL PORTFOLIO RESULTS")
    print("=" * 60)
    
    # Sort by daily return
    results.sort(key=lambda x: x["daily"], reverse=True)
    
    print("Individual Symbol Performance:")
    for r in results:
        status = "🎯" if r["daily"] >= 1.0 else "📈" if r["daily"] >= 0.5 else "📉"
        win_rate = (r["wins"] / r["trades"] * 100) if r["trades"] > 0 else 0
        print(f"{status} {r["symbol"]}: {r["daily"]:+.2f}% daily | {r["trades"]} trades | {win_rate:.1f}% wins | ${r["pnl"]:.2f}")
    
    print(f"\n🏆 PORTFOLIO TOTALS:")
    portfolio_total_return = (total_profit / (100000 * len([r for r in results if r["trades"] > 0]))) * 100
    portfolio_daily = portfolio_total_return / 10
    overall_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    
    print(f"💰 Combined Daily Return: {portfolio_daily:+.2f}%")
    print(f"💵 Total Profit: ${total_profit:.2f}")
    print(f"🎯 Total Trades: {total_trades}")
    print(f"✅ Overall Win Rate: {overall_win_rate:.1f}%")
    
    if portfolio_daily >= 1.0:
        print("🎉 TARGET ACHIEVED! 1%+ daily return with multi-symbol portfolio!")
    elif portfolio_daily >= 0.5:
        print("📈 Very close! Consider scaling up position sizes")
    else:
        print("🔧 Good foundation - optimize best performing symbols")
    
    # Best performers
    best_symbols = [r["symbol"] for r in results if r["daily"] >= 0.3][:3]
    if best_symbols:
        print(f"\n🌟 Best Performers for Focus: {", ".join(best_symbols)}")

if __name__ == "__main__":
    test_multi_symbols()

