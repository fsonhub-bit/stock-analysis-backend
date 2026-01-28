
import asyncio
from app.services.macro import macro_analyzer
from app.services import market_data
import json

async def main():
    print("--- Starting Phase 4 Global Macro Verification ---")
    
    # 1. Fetch Global Data
    print("\nFetching Global Market Data (S&P500, SOX, USD/JPY)...")
    global_data = market_data.fetch_global_market_data()
    print("Global Data Result:")
    print(json.dumps(global_data, indent=2, ensure_ascii=False))
    
    # 2. Fetch Headlines
    print("\nFetching Headlines...")
    headlines = macro_analyzer.fetch_news_headlines()
    if not headlines:
        print("Warning: No headlines fetched.")
    else:
        print(f"Headlines fetched (count lines: {len(headlines.splitlines())})")

    # 3. Analyze Weighted Sentiment
    print("\nAnalyzing Weighted Sentiment via Gemini...")
    sentiment = macro_analyzer.analyze_sentiment(headlines, global_data)
    print("\n--- Weighted Sentiment Result ---")
    print(json.dumps(sentiment, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
