
import feedparser
import google.generativeai as genai
import json
import os
from typing import Dict, Any

from app.config import config

class MacroAnalyzer:
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-flash-latest")
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

    def analyze_sentiment(self, headlines: str) -> Dict[str, Any]:
        """
        Analyze sentiment for sectors based on headlines using Gemini.
        Returns a dictionary like {"自動車": -2, "半導体": +4, "全体": +1, "reason": "..."}
        """
        if not self.model or not headlines:
            print("Gemini API Key missing or no headlines.")
            return {"全体": 0, "reason": "API Key未設定またはニュース取得失敗"}

        sectors = list(set(config.TICKER_SECTOR_MAP.values()))
        sectors_str = ", ".join(sectors)
        
        prompt = f"""
        あなたはプロの株式ストラテジストです。
        以下の最新ニュース見出しを分析し、以下のセクターおよび市場全体に対する投資家のセンチメントを -5(非常に悲観) 〜 +5(非常に楽観) の整数で採点してください。
        
        対象セクター: [{sectors_str}, 全体]
        
        ニュース:
        {headlines}
        
        出力フォーマット(JSONのみ):
        {{
            "自動車・輸送機": 0,
            "銀行・金融": 0,
            "通信・投資": 0,
            "全体": 0,
            "reason_summary": "市場全体の雰囲気を表す短い要約コメント(50文字以内)"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Clean response text to ensure JSON
            text = response.text.strip()
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "")
            
            result = json.loads(text)
            return result
        except Exception as e:
            print(f"Gemini Analysis Error: {e}")
            return {"全体": 0, "reason_summary": "AI分析エラー"}

macro_analyzer = MacroAnalyzer()
