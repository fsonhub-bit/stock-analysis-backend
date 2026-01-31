
import feedparser
import google.generativeai as genai
import json
import os
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
        Analyze macro market conditions (Sector Scores & Risk Events).
        """
        if not self.model:
            return {}

        # Define broad sectors for comprehensive analysis
        sectors = [
            "自動車・輸送機", "電気・精密", "銀行・金融", "機械・鉄鋼", 
            "素材・化学", "医薬品", "情報・通信", "エネルギー", 
            "建設・不動産", "食品", "小売・サービス", "商社", "インフラ・運輸"
        ]
        sectors_str = ", ".join(sectors)
        
        from datetime import datetime
        
        prompt = f"""
あなたはプロの証券アナリストです。
本日は **{datetime.now().strftime('%Y/%m/%d')}** です。

以下の情報を元に、日本株市場の分析を行ってください。

### 役割
- 今日の市場センチメントをセクター別に評価する。
- 向こう2週間以内の重要経済イベントを抽出する。

### 入力情報
【米国市場・為替】
{global_text}

【国内主要ニュース】
{headlines}

### 出力フォーマット (JSON)
{{
    "sector_scores": {{
        "自動車・輸送機": 0,
        "半導体・ハイテク": 0,
        "全体": 0
    }},
    "reason_summary": "50文字以内の市場概況サマリ",
    "risk_events": [
        {{"name": "イベント名", "date": "YYYY-MM-DD", "impact": "High/Medium"}}
    ]
}}

### 制約事項
- `sector_scores` は -5(超悲観)〜+5(超楽観) でつけること。
- `risk_events` は入力情報または一般的な経済カレンダー知識から補完すること。
- 必ず有効なJSONのみを出力すること。Markdownのコードブロックは不要。
"""
        
        try:
            response = self.model.generate_content(prompt)
            # Clean response text to ensure JSON
            text = response.text.strip()
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "")
            if text.startswith("```"): # Handle case where language isn't specified
                text = text.replace("```", "")
            
            result = json.loads(text)
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
