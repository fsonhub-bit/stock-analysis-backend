
from fastapi import FastAPI, HTTPException, Query
from services.db_client import supabase
from datetime import date
from typing import Optional

app = FastAPI(title="S-Stock AI Analyst API")

@app.get("/")
def read_root():
    return {"message": "S-Stock AI Analyst API (Read-Only) is running"}

@app.get("/api/recommendations")
async def get_recommendations():
    try:
        # 最新の日付を取得
        latest_date_res = supabase.table("market_analysis_log").select("date").order("date", desc=True).limit(1).execute()
        if not latest_date_res.data:
            return {"status": "no_data", "stocks": []}
        
        target_date = latest_date_res.data[0]["date"]
        
        # BUY or AGGRESSIVE シグナルを取得
        # signal in ("BUY", "AGGRESSIVE")
        res = supabase.table("market_analysis_log")\
            .select("*")\
            .eq("date", target_date)\
            .in_("signal", ["BUY", "AGGRESSIVE"])\
            .order("trend_strength", desc=True)\
            .order("upside_ratio", desc=True)\
            .execute()
            
        return {"status": "success", "date": target_date, "stocks": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/latest")
async def get_latest_analysis(mode: str = "all"):
    """
    Get the latest analysis data.
    - mode="recommend": Returns only BUY/AGGRESSIVE signals (Lightweight)
    - mode="all": Returns all stocks (Heavy)
    """
    try:
        # Get latest date
        latest_date_res = supabase.table("market_analysis_log").select("date").order("date", desc=True).limit(1).execute()
        if not latest_date_res.data:
            return {"status": "no_data", "stocks": []}
        
        target_date = latest_date_res.data[0]["date"]
        
        query = supabase.table("market_analysis_log").select("*").eq("date", target_date)
        
        # Mode-based filtering
        if mode == "recommend":
            query = query.in_("signal", ["BUY", "AGGRESSIVE"])
            # Add ordering for recommendation view
            query = query.order("trend_strength", desc=True).order("upside_ratio", desc=True)
        else:
            # For "all", maybe order by sector or ticker?
            query = query.order("ticker", desc=False)
            
        res = query.execute()
            
        return {"status": "success", "date": target_date, "mode": mode, "count": len(res.data), "stocks": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/{ticker}")
async def get_stock_history(ticker: str):
    try:
        # 指定銘柄の全履歴（または直近90件）を取得
        res = supabase.table("market_analysis_log")\
            .select("*")\
            .eq("ticker", ticker)\
            .order("date", desc=False)\
            .limit(90)\
            .execute()
            
        return {"status": "success", "ticker": ticker, "history": res.data}
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
