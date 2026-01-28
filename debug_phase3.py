
import asyncio
from app.services.macro import macro_analyzer
from app.services import notifier

async def main():
    print("--- Starting Phase 3 Macro Verification ---")
    
    # 1. Fetch Headlines
    print("Fetching Headlines...")
    headlines = macro_analyzer.fetch_news_headlines()
    if not headlines:
        print("Warning: No headlines fetched. Check RSS connection.")
    else:
        print(f"Headlines fetched (first 100 chars):\n{headlines[:100]}...")

    # 2. Analyze
    print("\nAnalyzing Sentiment via Gemini...")
    sentiment = macro_analyzer.analyze_sentiment(headlines)
    print("\n--- Sentiment Result ---")
    print(sentiment)

    # 3. Simulate Notification
    print("\n--- Notification Payload Check ---")
    # Dummy mock for AnalysisResult isn't critical here since we test macro part
    payload = notifier.format_discord_message([], macro_sentiment=sentiment)
    print(payload)

if __name__ == "__main__":
    asyncio.run(main())
