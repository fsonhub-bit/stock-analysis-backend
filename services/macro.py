
import feedparser
import google.generativeai as genai
import json
import os
import re
from typing import Dict, Any

from app.config import config

class MacroAnalyzer:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Switch to Gemma 3 27B IT
            self.model = genai.GenerativeModel(
                model_name="gemma-3-27b-it",
                generation_config={
                    "temperature": 0.2,       # Low temp for factual accuracy
                    "max_output_tokens": 250, # Slightly higher to allow full Japanese formation
                }
            )
        else:
            self.model = None

    def fetch_news_headlines(self) -> str:
        """
        Fetch top news headlines from configured RSS feeds.
        """
        headlines = []
        for url in config.RSS_FEEDS:
            try:
                feed = feedparser.parse(url)
                # Take top 5 entries from each feed
                for entry in feed.entries[:5]:
                    headlines.append(f"- {entry.title}")
            except Exception as e:
                print(f"Error fetching RSS {url}: {e}")
        
        return "\n".join(headlines)

    def analyze_macro_market(self, global_text: str, headlines: str) -> dict:
        """
        Analyze macro market conditions (Sector Scores & Risk Events) using new Pro-Grade Logic.
        """
        if not self.model:
            return {}

        prompt = f"""
You are a top-tier hedge fund manager. 
Analyze the following "Market Data" and "News Headlines" to determine the sentiment for Japanese stock sectors.

### Market Data
{global_text}

### News Headlines
{headlines}

### Task
1. Analyze the Risk Appetite (Risk-On or Risk-Off?) based on VIX, HYG, and Yields.
2. Determine sentiment scores (-5 to +5) for Japanese sectors.
   (e.g., If SOXX is up, '電気・精密' (Electric/Precision) should be positive. If Oil/XLE is up, '商社' (Trading) is positive.)
3. Extract key risk events.

### Output Format (JSON)
Return a valid JSON object. Do not include any explanations or markdown ticks (```json) outside the JSON.
{{
    "market_mood": "Risk-On" or "Risk-Off" or "Neutral",
    "summary": "Short summary of the global market situation in Japanese (日本語).",
    "sector_scores": {{
        "自動車・輸送機": 0,
        "電気・精密": 0,
        "銀行・金融": 0, 
        "機械・鉄鋼": 0,
        "素材・化学": 0, 
        "医薬品": 0, 
        "情報・通信": 0, 
        "エネルギー": 0, 
        "建設・不動産": 0, 
        "食品": 0, 
        "小売・サービス": 0, 
        "商社": 0, 
        "インフラ・運輸": 0,
        "全体": 0
    }},
    "reason_summary": "Same as 'summary' field above",
    "risk_events": [
         {{"name": "Event Name", "date": "YYYY-MM-DD", "impact": "High/Medium"}}
    ]
}}
"""
        
        try:

            # Increase output limit for Macro Analysis (needs more tokens for full JSON)
            # 2000 tokens to ensure no truncation
            response = self.model.generate_content(
                prompt,
                generation_config={"max_output_tokens": 2000, "temperature": 0.2}
            )
            
            # Robust JSON extraction
            # Try to find the first '{' and last '}'
            raw_text = response.text
            start = raw_text.find('{')
            end = raw_text.rfind('}')
            
            if start != -1 and end != -1:
                text = raw_text[start:end+1]
            else:
                text = raw_text.strip()
            
            # Simple cleanup for common trailing comma issues
            text = re.sub(r",\s*([\]}])", r"\1", text)
            
            result = json.loads(text)
            
            # Ensure compatibility
            if "reason_summary" not in result and "summary" in result:
                result["reason_summary"] = result["summary"]
                
            return result
        except Exception as e:
            print(f"Gemini Analysis Error: {e}")
            return {"全体": 0, "reason_summary": "AI分析エラー"}

    def analyze_individual_stock(self, ticker: str, profile: str, finance_text: str) -> str:
        """
        Analyze individual stock performance based on profile and financial data.
        Returns a roughly 150-character summary.
        """
        if not self.model:
            return "AI機能が無効です。"

        from datetime import datetime
        today_str = datetime.now().strftime('%Y/%m/%d')

        prompt = f"""
あなたはプロの証券アナリストです。
以下の【企業の特色】と【直近の業績推移】データを分析し、投資家向けの短い要約を作成してください。

### 制約事項
1. **日本語**で記述すること。
2. **150文字以内**で簡潔にまとめること。
3. 主観的な挨拶（「はい、分かりました」等）は**一切不要**。分析結果のみを出力すること。
4. 以下の順序で構成すること:
   - 企業の強みや事業内容（簡潔に）
   - 直近の業績トレンド（増収増益/減収減益など）
   - 利益率や成長性への評価

### 入力データ
【日付】
{today_str}

【銘柄】
{ticker}

【企業の特色】
{profile}

【業績推移データ】
{finance_text}

### 出力
"""
        
        import time
        import re
        from google.api_core import exceptions

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                error_str = str(e)
                # Handle standard 429
                if "429" in error_str or "Quota exceeded" in error_str or "ResourceExhausted" in error_str:
                    print(f"Gemma 429 Exceeded (Attempt {attempt+1}/{max_retries}). Waiting...")
                    
                    delay = 10 * (attempt + 1) # Simple backoff
                    
                    if attempt < max_retries - 1:
                        print(f"    Sleeping for {delay:.2f}s before retry.")
                        time.sleep(delay)
                        continue
                
                print(f"Gemma Analysis Error ({ticker}): {e}")
                return "AI分析エラー: 通信または生成エラー"

macro_analyzer = MacroAnalyzer()
