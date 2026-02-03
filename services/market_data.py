import yfinance as yf
import pandas as pd
from app.config import config

from datetime import datetime, timedelta

def fetch_historical_data(ticker: str, period: str = "6mo", end_date: datetime = None) -> pd.DataFrame:
    """
    Fetch historical data for a given ticker using yfinance.
    If end_date is provided, data is fetched up to that date (exclusive).
    """
    try:
        if end_date:
            # yfinance end is exclusive. To include target_date, we need target_date + 1 day
            # But here end_date usually implies "Analysis Date".
            # If we want data available ON Analysis Date morning, we usually mean data up to "Yesterday Close".
            # But lets assume input is specific.
            # Usually yf.download(end=X) fetches up to X-1.
            # If I supply 2024-02-01, I want data UP TO 2024-02-01?
            # Let's standardize: end_date provided means "latest data point should be ON or BEFORE end_date".
            # If I pass 2024-02-02, I want close of 2024-02-02 if available?
            # yfinance 'end' is exclusive. So to get 2024-02-02, end must be 2024-02-03.
            end_val = (end_date + timedelta(days=1)).strftime('%Y-%m-%d')
            data = yf.download(ticker, end=end_val, progress=False, multi_level_index=False)
            # Slice by period is tricky with download, as start defaults to 1900.
            # Ideally we calculate start based on period.
            # But yfinance accepts 'period' OR 'start/end'.
            # If end is specified, 'period' argument is ignored by yfinance in some versions or conflicts.
            # So we should calculate start.
            if period == "6mo":
                start_val = (end_date - timedelta(days=180)).strftime('%Y-%m-%d')
                data = yf.download(ticker, start=start_val, end=end_val, progress=False, multi_level_index=False)
            else:
                # Default fallback
                data = yf.download(ticker, end=end_val, progress=False, multi_level_index=False)
        else:
            data = yf.download(ticker, period=period, progress=False, multi_level_index=False)

        if data.empty:
            print(f"Warning: No data found for {ticker}")
            return pd.DataFrame()
        
        # Ensure standard columns
        required_cols = {'Open', 'High', 'Low', 'Close', 'Volume'}
        if not required_cols.issubset(data.columns):
             if isinstance(data.columns, pd.MultiIndex):
                 data.columns = data.columns.get_level_values(0)
             
        return data
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

def fetch_global_market_data(target_date: datetime = None) -> dict:
    """
    Fetch global market data (US indices, FX) change percentage.
    If target_date is provided, calculates change for that specific date.
    """
    data_summary = {}
    
    for ticker, name in config.GLOBAL_TICKERS.items():
        try:
            # yfinance
            ticker_obj = yf.Ticker(ticker)
            
            if target_date:
                # Need history around target date
                # Fetch 5 days ending at target_date+1
                end_val = (target_date + timedelta(days=1)).strftime('%Y-%m-%d')
                start_val = (target_date - timedelta(days=7)).strftime('%Y-%m-%d')
                hist = ticker_obj.history(start=start_val, end=end_val)
            else:
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
