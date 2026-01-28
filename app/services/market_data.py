
import yfinance as yf
import pandas as pd

def fetch_historical_data(ticker: str, period: str = "3mo") -> pd.DataFrame:
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
