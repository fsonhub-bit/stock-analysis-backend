import yfinance as yf
import pandas as pd
from app.config import config

def fetch_historical_data(ticker: str, period: str = "6mo") -> pd.DataFrame:
    """
    Fetch historical data for a given ticker using yfinance.
    """
    try:
        data = yf.download(ticker, period=period, progress=False, multi_level_index=False)
        if data.empty:
            print(f"Warning: No data found for {ticker}")
            return pd.DataFrame()
        
        # Ensure standard columns
        required_cols = {'Open', 'High', 'Low', 'Close', 'Volume'}
        if not required_cols.issubset(data.columns):
             # Handle multi-level columns if they still appear or unexpected format
             # yf.download(multi_level_index=False) should handle this in newer versions,
             # but sometimes it returns MultiIndex columns.
             if isinstance(data.columns, pd.MultiIndex):
                 data.columns = data.columns.get_level_values(0)
             
        return data
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

def fetch_global_market_data() -> dict:
    """
    Fetch global market data (US indices, FX) change percentage.
    """
    data_summary = {}
    
    for ticker, name in config.GLOBAL_TICKERS.items():
        try:
            # yfinance
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period=config.GLOBAL_DATA_PERIOD)
            
            if len(hist) < 2:
                continue

            latest = hist.iloc[-1]
            prev = hist.iloc[-2]
            
            change_pct = ((latest['Close'] - prev['Close']) / prev['Close']) * 100
            
            data_summary[name] = {
                "price": float(latest['Close']),
                "change_pct": float(change_pct),
                "trend": "UP" if change_pct > 0 else "DOWN"
            }
            
        except Exception as e:
            print(f"Error fetching global data for {name} ({ticker}): {e}")
            
    return data_summary
