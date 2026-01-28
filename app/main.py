
from fastapi import FastAPI, BackgroundTasks
from app.config import config
from app.services import market_data, analysis, notifier
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
    results = []
    
    for ticker in config.TARGET_TICKERS:
        # 1. Fetch Data
        df = market_data.fetch_historical_data(ticker)
        if df.empty:
            continue
            
        # 2. Analyze
        rsi_series = analysis.calculate_rsi(df, period=config.RSI_PERIOD)
        if rsi_series.empty:
            continue
            
        current_rsi = rsi_series.iloc[-1]
        signal = analysis.judge_signal(current_rsi)
        current_price = df['Close'].iloc[-1]
        
        result = AnalysisResult(
            ticker=ticker,
            current_price=float(current_price),
            rsi=float(current_rsi),
            signal=signal,
            timestamp=df.index[-1]
        )
        results.append(result)

    # 3. Notify (only if there are results)
    if results:
        discord_content = notifier.format_discord_message(results)
        # Send notification in background to check pydantic/async compatibility
        # But notifier.send_notification is async, so we can await it or use background_tasks.
        # Since this endpoint is async, we can await it directly or use a background wrapper.
        # For simplicity and immediacy in this prototype, let's await it.
        # If latency becomes an issue, we can use background_tasks.add_task(notifier.send_notification, discord_content)
        # However, send_notification is async defined, so standard background_tasks might need a wrapper or run_in_executor if it was sync.
        # Since it is async def, background_tasks.add_task works fine with it in FastAPI.
        
        background_tasks.add_task(notifier.send_notification, discord_content)

    return {"status": "success", "analyzed_count": len(results)}
