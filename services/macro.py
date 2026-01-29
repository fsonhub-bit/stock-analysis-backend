
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

    def analyze_sentiment(self, headlines: str, global_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze sentiment for sectors based on headlines and global market data using Gemini.
        Returns a dictionary like {"自動車": -2, "半導体": +4, "全体": +1, "reason": "..."}
        """
        if not self.model:
            print("Gemini API Key missing.")
            return {"全体": 0, "reason_summary": "API Key未設定"}

        # Format global data
        global_text = "\n".join([
            f"- {name}: {d['price']:.2f} (前日比 {d['change_pct']:.2f}%)"
            for name, d in global_data.items()
        ])

        # Define broad sectors for comprehensive analysis
        sectors = [
            "自動車・輸送機", "電気・精密", "銀行・金融", "機械・鉄鋼", 
            "素材・化学", "医薬品", "情報・通信", "エネルギー", 
            "建設・不動産", "食品", "小売・サービス", "商社", "インフラ・運輸"
        ]
        sectors_str = ", ".join(sectors)
        
        prompt = f"""
        あなたは百戦錬磨の日本株ストラテジストです。以下の情報を元に、
        「今日の日本株市場における各セクターのセンチメント」を -5(超悲観)〜+5(超楽観) で判定してください。

        【重要：判断の重み付け】
        1. **米国株・為替動向 (Weight: 70%)**: 日本株は米国市場と為替に強く連動します。
           - SOX指数が上昇 → 日本の半導体セクターは「買い (+3以上)」
           - NASDAQが上昇 → 日本のハイテク・グロースは「買い」
           - ドル円が円安(数値上昇) → 輸出関連(自動車など)は「買い」、円高なら「売り」
        2. **国内ニュース (Weight: 30%)**: 個別の好悪材料を加味してください。

        【入力データ】
        == 米国市場・為替 (最重要) ==
        {global_text}

        == 国内主要ニュース ==
        {headlines}

        【出力フォーマット】
        JSON形式で出力してください。理由は簡潔に。「全体」は市場全体の地合いです。
        対象セクター: [{sectors_str}, 全体]
        
        Example JSON:
        {{
            "自動車・輸送機": 3,
            "半導体・ハイテク": -2,
            "銀行・金融": 0,
            "全体": 1,
            "reason_summary": "SOX指数の急落を受け半導体は厳しいが、円安進行により自動車は堅調。(50文字以内)"
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
