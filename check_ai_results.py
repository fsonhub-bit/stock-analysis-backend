
import os
import sys
from services.db_client import supabase
from datetime import datetime, timedelta

# Adjust path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def fetch_latest_aggressive_logs():
    try:
        # Get today or yesterday
        today = datetime.now()
        start_date = (today - timedelta(days=2)).strftime('%Y-%m-%d')
        
        print(f"Fetching logs since {start_date}...")
        
        res = supabase.table("market_analysis_log")\
            .select("date, ticker, name_jp, performance_summary, signal")\
            .eq("signal", "AGGRESSIVE")\
            .gte("date", start_date)\
            .order("date", desc=True)\
            .execute()
            
        if not res.data:
            print("No AGGRESSIVE logs found for recent dates.")
            return

        print(f"Found {len(res.data)} records.")
        for item in res.data:
            print("-" * 50)
            print(f"Date: {item['date']}")
            print(f"Ticker: {item['ticker']} ({item.get('name_jp')})")
            print(f"Summary: {item.get('performance_summary')}")
            print("-" * 50)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_latest_aggressive_logs()
