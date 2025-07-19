#!/usr/bin/env python3
import sys
sys.path.append("src")
import backtrader as bt
from strategies.optimized_breakout import OptimizedBreakout
from data.providers.yfinance_provider import YFinanceProvider

def test_enhanced_strategy():
    print("🚀 Testing ENHANCED Multi-Symbol, Multi-Timeframe Strategy")
    print("=" * 70)
    
    # 15-20 high-volume symbols across sectors
    symbols = [
        # 3x Leveraged ETFs (high volatility)
        "SOXL", "TQQQ", "SQQQ", "SPXL", "TNA", "LABU", "TECL", 
        
        # High-volume individual stocks
        "TSLA", "AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "META",
        
        # Volatile stocks
        "AMD", "NFLX", "BABA", "COIN", "PLTR"
    ]
    
    # Test both 5m and 15m timeframes
    timeframes = [
        {"period": "10d", "interval": "5m", "name": "5min"},
        {"period": "10d", "interval": "15m", "name": "15min"}
    ]
    
    provider = YFinanceProvider()
    results = []
    total_profit = 0
    total_trades = 0
    total_wins = 0
    
    for tf in timeframes:
        print(f"\n📊 Testing {tf["name"]} timeframe...")
        print("-" * 50)
        
        for symbol in symbols:
            print(f"Testing {symbol} on {tf["name"]}...")
            
            cerebro = bt.Cerebro()
            cerebro.broker.setcash(100000)
            cerebro.broker.setcommission(commission=0.001)
            
            # Add optimized strategy
            cerebro.addstrategy(OptimizedBreakout)
            
            # Get data
            data = provider.get_data(symbol, period=tf["period"], interval=tf["interval"])
            
            if data is not None and len(data) > 50:
                feed = bt.feeds.PandasData(dataname=data, name=symbol)
                cerebro.adddata(feed)
                
                try:
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
                    
                    if trades > 0:  # Only count symbols with trades
                        results.append({
                            "symbol": f"{symbol}_{tf["name"]}",
                            "return": symbol_return,
                            "daily": daily_return,
                            "trades": trades,
                            "wins": wins,
                            "pnl": pnl,
                            "avg_trade": pnl / trades if trades > 0 else 0
                        })
                        
                        total_profit += pnl
                        total_trades += trades
                        total_wins += wins
                        
                        win_rate = (wins / trades * 100) if trades > 0 else 0
                        print(f"✅ {symbol}_{tf["name"]}: {daily_return:+.2f}% daily | {trades} trades | {win_rate:.1f}% wins | ${pnl:.2f}")
                    
                except Exception as e:
                    print(f"❌ {symbol}_{tf["name"]}: Error - {e}")
            else:
                print(f"❌ {symbol}_{tf["name"]}: No data")
    
    # Summary
    print(f"\n" + "=" * 70)
    print("🏆 ENHANCED STRATEGY RESULTS")
    print("=" * 70)
    
    # Sort by daily return
    results.sort(key=lambda x: x["daily"], reverse=True)
    
    print("Top Performers:")
    for i, r in enumerate(results[:10]):  # Top 10
        status = "🎯" if r["daily"] >= 0.5 else "📈" if r["daily"] >= 0.1 else "📉"
        win_rate = (r["wins"] / r["trades"] * 100) if r["trades"] > 0 else 0
        print(f"{status} {i+1}. {r["symbol"]}: {r["daily"]:+.2f}% daily | ${r["avg_trade"]:.2f}/trade | {win_rate:.1f}% wins")
    
    print(f"\n🎯 PORTFOLIO TOTALS:")
    portfolio_daily = total_profit / (100000 * 10)  # 10 days, $100k base
    overall_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    avg_trade_profit = total_profit / total_trades if total_trades > 0 else 0
    
    print(f"💰 Total Daily Profit: ${total_profit/10:.2f}")
    print(f"📈 Daily Return: {portfolio_daily*100:+.2f}%")
    print(f"🎯 Total Trades: {total_trades}")
    print(f"✅ Overall Win Rate: {overall_win_rate:.1f}%")
    print(f"💵 Average Trade: ${avg_trade_profit:.2f}")
    
    # Commission analysis
    daily_trades = total_trades / 10
    daily_commission = daily_trades * avg_trade_profit * 0.001  # Rough estimate
    net_daily_profit = (total_profit / 10) - daily_commission
    
    print(f"\n💸 Commission Impact:")
    print(f"Daily Trades: {daily_trades:.1f}")
    print(f"Est. Daily Commission: ${daily_commission:.2f}")
    print(f"Net Daily Profit: ${net_daily_profit:.2f}")
    
    if portfolio_daily >= 0.01:  # 1% daily
        print("🎉 TARGET ACHIEVED! 1%+ daily return!")
    elif portfolio_daily >= 0.005:  # 0.5% daily
        print("📈 Very close! Minor optimization needed")
    else:
        needed_improvement = (0.01 - portfolio_daily) * 100000
        print(f"🔧 Need ${needed_improvement:.0f} more daily profit for 1% target")

if __name__ == "__main__":
    test_enhanced_strategy()

