import backtrader as bt

class BalancedBreakout(bt.Strategy):
    params = (
        ("lookback_period", 5),          # Shorter for faster signals
        ("volume_threshold", 0.3),       # Much lower for more opportunities
        ("stop_loss_pct", 0.15),        # Tighter stops
        ("take_profit_pct", 0.20),      # Smaller targets
        ("max_hold_bars", 8),           # Hold max 8 minutes
        ("min_breakout_pct", 0.003),    # 0.3% minimum breakout
        ("position_size", 1500),        # Default position size
        ("trade_start_hour", 9),        # Market hours
        ("trade_end_hour", 15),         
        ("min_rsi_spread", 10),         # Lower RSI spread
        ("volume_spike_threshold", 1.3), # Lower spike requirement
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume
        # Ultra-fast indicators for 1-minute scalping
        self.resistance = bt.indicators.Highest(self.datahigh, period=self.params.lookback_period)
        self.support = bt.indicators.Lowest(self.datalow, period=self.params.lookback_period)
        self.volume_ma = bt.indicators.SMA(self.datavolume, period=8)
        self.rsi = bt.indicators.RSI(self.dataclose, period=4)
        self.price_ma = bt.indicators.SMA(self.dataclose, period=3)
        self.volume_ratio = self.datavolume / self.volume_ma
        # Volatility indicator for dynamic stops
        self.atr = bt.indicators.ATR(self.datas[0], period=8)
        # Trade tracking
        self.order = None
        self.entry_price = 0
        self.entry_bar = 0
        self.trade_count = 0
        self.wins = 0
        self.total_pnl = 0
        self.stock_trade_stats = {}
        # Universal market condition filter - adapts to any market's volatility profile
        self.market_volatility_threshold = 0.0005  # Base threshold, auto-adjusts per symbol
        
        # Nifty 50 focused configuration for Indian market
        self.symbol_params = {}  # Will be populated dynamically
        
        # Nifty 50 specific parameters (high liquidity, stable stocks)
        self.nifty50_params = {
            'base_position_size': 50000,      # ₹50,000 standard position
            'volatility_threshold': 0.0006,   # Lower threshold for liquid stocks
            'volume_multiplier': 0.8,         # Lower volume requirement (high liquidity)
            'stop_loss_mult': 0.9,           # Tighter stops (predictable moves)
            'circuit_risk_low': True,        # Lower circuit risk
            'optimal_trading_window': (9.5, 15.0),  # 9:30 AM - 3:00 PM optimal
        }
        
        # Nifty 50 optimized parameters
        self.nifty50_market_params = {
            'circuit_limit_factor': 0.05,    # 5% circuit limit (rare for Nifty 50)
            'brokerage_factor': 0.0003,      # 0.03% lower brokerage for high volume
            'market_hours': (9.5, 15.0),     # Optimal trading window
            'high_liquidity': True,          # All Nifty 50 have high liquidity
            'rupee_based_sizing': True,      # Use ₹50,000 standard positions
        }
        
        # Nifty 50 adaptive parameters
        self.adaptive_params = {
            'volatility_multiplier': 1.0,    # Standard for stable large caps
            'volume_multiplier': 0.8,        # Lower requirement due to liquidity
            'position_size_standard': 50000, # Standard ₹50K position
            'circuit_limit_awareness': False, # Minimal circuit risk for Nifty 50
        }
        
    def is_nifty50_stock(self, symbol):
        """Check if symbol is a Nifty 50 stock and return True/False"""
        if not symbol:
            return False
            
        symbol = symbol.upper()
        
        # Complete Nifty 50 stock list (as of 2025)
        nifty50_stocks = [
            'RELIANCE', 'TCS', 'HDFCBANK', 'BHARTIARTL', 'ICICIBANK', 'SBIN', 'LICI',
            'ITC', 'HINDUNILVR', 'LT', 'HCLTECH', 'MARUTI', 'SUNPHARMA', 'TITAN',
            'ONGC', 'TATAMOTORS', 'AXISBANK', 'NESTLEIND', 'WIPRO', 'ULTRACEMCO',
            'ASIANPAINT', 'M&M', 'KOTAKBANK', 'NTPC', 'BAJFINANCE', 'TECHM', 'TATACONSUM',
            'POWERGRID', 'HDFCLIFE', 'TATASTEEL', 'SBILIFE', 'COALINDIA', 'GRASIM',
            'BAJAJFINSV', 'CIPLA', 'JSWSTEEL', 'HEROMOTOCO', 'BRITANNIA', 'INDUSINDBK',
            'DRREDDY', 'EICHERMOT', 'UPL', 'APOLLOHOSP', 'ADANIPORTS', 'BPCL',
            'DIVISLAB', 'TRENT', 'HINDALCO', 'ADANIENT', 'BAJAJ-AUTO', 'INFY'
        ]
        
        # Clean symbol (remove .NS or .BO suffix)
        base_symbol = symbol.replace('.NS', '').replace('.BO', '')
        
        return base_symbol in nifty50_stocks
    
    def get_nifty50_config(self, symbol, price_level):
        """Get optimized configuration for Nifty 50 stocks"""
        
        # Sector-wise optimization for Nifty 50
        sector_configs = {
            # IT Sector (high liquidity, stable)
            'TCS': {'volatility_adj': 0.9, 'volume_adj': 0.8, 'stop_adj': 0.9},
            'INFY': {'volatility_adj': 0.9, 'volume_adj': 0.8, 'stop_adj': 0.9},
            'HCLTECH': {'volatility_adj': 0.9, 'volume_adj': 0.8, 'stop_adj': 0.9},
            'WIPRO': {'volatility_adj': 0.9, 'volume_adj': 0.8, 'stop_adj': 0.9},
            'TECHM': {'volatility_adj': 0.9, 'volume_adj': 0.8, 'stop_adj': 0.9},
            
            # Banking (high volume, moderate volatility)
            'HDFCBANK': {'volatility_adj': 1.0, 'volume_adj': 0.7, 'stop_adj': 1.0},
            'ICICIBANK': {'volatility_adj': 1.0, 'volume_adj': 0.7, 'stop_adj': 1.0},
            'SBIN': {'volatility_adj': 1.1, 'volume_adj': 0.7, 'stop_adj': 1.1},
            'AXISBANK': {'volatility_adj': 1.1, 'volume_adj': 0.8, 'stop_adj': 1.1},
            'KOTAKBANK': {'volatility_adj': 1.0, 'volume_adj': 0.8, 'stop_adj': 1.0},
            
            # High volatility stocks
            'RELIANCE': {'volatility_adj': 1.2, 'volume_adj': 0.6, 'stop_adj': 1.2},
            'TATAMOTORS': {'volatility_adj': 1.3, 'volume_adj': 0.9, 'stop_adj': 1.3},
            'TATASTEEL': {'volatility_adj': 1.3, 'volume_adj': 0.9, 'stop_adj': 1.3},
            'BAJFINANCE': {'volatility_adj': 1.2, 'volume_adj': 0.8, 'stop_adj': 1.2},
        }
        
        base_symbol = symbol.replace('.NS', '').replace('.BO', '')
        sector_adj = sector_configs.get(base_symbol, {
            'volatility_adj': 1.0, 'volume_adj': 0.8, 'stop_adj': 1.0  # Default
        })
        
        # Calculate position size based on stock price (₹50K base)
        if price_level > 3000:      # Very high-priced (₹3000+) like MRF
            position_size = 50000 // price_level * 15
        elif price_level > 1500:    # High-priced (₹1500-3000) like NESTLEIND
            position_size = 50000 // price_level * 25
        elif price_level > 500:     # Medium-priced (₹500-1500) most Nifty 50
            position_size = 50000 // price_level * 50
        else:                       # Lower-priced (<₹500)
            position_size = 50000 // price_level * 100
        
        return {
            'position_size': max(1, int(position_size)),  # Ensure at least 1 share
            'volatility_threshold': self.nifty50_params['volatility_threshold'] * sector_adj['volatility_adj'],
            'volume_threshold_mult': self.nifty50_params['volume_multiplier'] * sector_adj['volume_adj'],
            'stop_loss_mult': self.nifty50_params['stop_loss_mult'] * sector_adj['stop_adj'],
            'is_nifty50': True,
            'sector_type': self.get_stock_sector(base_symbol)
        }
    
    def get_stock_sector(self, symbol):
        """Get sector classification for Nifty 50 stock"""
        sectors = {
            'IT': ['TCS', 'HCLTECH', 'WIPRO', 'TECHM'],
            'Banking': ['HDFCBANK', 'ICICIBANK', 'SBIN', 'AXISBANK', 'KOTAKBANK', 'INDUSINDBK'],
            'Energy': ['RELIANCE', 'ONGC', 'BPCL', 'COALINDIA', 'POWERGRID', 'NTPC'],
            'Auto': ['MARUTI', 'TATAMOTORS', 'M&M', 'BAJAJ-AUTO', 'HEROMOTOCO', 'EICHERMOT'],
            'FMCG': ['ITC', 'HINDUNILVR', 'NESTLEIND', 'BRITANNIA', 'TATACONSUM'],
            'Pharma': ['SUNPHARMA', 'CIPLA', 'DRREDDY', 'DIVISLAB', 'APOLLOHOSP'],
            'Materials': ['ULTRACEMCO', 'ASIANPAINT', 'JSWSTEEL', 'TATASTEEL', 'HINDALCO', 'GRASIM'],
            'Financials': ['BAJFINANCE', 'BAJAJFINSV', 'HDFCLIFE', 'SBILIFE', 'LICI'],
            'Telecom': ['BHARTIARTL'],
            'Conglomerate': ['LT', 'ADANIPORTS', 'ADANIENT'],
            'Consumer': ['TITAN', 'TRENT'],
            'Utilities': ['UPL']
        }
        
        for sector, stocks in sectors.items():
            if symbol in stocks:
                return sector
        return 'Other'
    
    def calibrate_nifty50_stock(self, symbol, lookback_bars=50):
        """Calibrate parameters specifically for Nifty 50 stocks"""
        if len(self.data) < lookback_bars:
            return  # Not enough data for calibration
        
        # Verify it's a Nifty 50 stock
        if not self.is_nifty50_stock(symbol):
            self.log(f"⚠️  {symbol} is NOT a Nifty 50 stock - strategy optimized for Nifty 50 only!")
            return
        
        # Calculate symbol's characteristics
        recent_atr = []
        recent_prices = []
        recent_volumes = []
        
        for i in range(min(lookback_bars, len(self.data))):
            if len(self.data) > i and self.dataclose[-i] > 0:
                atr_pct = self.atr[-i] / self.dataclose[-i] if self.atr[-i] > 0 else 0
                recent_atr.append(atr_pct)
                recent_prices.append(self.dataclose[-i])
                recent_volumes.append(self.datavolume[-i])
        
        if not recent_atr:
            return
        
        avg_volatility = sum(recent_atr) / len(recent_atr)
        avg_price = sum(recent_prices) / len(recent_prices)
        avg_volume = sum(recent_volumes) / len(recent_volumes)
        
        # Get Nifty 50 specific configuration
        config = self.get_nifty50_config(symbol, avg_price)
        
        # Store calibrated parameters
        self.symbol_params[symbol] = {
            'position_size': config['position_size'],
            'stop_loss_mult': config['stop_loss_mult'],
            'volume_threshold_mult': config['volume_threshold_mult'],
            'volatility_threshold': config['volatility_threshold'],
            'avg_volatility': avg_volatility,
            'avg_price': avg_price,
            'is_nifty50': True,
            'sector': config['sector_type'],
            'calibrated': True
        }
        
        self.log(f"� NIFTY 50 CALIBRATED {symbol} ({config['sector_type']}): Vol={avg_volatility:.4f}, Price=₹{avg_price:.2f}, PosSize={config['position_size']}")
        self.log(f"💡 Optimized for high liquidity and stable Nifty 50 characteristics")

    def log(self, txt):
        print(f"{txt}")
        
    def next(self):
        if len(self.data) < self.params.lookback_period:
            return
            
        # Get symbol info - Nifty 50 focus
        symbol = self.datas[0]._name if hasattr(self.datas[0], '_name') else 'UNKNOWN'
        
        # Auto-calibrate Nifty 50 stock parameters if not done yet
        if symbol not in self.symbol_params or not self.symbol_params.get(symbol, {}).get('calibrated', False):
            self.calibrate_nifty50_stock(symbol)
        
        # Get symbol-specific parameters (optimized for Nifty 50)
        symbol_params = self.symbol_params.get(symbol, {
            'position_size': 50000,  # Default ₹50,000 position for Nifty 50
            'stop_loss_mult': 0.9,   # Tighter stops for liquid stocks
            'volume_threshold_mult': 0.8,  # Lower volume requirement
            'volatility_threshold': 0.0006  # Lower threshold for stable stocks
        })
        
        # Nifty 50 optimized trading hours (9:30 AM to 3:00 PM IST)
        current_time = self.data.datetime.time(0)
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        # Convert to decimal hours
        current_decimal_hour = current_hour + current_minute / 60.0
        
        # Nifty 50 optimal trading window: 9:30 AM - 3:00 PM
        optimal_window = 9.5 <= current_decimal_hour <= 15.0
        
        if not optimal_window:
            return
            
        # Universal market condition filter - adapts to symbol's volatility profile
        current_volatility = self.atr[0] / self.dataclose[0] if self.dataclose[0] > 0 else 0
        volatility_threshold = symbol_params.get('volatility_threshold', self.market_volatility_threshold)
        if current_volatility < volatility_threshold:
            return
        
        # Extract symbol-specific parameters
        position_size = symbol_params.get('position_size', self.params.position_size)
        stop_loss_mult = symbol_params.get('stop_loss_mult', 1.0)
        volume_threshold_mult = symbol_params.get('volume_threshold_mult', 1.0)
        
        # Manage existing position with dynamic volatility-based stops
        if self.position:
            current_price = self.dataclose[0]
            hold_time = len(self.data) - self.entry_bar
            dynamic_stop = self.atr[0] * stop_loss_mult
            if self.position.size > 0:  # Long position
                stop_price = self.entry_price - dynamic_stop
                target_price = self.entry_price * (1 + self.params.take_profit_pct / 100)
                if current_price <= stop_price:
                    self.order = self.close()
                    self.log(f"🛑 DYN STOP: {current_price:.2f} (ATR {dynamic_stop:.2f})")
                    return
                elif current_price >= target_price:
                    self.order = self.close()
                    self.log(f"🎯 TARGET: {current_price:.2f}")
                    return
                elif hold_time >= self.params.max_hold_bars:
                    self.order = self.close()
                    self.log(f"⏰ TIME: {current_price:.2f}")
                    return
            elif self.position.size < 0:  # Short position
                stop_price = self.entry_price + dynamic_stop
                target_price = self.entry_price * (1 - self.params.take_profit_pct / 100)
                if current_price >= stop_price:
                    self.order = self.close()
                    self.log(f"🛑 DYN SHORT STOP: {current_price:.2f} (ATR {dynamic_stop:.2f})")
                    return
                elif current_price <= target_price:
                    self.order = self.close()
                    self.log(f"🎯 SHORT TARGET: {current_price:.2f}")
                    return
                elif hold_time >= self.params.max_hold_bars:
                    self.order = self.close()
                    self.log(f"⏰ SHORT TIME: {current_price:.2f}")
                    return
        # Skip if we have position or pending order
        if self.position or self.order:
            return
        # Optimized entry logic for 1-minute scalping
        current_close = self.dataclose[0]
        current_volume = self.datavolume[0]
        resistance_level = self.resistance[-1]
        support_level = self.support[-1]
        # Nifty 50 optimized volume and momentum checks
        base_volume_threshold = 0.8 * volume_threshold_mult  # Lower for high liquidity
        volume_ok = current_volume > (self.volume_ma[0] * base_volume_threshold)
        volume_spike = current_volume > (self.volume_ma[0] * base_volume_threshold * 1.4)  # Lower spike requirement
        price_momentum = current_close > self.price_ma[0] if self.price_ma[0] > 0 else False
        # LONG ENTRY: Enhanced breakout with momentum confirmation
        if (current_close > resistance_level and volume_ok and 
            self.rsi[0] > 50 and self.rsi[0] < 75 and price_momentum):
            breakout_strength = ((current_close - resistance_level) / resistance_level * 100)
            if breakout_strength >= 0.005:  # 0.5% minimum breakout
                size = position_size
                if volume_spike:
                    size = int(size * 1.2)
                self.order = self.buy(size=size)
                self.entry_price = current_close
                self.entry_bar = len(self.data)
                vol_ratio = current_volume / self.volume_ma[0]
                self.log(f"🟢 LONG: {current_close:.2f} | Strength: {breakout_strength:.2f}% | Vol: {vol_ratio:.1f}x | RSI: {self.rsi[0]:.1f} | ATR: {self.atr[0]:.2f}")
        # SHORT ENTRY: Enhanced breakdown with bearish momentum
        elif (current_close < support_level and volume_ok and
              self.rsi[0] < 50 and self.rsi[0] > 25 and not price_momentum):
            breakdown_strength = ((support_level - current_close) / support_level * 100)
            if breakdown_strength >= 0.005:  # 0.5% minimum breakdown
                size = position_size
                if volume_spike:
                    size = int(size * 1.2)
                self.order = self.sell(size=size)
                self.entry_price = current_close
                self.entry_bar = len(self.data)
                vol_ratio = current_volume / self.volume_ma[0]
                self.log(f"🔴 SHORT: {current_close:.2f} | Strength: {breakdown_strength:.2f}% | Vol: {vol_ratio:.1f}x | RSI: {self.rsi[0]:.1f} | ATR: {self.atr[0]:.2f}")
            
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                pass  # Entry logged in next()
            elif order.issell():
                if self.entry_price > 0:
                    pnl = (order.executed.price - self.entry_price) * order.executed.size
                    self.total_pnl += pnl
                    pnl_pct = (pnl / (self.entry_price * abs(order.executed.size))) * 100
                    self.trade_count += 1
                    if pnl > 0:
                        self.wins += 1
                        status = "WIN ✅"
                    else:
                        status = "LOSS ❌"
                    self.log(f"EXIT: {order.executed.price:.2f} | PnL: ${pnl:.2f} ({pnl_pct:+.2f}%) | {status}")
                    # Track per-stock stats
                    symbol = self.datas[0]._name if hasattr(self.datas[0], '_name') else str(self.datas[0])
                    if symbol not in self.stock_trade_stats:
                        self.stock_trade_stats[symbol] = {'trades': 0, 'pnl': 0.0}
                    self.stock_trade_stats[symbol]['trades'] += 1
                    self.stock_trade_stats[symbol]['pnl'] += pnl
                    self.entry_price = 0
        self.order = None
        
    def stop(self):
        win_rate = (self.wins / self.trade_count * 100) if self.trade_count > 0 else 0
        final_value = self.broker.get_value()
        total_return = ((final_value / 100000) - 1) * 100
        daily_return = total_return / 10
        
        print(f"\n🏁 BALANCED BREAKOUT RESULTS:")
        print(f"💰 Total Return: {total_return:+.2f}%")
        print(f"📈 Daily Average: {daily_return:+.2f}%")
        print(f"🎯 Total Trades: {self.trade_count}")
        print(f"✅ Win Rate: {win_rate:.1f}%")
        print(f"💵 Total PnL: ${self.total_pnl:.2f}")
        
        # Per-stock trade summary
        if self.stock_trade_stats:
            print("\n📊 Per-Stock Trade Summary:")
            for symbol, stats in self.stock_trade_stats.items():
                print(f"  {symbol}: Trades={stats['trades']}, PnL=${stats['pnl']:.2f}")
            total_pnl = sum(stats['pnl'] for stats in self.stock_trade_stats.values())
            print(f"  TOTAL PnL (all stocks): ${total_pnl:.2f}")
        
        if self.trade_count > 0:
            avg_trade = self.total_pnl / self.trade_count
            print(f"📊 Average trade: ${avg_trade:.2f}")
            
            # Estimate what we need for 1% daily
            needed_daily = 1000  # $1000 per day for 1%
            needed_per_trade = needed_daily / (self.trade_count / 10)  # trades per day
            print(f"🎯 Need ${needed_per_trade:.2f} per trade for 1% daily target")
        
        if daily_return >= 1.0:
            print("🎯 TARGET ACHIEVED!")
        elif daily_return >= 0.5:
            print("📈 Close to target - minor tweaks needed!")
        elif daily_return >= 0.2:
            print("🔧 Good base - optimize position sizing")
        else:
            print("📉 Need strategy refinement")

