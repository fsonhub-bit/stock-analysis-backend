
import os
import sys
import asyncio
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
from services.db_client import supabase
from services.macro import macro_analyzer
from services.market_data import fetch_global_market_data
from app.config import config
import json

# Adjust path to import services if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Manually calculate RSI(14), SMA(75), BB(20,2), ATR(14) using pandas.
    """
    # SMA 75
    df['SMA75'] = df['Close'].rolling(window=75).mean()

    # Bollinger Bands (20, 2)
    sma20 = df['Close'].rolling(window=20).mean()
    std20 = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = sma20 + (2 * std20)
    
    # RSI 14
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    # Note: Wilder's smoothing is standard for RSI, but simple rolling is often used in approximations.
    # For better accuracy with Wilder:
    # gain = delta.where(delta>0, 0).ewm(alpha=1/14, adjust=False).mean()
    # loss = -delta.where(delta<0, 0).ewm(alpha=1/14, adjust=False).mean()

    # ATR 14
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    # Simple Moving Average matches typical TR calculation roughly
    df['ATR'] = pd.Series(true_range).rolling(window=14).mean()
    
    return df

async def main():
    print(f"[{datetime.now()}] Starting Daily Analysis Batch (Manual Tech Check)...")

    # 1. Macro Analysis
    print(">>> 1. Performing Global Macro Analysis...")
    try:
        global_data = fetch_global_market_data()
        headlines = macro_analyzer.fetch_news_headlines()
        macro_result = macro_analyzer.analyze_sentiment(headlines, global_data)
        
        # Save to DB (daily_macro_log)
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        # Extract individual global indices
        usd_jpy = global_data.get("USD/JPY", {}).get("price")
        sox = global_data.get("PHLX Semiconductor (SOX)", {}).get("price")
        nasdaq = global_data.get("NASDAQ Composite", {}).get("price")
        
        macro_record = {
            "date": today_str,
            "summary": macro_result.get("reason_summary", ""),
            "usd_jpy": usd_jpy,
            "sox_index": sox,
            "nasdaq_index": nasdaq,
            "sector_scores": macro_result # JSONB
        }
        
        # Upsert Macro Log
        supabase.table("daily_macro_log").upsert(macro_record).execute()
        print("    Saved Macro Log to DB.")
        
    except Exception as e:
        print(f"!!! Error in Macro Analysis: {e}")
        # Continue? Yes, technical analysis is still valuable.
        macro_result = {}

    # 2. Load Tickers
    print(">>> 2. Loading Tickers...")
    try:
        tickers_df = pd.read_csv("batch_jobs/data/prime_tickers.csv")
        tickers = tickers_df['ticker'].tolist()
        ticker_sector_map = dict(zip(tickers_df['ticker'], tickers_df['sector']))
        print(f"    Loaded {len(tickers)} tickers.")
    except FileNotFoundError:
        print("!!! prime_tickers.csv not found. Aborting.")
        return

    # 3. Bulk Analysis Loop
    print(">>> 3. Starting Bulk Analysis...")
    
    # Process in chunks of 50 for yfinance
    chunk_size = 50
    results_to_insert = []
    
    for i in range(0, len(tickers), chunk_size):
        chunk_tickers = tickers[i:i + chunk_size]
        print(f"    Processing chunk {i}-{i+len(chunk_tickers)}...")
        
        try:
            # Bulk download from yfinance
            tickers_str = " ".join(chunk_tickers)
            # Fetch enough data for SMA75 (needs ~4-6 months)
            data = yf.download(tickers_str, period="6mo", group_by='ticker', auto_adjust=True, threads=True)
            
            for ticker in chunk_tickers:
                try:
                    # Handle single ticker result vs multi-ticker dataframe structure differences in yfinance
                    if len(chunk_tickers) == 1:
                        df = data
                    else:
                        if ticker not in data.columns.levels[0]:
                             continue
                        df = data[ticker]

                    if df.empty or len(df) < 75:
                        continue

                    # Calculate Indicators Manually
                    df = calculate_technical_indicators(df)
                    
                    # Latest row
                    row = df.iloc[-1]
                    
                    # Ensure columns exist
                    if pd.isna(row['BB_Upper']) or pd.isna(row['ATR']) or pd.isna(row['RSI']):
                        continue
                        
                    bb_upper = row['BB_Upper']
                    atr = row['ATR']
                    close = row['Close']
                    rsi = row['RSI']
                    sma75 = row['SMA75']
                    
                    # --- Logic ---
                    # 1. Trend: Close > SMA75
                    # 2. Trigger: RSI < 35
                    # 3. S-Stock: Upside Potential > 2*ATR
                    
                    signal = "WAIT"
                    reason = []
                    
                    if close > sma75:
                        if rsi < 35: 
                            signal = "BUY" # Candidate
                            reason.append("RSI Low & Uptrend")
                            
                            upside_potential = bb_upper - close
                            if upside_potential > (atr * 2):
                                reason.append("High Upside > 2xATR")
                            else:
                                signal = "WAIT" # Failed S-Stock criteria
                                
                    upside_ratio = (bb_upper - close) / atr if atr > 0 else 0
                    
                    # Macro Score Integration
                    # Macro Score Integration
                    english_sector = ticker_sector_map.get(ticker, "Unknown")
                    
                    # Mapping English JPX 33 Sectors to Macro Categories
                    sector_map = {
                        "Fishery, Agriculture and Forestry": "食品",
                        "Foods": "食品",
                        "Construction": "建設・不動産",
                        "Real Estate": "建設・不動産",
                        "Textiles and Apparels": "素材・化学",
                        "Chemicals": "素材・化学",
                        "Pharmaceutical": "医薬品",
                        "Oil and Coal Products": "エネルギー",
                        "Mining": "エネルギー",
                        "Rubber Products": "素材・化学",
                        "Glass and Ceramics Products": "素材・化学",
                        "Pulp and Paper": "素材・化学",
                        "Iron and Steel": "機械・鉄鋼",
                        "Nonferrous Metals": "機械・鉄鋼",
                        "Metal Products": "機械・鉄鋼",
                        "Machinery": "機械・鉄鋼",
                        "Electric Appliances": "電気・精密",
                        "Precision Instruments": "電気・精密",
                        "Transportation Equipment": "自動車・輸送機",
                        "Other Products": "小売・サービス",
                        "Information & Communication": "情報・通信",
                        "Services": "小売・サービス",
                        "Electric Power and Gas": "インフラ・運輸",
                        "Land Transportation": "インフラ・運輸",
                        "Marine Transportation": "インフラ・運輸",
                        "Air Transportation": "インフラ・運輸",
                        "Warehousing and Harbor Transportation Services": "インフラ・運輸",
                        "Wholesale Trade": "商社",
                        "Retail Trade": "小売・サービス",
                        "Banks": "銀行・金融",
                        "Securities and Commodities Futures": "銀行・金融",
                        "Insurance": "銀行・金融",
                        "Other Financing Business": "銀行・金融"
                    }
                    
                    target_category = sector_map.get(english_sector, "全体")
                    
                    macro_score = 0
                    if macro_result:
                        # Try specific category, then "全体", then 0
                        macro_score = macro_result.get(target_category, macro_result.get("全体", 0))

                    if macro_score < 0 and signal == "BUY":
                         reason.append(f"Macro Negative ({macro_score})")

                    # Prepare DB Record
                    # Handle NaN / Inf
                    if pd.isna(upside_ratio) or np.isinf(upside_ratio): upside_ratio = 0
                    if pd.isna(atr) or np.isinf(atr): atr = 0
                    
                    results_to_insert.append({
                        "date": today_str,
                        "ticker": ticker,
                        "sector": sector,
                        "close_price": float(close),
                        "rsi_14": float(rsi),
                        "atr_14": float(atr),
                        "upside_ratio": float(upside_ratio),
                        "macro_score": int(macro_score),
                        "signal": signal,
                        "reason": ", ".join(reason) if reason else None
                    })
                    
                except Exception as e:
                    # print(f"    Error processing {ticker} detail: {e}")
                    continue

        except Exception as e:
            print(f"!!! Error in Chunk {i}: {e}")

    # 4. DB Upsert
    print(f">>> 4. Saving {len(results_to_insert)} records to DB...")
    if results_to_insert:
        # Upsert in chunks of 500
        db_chunk_size = 500
        for i in range(0, len(results_to_insert), db_chunk_size):
            chunk = results_to_insert[i:i + db_chunk_size]
            try:
                # ignore_duplicates=False means upsert
                supabase.table("market_analysis_log").upsert(chunk).execute()
                print(f"    Upserted batch {i}-{i+len(chunk)}")
            except Exception as e:
                print(f"!!! DB Error: {e}")

    print(f"[{datetime.now()}] Batch Analysis Complete.")

if __name__ == "__main__":
    asyncio.run(main())
