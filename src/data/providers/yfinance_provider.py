import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

class YFinanceProvider:
    """
    Yahoo Finance data provider for intraday trading bot
    Handles data fetching, cleaning, and preprocessing
    """
    
    def __init__(self):
        self.cache = {}
        print("📡 YFinance Data Provider Initialized")
    
    def get_data(self, symbol, period='10d', interval='5m', preprocess=True):
        """
        Fetch intraday data from Yahoo Finance
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL', 'TSLA')
            period (str): Data period ('1d', '5d', '10d', '1mo', '3mo')
            interval (str): Data interval ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h')
            preprocess (bool): Whether to clean and preprocess data
            
        Returns:
            pd.DataFrame: OHLCV data with datetime index
        """
        
        cache_key = f"{symbol}_{period}_{interval}"
        
        try:
            print(f"📊 Fetching {symbol} data - Period: {period}, Interval: {interval}")
            
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Fetch data
            data = ticker.history(
                period=period,
                interval=interval,
                auto_adjust=True,  # Adjust for splits and dividends
                prepost=False,     # Exclude pre/post market data
                repair=True        # Fix bad data points
            )
            
            if data.empty:
                print(f"❌ No data received for {symbol}")
                return None
            
            print(f"✅ Fetched {len(data)} bars for {symbol}")
            
            if preprocess:
                data = self._preprocess_data(data, symbol)
            
            # Cache the data
            self.cache[cache_key] = data
            
            return data
            
        except Exception as e:
            print(f"❌ Error fetching data for {symbol}: {str(e)}")
            return None
    
    def _preprocess_data(self, data, symbol):
        """
        Clean and preprocess the raw data
        
        Args:
            data (pd.DataFrame): Raw OHLCV data
            symbol (str): Stock symbol for logging
            
        Returns:
            pd.DataFrame: Cleaned data
        """
        
        original_length = len(data)
        
        # Remove rows with any NaN values
        data = data.dropna()
        
        # Remove rows where OHLC values are invalid
        data = data[
            (data['Open'] > 0) & 
            (data['High'] > 0) & 
            (data['Low'] > 0) & 
            (data['Close'] > 0) &
            (data['Volume'] >= 0)
        ]
        
        # Ensure High >= Low, High >= Open, High >= Close, Low <= Open, Low <= Close
        data = data[
            (data['High'] >= data['Low']) &
            (data['High'] >= data['Open']) &
            (data['High'] >= data['Close']) &
            (data['Low'] <= data['Open']) &
            (data['Low'] <= data['Close'])
        ]
        
        # Remove extreme outliers (price changes > 50% in one bar)
        data['price_change'] = data['Close'].pct_change()
        data = data[abs(data['price_change']) <= 0.5]
        data = data.drop('price_change', axis=1)
        
        # Filter trading hours (9:30 AM - 4:00 PM EST)
        if not data.empty:
            data = self._filter_trading_hours(data)
        
        cleaned_length = len(data)
        removed_bars = original_length - cleaned_length
        
        if removed_bars > 0:
            print(f"🧹 Cleaned {symbol} data: Removed {removed_bars} invalid bars")
        
        return data
    
    def _filter_trading_hours(self, data):
        """
        Filter data to regular trading hours (9:30 AM - 4:00 PM EST)
        
        Args:
            data (pd.DataFrame): OHLCV data
            
        Returns:
            pd.DataFrame: Filtered data
        """
        
        # Convert to Eastern Time if not already
        if data.index.tz is None:
            # Assume UTC and convert to Eastern
            data.index = data.index.tz_localize('UTC').tz_convert('America/New_York')
        elif data.index.tz != pytz.timezone('America/New_York'):
            data.index = data.index.tz_convert('America/New_York')
        
        # Filter to trading hours (9:30 AM - 4:00 PM EST)
        trading_hours = data.between_time('09:30', '16:00')
        
        # Remove weekends
        trading_days = trading_hours[trading_hours.index.dayofweek < 5]
        
        return trading_days
    
    def get_multiple_symbols(self, symbols, period='10d', interval='5m'):
        """
        Fetch data for multiple symbols
        
        Args:
            symbols (list): List of stock symbols
            period (str): Data period
            interval (str): Data interval
            
        Returns:
            dict: Dictionary of symbol -> DataFrame mappings
        """
        
        results = {}
        
        for symbol in symbols:
            print(f"\n📊 Processing {symbol}...")
            data = self.get_data(symbol, period, interval)
            if data is not None and len(data) > 50:  # Minimum bars required
                results[symbol] = data
                print(f"✅ {symbol}: {len(data)} bars loaded")
            else:
                print(f"❌ {symbol}: Insufficient data")
        
        return results
    
    def get_current_price(self, symbol):
        """
        Get current/latest price for a symbol
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            float: Current price or None if error
        """
        
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='1d', interval='1m')
            if not hist.empty:
                return hist['Close'].iloc[-1]
        except:
            pass
        
        return None
    
    def get_market_status(self):
        """
        Check if market is currently open
        
        Returns:
            bool: True if market is open
        """
        
        try:
            # Get current time in Eastern timezone
            et = pytz.timezone('America/New_York')
            now = datetime.now(et)
            
            # Check if it's a weekday
            if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return False
            
            # Check trading hours (9:30 AM - 4:00 PM EST)
            market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
            
            return market_open <= now <= market_close
            
        except:
            return False
    
    def validate_symbol(self, symbol):
        """
        Validate if a symbol exists and has data
        
        Args:
            symbol (str): Stock symbol to validate
            
        Returns:
            bool: True if symbol is valid
        """
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Check if we got valid info
            if 'symbol' in info or 'shortName' in info:
                return True
                
        except:
            pass
        
        return False
    
    def get_symbol_info(self, symbol):
        """
        Get basic information about a symbol
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            dict: Symbol information
        """
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'name': info.get('shortName', 'Unknown'),
                'sector': info.get('sector', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'avg_volume': info.get('averageVolume', 0),
                'price': info.get('currentPrice', 0)
            }
            
        except Exception as e:
            print(f"❌ Error getting info for {symbol}: {str(e)}")
            return None

# Example usage and testing
if __name__ == "__main__":
    provider = YFinanceProvider()
    
    # Test single symbol
    print("Testing single symbol fetch...")
    data = provider.get_data('AAPL', period='5d', interval='5m')
    if data is not None:
        print(f"AAPL data shape: {data.shape}")
        print(f"Date range: {data.index[0]} to {data.index[-1]}")
        print(f"Sample data:\n{data.head()}")
    
    # Test multiple symbols
    print("\nTesting multiple symbols...")
    symbols = ['AAPL', 'TSLA', 'MSFT']
    multi_data = provider.get_multiple_symbols(symbols, period='3d', interval='5m')
    print(f"Successfully loaded {len(multi_data)} symbols")
    
    # Test market status
    print(f"\nMarket open: {provider.get_market_status()}")
    
    # Test symbol validation
    print(f"AAPL valid: {provider.validate_symbol('AAPL')}")
    print(f"INVALID valid: {provider.validate_symbol('INVALID123')}")