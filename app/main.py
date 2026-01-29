
from fastapi import FastAPI, HTTPException, Query
from services.db_client import supabase
from datetime import date
from typing import Optional

app = FastAPI(title="S-Stock AI Analyst API")

@app.get("/")
def read_root():
    return {"message": "S-Stock AI Analyst API (Read-Only) is running"}

@app.get("/api/stocks/recommendations")
def get_recommendations(
    target_date: Optional[str] = None
):
    """
    Get recommended stocks (BUY signal) for a specific date (default: today).
    """
    if not target_date:
        target_date = date.today().isoformat()
        
    try:
        response = supabase.table("market_analysis_log") \
            .select("*") \
            .eq("date", target_date) \
            .eq("signal", "BUY") \
            .order("upside_ratio", desc=True) \
            .execute()
            
        return {"data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stocks/{ticker}/history")
def get_stock_history(ticker: str):
    """
    Get analysis history for a specific ticker.
    """
    try:
        response = supabase.table("market_analysis_log") \
            .select("date, close_price, rsi_14, signal, upside_ratio") \
            .eq("ticker", ticker) \
            .order("date", desc=False) \
            .execute()
            
        return {"data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/macro/latest")
def get_latest_macro():
    """
    Get the latest macro environment analysis.
    """
    try:
        target_date = date.today().isoformat()
        response = supabase.table("daily_macro_log") \
            .select("*") \
            .eq("date", target_date) \
            .execute()
            
        if not response.data:
            # Fallback to mostly recent if today not done yet?
            response = supabase.table("daily_macro_log") \
                .select("*") \
                .order("date", desc=True) \
                .limit(1) \
                .execute()
                
        return {"data": response.data[0] if response.data else None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
