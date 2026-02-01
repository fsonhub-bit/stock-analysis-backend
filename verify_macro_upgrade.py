
import sys
import os
import asyncio
# Add root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.macro import macro_analyzer
from services.market_data import fetch_global_market_data

def test_macro_upgrade():
    print(">>> 1. Fetching Global Market Data (New Monitor)...")
    try:
        global_data = fetch_global_market_data()
        market_text_lines = []
        for name, data in global_data.items():
            price = data.get("price")
            change = data.get("change_pct")
            line = f"- {name}: {price:,.2f} (Change: {change:+.2f}%)"
            market_text_lines.append(line)
            print(f"    {line}")
        market_text = "\n".join(market_text_lines)
    except Exception as e:
        print(f"❌ Error fetching market data: {e}")
        return

    print("\n>>> 2. Fetching English Headlines...")
    try:
        headlines = macro_analyzer.fetch_news_headlines()
        print(headlines)
    except Exception as e:
        print(f"❌ Error fetching headlines: {e}")
        return

    print("\n>>> 3. Running Gemma 3 Analysis (English Input -> JP Output)...")
    try:
        result = macro_analyzer.analyze_macro_market(market_text, headlines)
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if "market_mood" in result and "sector_scores" in result:
            print("\n✅ Verification Success: Structure matches requirements.")
        else:
             print("\n⚠️ Verification Warning: Missing keys.")
             
    except Exception as e:
        print(f"❌ Error in analysis: {e}")

if __name__ == "__main__":
    test_macro_upgrade()
