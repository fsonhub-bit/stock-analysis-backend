
import pandas as pd
from app.config import config

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate RSI using pandas.
    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss
    """
    if df.empty or len(df) < period + 1:
        return pd.Series(dtype=float)

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)

    # Calculate average gain/loss
    # First `period` days is simple average, then smoothed
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    
    # Use simple rolling mean for this prototype to keep it simple and match common simple implementations.
    # For Wilder's smoothing (standard RSI), we would do e.g.:
    # avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    # avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    # But user asked for "Pandas to calculate RSI" without specifying Wilder's specifically, 
    # though Wilder's is standard. Let's use Wilder's method via EWM for accuracy.
    
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def judge_signal(rsi_value: float) -> str:
    """
    Judge BUY/SELL/WAIT based on RSI value.
    """
    if pd.isna(rsi_value):
        return "WAIT"
    
    if rsi_value <= config.RSI_OVERSOLD:
        return "BUY"
    elif rsi_value >= config.RSI_OVERBOUGHT:
        return "SELL"
    else:
        return "WAIT"
