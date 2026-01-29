
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

import requests
from bs4 import BeautifulSoup
import time
import re

# Adjust path to import services if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_yahoo_finance_data(ticker):
    """
    Scrape Profile, Earnings Date, Finance Highlights, and Company Name from Yahoo! Finance Japan.
    """
    # Remove '.T' for URL (e.g. 7203.T -> 7203)
    code = ticker.split('.')[0]
    base_url = f"https://finance.yahoo.co.jp/quote/{code}"
    
    data = {"profile": "", "finance": "", "earnings_date": "", "name_jp": ""}
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        
        # 1. Main Page (Earnings Date & Basic Info)
        res = requests.get(base_url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Company Name (Title or H1)
            h1 = soup.find('h1')
            if h1:
                # Text might be "ソフトバンクグループ(株)" or "ソフトバンクグループ(株)【9984】"
                raw_name = h1.text.strip()
                # Remove ticker if present (e.g. 【9984】)
                data['name_jp'] = re.sub(r'【\d+】.*', '', raw_name).strip()
            
            # Fallback to title
            if not data['name_jp']:
                title_text = soup.title.string if soup.title else ""
                match = re.search(r'^(.*?)(?:【\d+】)', title_text)
                if match:
                    data['name_jp'] = match.group(1).strip()

            # Feature/Profile
            # Robust search for "特色"
            # 1. Try class (often changes)
            profile_el = soup.find('p', class_='_6YdC6U3')
            
            # 2. Try text search for "【特色】" or "特色" in dt/span
            if not profile_el:
                feature_label = soup.find(string=re.compile("特色"))
                if feature_label:
                    # Often <span class="...">【特色】</span> <span class="...">Descr...</span>
                    try:
                       parent = feature_label.parent
                       # Check siblings
                       sibling = parent.find_next_sibling()
                       if sibling:
                           data['profile'] = sibling.text.strip()
                       else:
                           # Maybe in the same parent text?
                           full_text = parent.parent.text.replace(feature_label, "").strip()
                           if len(full_text) > 5 and len(full_text) < 200:
                               data['profile'] = full_text
                    except:
                        pass

            else:
                 data['profile'] = profile_el.text.strip()

            # Fallback to meta if still empty
            if not data['profile']:
                 meta_desc = soup.find('meta', attrs={'name': 'description'})
                 if meta_desc:
                     data['profile'] = meta_desc.get('content', '')
                 
            # Earnings Date
            # Usually in a section "決算発表予定日"
            # Attempt to find text "決算発表予定日"
            text_el = soup.find(string=re.compile("決算発表予定日"))
            if text_el:
                 # Usually the date is in the next span or parent's text
                 parent = text_el.parent
                 # Look for date pattern YYYY/MM/DD or YYYY/M/D
                 match = re.search(r'\d{4}/\d{1,2}/\d{1,2}', parent.parent.text)
                 if match:
                     data['earnings_date'] = match.group(0)

        # 2. Performance Page (Finance)
        # Let's fetch /performance for detailed table text
        res_perf = requests.get(f"{base_url}/performance", headers=headers, timeout=10)
        if res_perf.status_code == 200:
            soup_perf = BeautifulSoup(res_perf.text, 'html.parser')
            # Extract simple text from the performance table
            # Look for table rows
            rows = soup_perf.find_all('tr')
            perf_text_list = []
            for row in rows[:8]: # Limit to header + recent years
                cols = [c.text.strip() for c in row.find_all(['th', 'td'])]
                if cols:
                    perf_text_list.append(" | ".join(cols))
            
            data['finance'] = "\n".join(perf_text_list)
            
    except Exception as e:
        print(f"    Scraping Warning ({ticker}): {e}")
        
    return data

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
    print(f"[{datetime.now()}] Starting Ultimate Daily Analysis...")

    # 1. Macro Analysis
    print(">>> 1. Performing Global Macro Analysis...")
    macro_result = {}
    risk_events = []
    
    try:
        global_data = fetch_global_market_data()
        headlines = macro_analyzer.fetch_news_headlines()
        ai_response = macro_analyzer.analyze_sentiment(headlines, global_data)
        
        # New response structure: { "sector_scores": {...}, "reason_summary": "...", "risk_events": [...] }
        # Fallback for old format if AI hallucinates
        if "sector_scores" in ai_response:
            macro_result = ai_response["sector_scores"]
            summary = ai_response.get("reason_summary", "")
            risk_events = ai_response.get("risk_events", [])
        else:
            # Handle flat format (old style)
            macro_result = ai_response
            summary = ai_response.get("reason_summary", "")
            risk_events = [] # No events

        # Save to DB (daily_macro_log)
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        usd_jpy = global_data.get("USD/JPY", {}).get("price")
        sox = global_data.get("PHLX Semiconductor (SOX)", {}).get("price")
        nasdaq = global_data.get("NASDAQ Composite", {}).get("price")
        
        macro_record = {
            "date": today_str,
            "summary": summary,
            "sector_scores": macro_result,
            "risk_events": risk_events,
            "usd_jpy": usd_jpy,
            "sox_index": sox,
            "nasdaq_index": nasdaq
        }
        
        supabase.table("daily_macro_log").upsert(macro_record).execute()
        print(f"    Saved Macro Log (Events: {len(risk_events)}).")
        
    except Exception as e:
        print(f"!!! Error in Macro Analysis: {e}")
        # Continue with technical analysis
    
    # 2. Pre-fetch US Indices for Correlation Calculation (60 days)
    print(">>> 2. Pre-fetching US Indices for Correlation...")
    us_indices_hist = {}
    try:
        # Fetch longer history for correlation (90d to be safe for 60d rolling)
        us_tickers = ["^SOX", "^IXIC", "^GSPC"]
        us_data = yf.download(us_tickers, period="3mo", auto_adjust=True, threads=True)
        # Handle MultiIndex
        for ticker in us_tickers:
            if isinstance(us_data.columns, pd.MultiIndex):
                try:
                    us_indices_hist[ticker] = us_data.xs(ticker, axis=1, level=1)['Close']
                except:
                    # Alternative yfinance structure check
                     us_indices_hist[ticker] = us_data['Close'][ticker]
            else:
                 us_indices_hist[ticker] = us_data['Close'] # Single ticker case (unlikely here)
            
            # Fill NaN for alignment validity
            us_indices_hist[ticker] = us_indices_hist[ticker].fillna(method='ffill')
            
    except Exception as e:
        print(f"!!! Error fetching US indices history: {e}")

    # 3. Load Tickers
    print(">>> 3. Loading Tickers...")
    try:
        tickers_df = pd.read_csv("batch_jobs/data/prime_tickers.csv")
        tickers = tickers_df['ticker'].tolist()
        ticker_sector_map = dict(zip(tickers_df['ticker'], tickers_df['sector']))
        ticker_name_map = dict(zip(tickers_df['ticker'], tickers_df['name']))
        print(f"    Loaded {len(tickers)} tickers.")
    except FileNotFoundError:
        print("!!! prime_tickers.csv not found. Aborting.")
        return

    # 4. Bulk Analysis Loop
    print(">>> 4. Starting Bulk Analysis...")
    chunk_size = 50
    results_to_insert = []
    
    for i in range(0, len(tickers), chunk_size):
        chunk_tickers = tickers[i:i + chunk_size]
        print(f"    Processing chunk {i}-{i+len(chunk_tickers)}...")
        
        try:
            # Fetch for SMA75 (needs ~6mo)
            data = yf.download(chunk_tickers, period="6mo", group_by='ticker', auto_adjust=True, threads=True)
            
            for ticker in chunk_tickers:
                try:
                    # Extract DF
                    if len(chunk_tickers) == 1:
                        df = data
                    else:
                        if ticker not in data.columns.levels[0]: continue
                        df = data[ticker].copy() # Copy to avoid SettingWithCopy

                    if df.empty or len(df) < 75: continue
                    
                    # --- TECHNICAL CALCULATION ---
                    # 1. Basics
                    df['SMA5'] = df['Close'].rolling(window=5).mean()
                    df['SMA75'] = df['Close'].rolling(window=75).mean()
                    df['Vol_SMA5'] = df['Volume'].rolling(window=5).mean()
                    
                    # 2. Bollinger Bands (20, 2)
                    sma20 = df['Close'].rolling(window=20).mean()
                    std20 = df['Close'].rolling(window=20).std()
                    df['BB_Upper'] = sma20 + (2 * std20)
                    df['BB_Lower'] = sma20 - (2 * std20)
                    
                    # 3. RSI 14
                    delta = df['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    df['RSI'] = 100 - (100 / (1 + rs))
                    
                    # 4. ATR 14
                    high_low = df['High'] - df['Low']
                    high_close = np.abs(df['High'] - df['Close'].shift())
                    low_close = np.abs(df['Low'] - df['Close'].shift())
                    ranges = pd.concat([high_low, high_close, low_close], axis=1)
                    true_range = np.max(ranges, axis=1)
                    df['ATR'] = pd.Series(true_range).rolling(window=14).mean()
                    
                    # 5. MACD (12, 26, 9)
                    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
                    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
                    df['MACD'] = exp1 - exp2
                    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
                    df['MACD_Hist'] = df['MACD'] - df['Signal_Line']

                    # Latest Data
                    row = df.iloc[-1]
                    prev_row = df.iloc[-2]
                    
                    # Clean NaNs
                    if pd.isna(row['SMA75']) or pd.isna(row['RSI']): continue
                    
                    close = row['Close']
                    opn = row['Open']
                    volume = row['Volume']
                    rsi = row['RSI']
                    atr = row['ATR'] if not pd.isna(row['ATR']) else 0
                    bb_upper = row['BB_Upper']
                    sma5 = row['SMA5']
                    vol_sma5 = row['Vol_SMA5']
                    macd_hist = row['MACD_Hist']
                    prev_hist = prev_row['MACD_Hist']
                    
                    # --- CORRELATION CALCULATION ---
                    # Determine Parent Index
                    english_sector = ticker_sector_map.get(ticker, "")
                    # CSV Name is now assigned to name_en
                    name_en = ticker_name_map.get(ticker, "")
                    name_jp = None
                    
                    parent_index_ticker = "^GSPC" # Default S&P500
                    if english_sector in ["Electric Appliances", "Precision Instruments"]:
                        parent_index_ticker = "^SOX" # Semi/Tech
                    elif english_sector in ["Information & Communication", "Services"]:
                        parent_index_ticker = "^IXIC" # Nasdaq
                        
                    correlation_us = 0.0
                    if parent_index_ticker in us_indices_hist:
                        # Align dates
                        us_series = us_indices_hist[parent_index_ticker]
                        
                        # Get last 60 days overlapping data
                        # Align index
                        aligned_data = pd.DataFrame({'stock': df['Close'], 'us': us_series}).dropna().tail(60)
                        
                        if len(aligned_data) > 30:
                            correlation_us = aligned_data['stock'].corr(aligned_data['us'])

                    # --- LOGIC & SCORING ---
                    
                    signal = "WAIT"
                    reason = []
                    
                    # Macro Score Integration
                    # Mapping English JPX to Japanese Categories (Simplified for brevity, assumed same logic as before)
                    sector_map = {
                        "Electric Appliances": "電気・精密", "Precision Instruments": "電気・精密",
                        "Transportation Equipment": "自動車・輸送機", "Banks": "銀行・金融",
                        "Information & Communication": "情報・通信", "Services": "小売・サービス",
                        "Wholesale Trade": "商社", "Retail Trade": "小売・サービス",
                        "Chemicals": "素材・化学", "Pharmaceutical": "医薬品",
                        "Foods": "食品", "Construction": "建設・不動産", "Real Estate": "建設・不動産"
                    } # Add full list if needed, using safe default
                    target_category = sector_map.get(english_sector, "全体")
                    macro_score = macro_result.get(target_category, macro_result.get("全体", 0))

                    # 1. AGGRESSIVE (Short-term Surge)
                    # RSI < 50 (Not Overheated yet), Close > SMA5, Volume surge, Positive Candle, Uptrending
                    if rsi < 60 and close > sma5 and volume > (vol_sma5 * 1.5) and close > opn:
                        # Specific check: SMA5 is pointing up?
                         if sma5 > prev_row['SMA5']:
                            signal = "AGGRESSIVE"
                            reason.append("Vol Surge & Short-term Uptrend")

                    # 2. BUY (S-Stock logic / Dip Buy)
                    # Condition: Trend is up (Close > SMA75), RSI sold off (<35), High Upside, Macro OK
                    elif close > row['SMA75']:
                        if rsi < 35:
                            if macro_score >= 0:
                                signal = "BUY"
                                reason.append("RSI Dip & Uptrend")
                            else:
                                # Macro risk suppress
                                pass
                    
                    # 3. Trend Strength Score (0-3) -> C-S
                    trend_score = 0
                    if macd_hist > 0 and macd_hist > prev_hist: trend_score += 1 # Accelerating
                    if close > bb_upper: trend_score += 1 # Band walk potentially (or just breakout)
                    if close > df['High'].iloc[-5:-1].max(): trend_score += 1 # New High in 5 days
                    
                    trend_rank_map = {0: "C", 1: "B", 2: "A", 3: "S"}
                    trend_strength = trend_rank_map.get(trend_score, "C")

                    # 4. Exit Guideline (Event Risk)
                    exit_guide = None
                    if signal in ["BUY", "AGGRESSIVE"]: 
                        # Check high correlation + upcoming event
                        if correlation_us > 0.6:
                             # Check if any high impact event is within 3 days
                            target_date_limit = (datetime.now() + pd.Timedelta(days=3)).strftime('%Y-%m-%d')
                            for event in risk_events:
                                     exit_guide = f"⚠️ {event.get('name')}直前。相関高({correlation_us:.2f})のため警戒"
                                     break

                    # --- Name Fetch (JP Strategy) & Deep Dive ---
                    # Strategy: If BUY or AGGRESSIVE, scrape Yahoo Finance for name_jp
                    # If AGGRESSIVE, also get profile/finance for AI summary
                    
                    perf_summary = None
                    earnings_date = None
                    
                    if signal in ["BUY", "AGGRESSIVE"]:
                        try:
                            # Scraping for Name (JP) and Data
                            y_data = get_yahoo_finance_data(ticker)
                            
                            # Populate name_jp
                            if y_data.get("name_jp"):
                                name_jp = y_data["name_jp"]
                                
                            # If AGGRESSIVE, do Deep Dive (AI)
                            if signal == "AGGRESSIVE":
                                print(f"    🕵️ Deep Analyzing {ticker} ({name_jp})...")
                                earnings_date = y_data.get("earnings_date")
                                
                                if y_data.get("profile"):
                                    perf_summary = macro_analyzer.analyze_individual_stock(
                                        ticker, 
                                        y_data["profile"], 
                                        y_data.get("finance", "")
                                    )
                                # Be polite
                                time.sleep(2)
                            else:
                                # For BUY, just sleep a bit less or same
                                time.sleep(1)
                                
                        except Exception as e:
                            print(f"    Data Fetch Failed for {ticker}: {e}")

                    # Upside calc
                    upside_ratio = (row['BB_Upper'] - close) / atr if atr > 0 else 0
                    
                    # Clean data for DB
                    if pd.isna(upside_ratio) or np.isinf(upside_ratio): upside_ratio = 0
                    if pd.isna(correlation_us) or np.isinf(correlation_us): correlation_us = 0
                    
                    results_to_insert.append({
                        "date": today_str,
                        "ticker": ticker,
                        "sector": english_sector,
                        "name_jp": name_jp,
                        "name_en": name_en,
                        "close_price": float(close),
                        "rsi_14": float(rsi),
                        "atr_14": float(atr),
                        "upside_ratio": float(upside_ratio),
                        "macro_score": int(macro_score),
                        "signal": signal,
                        "trend_strength": trend_strength,
                        "correlation_us": float(correlation_us),
                        "exit_guideline": exit_guide,
                        "performance_summary": perf_summary,
                        "earnings_release_date": earnings_date,
                        "reason": ", ".join(reason) if reason else None
                    })

                except Exception as e:
                    continue

        except Exception as e:
            print(f"!!! Error in Chunk {i}: {e}")

    # 5. DB Upsert
    print(f">>> 5. Saving {len(results_to_insert)} records to DB...")
    if results_to_insert:
        db_chunk_size = 500
        for i in range(0, len(results_to_insert), db_chunk_size):
            chunk = results_to_insert[i:i + db_chunk_size]
            try:
                supabase.table("market_analysis_log").upsert(chunk).execute()
                print(f"    Upserted batch {i}-{i+len(chunk)}")
            except Exception as e:
                print(f"!!! DB Error: {e}")

    print(f"[{datetime.now()}] Ultimate Analysis Complete.")

if __name__ == "__main__":
    asyncio.run(main())
