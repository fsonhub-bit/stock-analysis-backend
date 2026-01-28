
import pandas as pd
from datetime import datetime
from app.config import config
from app.models import AnalysisResult

def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate RSI, SMA75, Bollinger Bands (20, 2std), and ATR(14).
    """
    if df.empty:
        return df

    # 1. RSI (14)
    period = 14
    delta = df['Close'].diff()
    # Simple moving average for RSI as per user request (or consistent with previous impl)
    # Using EWM matching previous behavior for smoother RSI
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # 2. SMA (75)
    df['SMA75'] = df['Close'].rolling(window=75).mean()

    # 3. Bollinger Bands (20, 2std)
    sma20 = df['Close'].rolling(window=20).mean()
    std20 = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = sma20 + (std20 * 2)

    # 4. ATR (14)
    # TR = max(high-low, |high-prev_close|, |low-prev_close|)
    prev_close = df['Close'].shift()
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - prev_close).abs()
    low_close = (df['Low'] - prev_close).abs()
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()
    
    return df

def analyze_ticker(ticker: str, df: pd.DataFrame) -> AnalysisResult:
    """
    Analyze ticker based on S-Stock logic:
    1. Trend Check (Close > 75SMA)
    2. Trigger (RSI < 30)
    3. Safety Check (Upside > ATR * 2)
    """
    # Ensure indicators are calculated
    if 'RSI' not in df.columns:
        df = calculate_technical_indicators(df)
        
    latest = df.iloc[-1]
    
    # Defaults
    signal = "WAIT"
    reason = ""
    
    # Handle NaN values (e.g., if not enough data for 75 SMA)
    if pd.isna(latest.get('SMA75')) or pd.isna(latest.get('ATR')):
        return AnalysisResult(
            ticker=ticker,
            current_price=latest['Close'],
            rsi=latest.get('RSI', 0),
            atr=0.0,
            target_price=0.0,
            upside_ratio=0.0,
            signal="WAIT",
            reason="データ不足 (SMA75/ATR計算不可)",
            timestamp=datetime.now()
        )

    # Logic
    # 1. Trend Filter
    if latest['Close'] < latest['SMA75']:
        reason = "長期トレンド弱含み (Close < SMA75)"
    
    # 2. RSI Trigger
    elif latest['RSI'] > 30:
        reason = f"RSI中立 ({latest['RSI']:.1f})"
        
    else:
        # 3. S-Stock Safety Check
        upside = latest['BB_Upper'] - latest['Close']
        atr = latest['ATR']
        
        ratio = 0.0
        if atr > 0:
            ratio = upside / atr
            
        if ratio > 2.0:
            signal = "BUY"
            reason = f"🔥🔥 S株適正あり (上値余地 ATR×{ratio:.1f}倍)"
        else:
            signal = "WAIT"
            reason = f"RSI到達だが値幅余地不足 (ATR×{ratio:.1f}倍)"

    return AnalysisResult(
        ticker=ticker,
        current_price=float(latest['Close']),
        rsi=float(latest['RSI']),
        atr=float(latest['ATR']),
        target_price=float(latest['BB_Upper']),
        upside_ratio=float(latest['BB_Upper'] - latest['Close']) / latest['ATR'] if latest['ATR'] > 0 else 0.0,
        signal=signal,
        reason=reason,
        timestamp=datetime.now()
    )
