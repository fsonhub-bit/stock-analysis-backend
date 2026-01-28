
from typing import List, Dict, Any
import httpx
from app.models import AnalysisResult
from app.config import config

def format_discord_message(results: List[AnalysisResult], macro_sentiment: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Format analysis results into a Discord embed message with S-Stock details and Macro Sentiment.
    """
    embeds = []
    
    # 0. Macro Sentiment Embed (First)
    if macro_sentiment:
        reason = macro_sentiment.get("reason_summary", "")
        # Filter only integer scores for display
        scores = {k: v for k, v in macro_sentiment.items() if isinstance(v, int)}
        
        score_text = ""
        for k, v in scores.items():
            sign = "+" if v > 0 else ""
            score_text += f"**{k}**: {sign}{v}\n"
            
        macro_embed = {
            "title": "🌍 AI Market Sentiment Analysis",
            "description": f"{reason}\n\n{score_text}",
            "color": 0x3498DB # Blue
        }
        embeds.append(macro_embed)
    
    # 1. Individual Ticker Embeds
    for res in results:
        color = 0x808080 # Gray for WAIT
        title_prefix = ""
        
        if res.signal == "BUY":
            color = 0xE74C3C # Red
            title_prefix = "🚨 ALERT: "
        elif res.signal == "SELL":
            color = 0x2ECC71 # Green
        
        # Get sector sentiment if available
        sector = config.TICKER_SECTOR_MAP.get(res.ticker, "Unknown")
        sector_score = 0
        if macro_sentiment:
            sector_score = macro_sentiment.get(sector, macro_sentiment.get("全体", 0))
        
        sector_info = f"Sector ({sector}): {'+' if sector_score > 0 else ''}{sector_score}"
        
        # Build description with S-Stock specific fields
        description = (
            f"**Price:** {res.current_price:,.1f}\n"
            f"**Analysis Reason:**\n{res.reason}\n\n"
            f"**Macro Context:** {sector_info}\n"
            f"**Technical Indicators:**\n"
            f"- RSI: {res.rsi:.1f}\n"
            f"- ATR (14): {res.atr:.1f}\n"
            f"- Target Price (+2σ): {res.target_price:,.1f}\n"
            f"- Upside: {res.upside_ratio:.1f}x ATR"
        )

        embed = {
            "title": f"{title_prefix}{res.ticker} Signal: {res.signal}",
            "description": description,
            "color": color,
            "footer": {"text": f"Time: {res.timestamp.strftime('%Y-%m-%d %H:%M')}"}
        }
        embeds.append(embed)

    return {
        "content": f"S-Stock Analysis Report ({len(results)} items)",
        "embeds": embeds
    }

async def send_notification(content: Dict[str, Any]):
    """
    Send notification to Discord webhook.
    """
    webhook_url = config.DISCORD_WEBHOOK_URL
    if not webhook_url:
        print("Discord Webhook URL not set.")
        return

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(webhook_url, json=content)
            response.raise_for_status()
            print("Notification sent successfully.")
        except httpx.HTTPError as e:
            print(f"Failed to send notification: {e}")
