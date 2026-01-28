
import asyncio
import pandas as pd
from app.services import market_data, analysis, notifier
from app.config import config

async def main():
    print("--- Starting Phase 2 Logic Verification ---")
    ticker = config.TARGET_TICKERS[0]
    print(f"Testing with ticker: {ticker}")

    # 1. Fetch Data
    print("Fetching data (6mo)...")
    df = market_data.fetch_historical_data(ticker, period="6mo")
    
    if df.empty:
        print("Error: No data fetched.")
        return
        
    print(f"Fetched {len(df)} rows. Columns: {df.columns.tolist()}")

    # 2. Analyze
    print("Running analysis...")
    result = analysis.analyze_ticker(ticker, df)
    
    print("\n--- Analysis Result ---")
    print(f"Ticker: {result.ticker}")
    print(f"Price: {result.current_price}")
    print(f"RSI: {result.rsi}")
    print(f"ATR: {result.atr}")
    print(f"SMA75: {df.iloc[-1].get('SMA75', 'N/A')}")
    print(f"BB_Upper: {result.target_price}")
    print(f"Signal: {result.signal}")
    print(f"Reason: {result.reason}")

    # 3. Notify (Simulated)
    print("\n--- Notification Payload ---")
    payload = notifier.format_discord_message([result])
    print(payload)
    
    # Uncomment to send real notification
    # print("\nSending real notification...")
    # await notifier.send_notification(payload)

if __name__ == "__main__":
    asyncio.run(main())
