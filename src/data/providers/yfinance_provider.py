import yfinance as yf
import pandas as pd
from datetime import time

class YFinanceProvider:
    def __init__(self):
        self.name = "YFinance"
    
    def get_data(self, symbol, period='5d', interval='5m'):
        try:
            print(f"📊 Fetching {interval} data for {symbol}...")
            
            # Get data WITHOUT pre/post market
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval, prepost=False)
            
            if data.empty:
                return None
            
            # STRICT market hours filter: 9:30 AM - 4:00 PM ONLY
            start_time = time(9, 30)
            end_time = time(16, 0)
            
            # Convert to ET timezone if needed
            if data.index.tz is None:
                data.index = data.index.tz_localize('US/Eastern')
            
            # Filter by time AND weekdays
            time_mask = (data.index.time >= start_time) & (data.index.time <= end_time)
            weekday_mask = data.index.weekday < 5
            
            data = data[time_mask & weekday_mask]
            
            if not data.empty:
                first_bar = data.index[0].strftime('%Y-%m-%d %H:%M')
                last_bar = data.index[-1].strftime('%Y-%m-%d %H:%M')
                print(f"✅ Got {len(data)} CLEAN market hours bars")
                print(f"   Range: {first_bar} to {last_bar}")
            
            return data
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
