
from fastapi import FastAPI, BackgroundTasks
from app.config import config
from app.services import market_data, analysis, notifier
from app.services.macro import macro_analyzer
from app.models import AnalysisResult

app = FastAPI(title="S-Stock Analysis Backend")

@app.get("/")
def read_root():
    return {"message": "S-Stock Analysis Backend is running"}

@app.post("/api/analyze")
async def analyze_s_stocks(background_tasks: BackgroundTasks):
    """
    Trigger stock analysis and notification.
    """
    # 0. Macro Analysis
    print("Fetching Macro Data...")
    headlines = macro_analyzer.fetch_news_headlines()
    macro_sentiment = macro_analyzer.analyze_sentiment(headlines)
    print(f"Macro Sentiment: {macro_sentiment}")

    results = []
    
    for ticker in config.TARGET_TICKERS:
        # 1. Fetch Data
        df = market_data.fetch_historical_data(ticker)
        if df.empty:
            continue
            
        # 2. Analyze (Integrated Logic)
        result = analysis.analyze_ticker(ticker, df)
        results.append(result)

    # 3. Notify (only if there are results)
    if results:
        discord_content = notifier.format_discord_message(results, macro_sentiment)
        background_tasks.add_task(notifier.send_notification, discord_content)

    # Format Response
    macro_response = {}
    if macro_sentiment:
        summary = macro_sentiment.get("reason_summary", "")
        sectors = {k: v for k, v in macro_sentiment.items() if k != "reason_summary"}
        macro_response = {
            "summary": summary,
            "sectors": sectors
        }

    return {
        "status": "success",
        "macro": macro_response,
        "stocks": results
    }
