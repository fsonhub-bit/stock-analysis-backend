
from typing import List, Dict, Any
import httpx
from app.models import AnalysisResult
from app.config import config

def format_discord_message(results: List[AnalysisResult]) -> Dict[str, Any]:
    """
    Format analysis results into a Discord embed message.
    """
    embeds = []
    
    for res in results:
        color = 0x808080 # Gray for WAIT
        title_prefix = ""
        
        if res.signal == "BUY":
            color = 0xFF0000 # Red (often associated with 'hot' or 'action' in trading contexts, or Green? 
            # In Japanese context, Red often means price up/gain, Green means down. 
            # But for "Signal", usually Red/Green is standard.
            # Let's use Red for BUY as requested "Red text or bold for BUY signal" in prompt.
            color = 0xE74C3C # Red
            title_prefix = "🚨 ALERT: "
        elif res.signal == "SELL":
            color = 0x2ECC71 # Green
        
        embed = {
            "title": f"{title_prefix}{res.ticker} Signal: {res.signal}",
            "color": color,
            "fields": [
                {"name": "Price", "value": f"{res.current_price:,.1f}", "inline": True},
                {"name": "RSI", "value": f"{res.rsi:.2f}", "inline": True},
                {"name": "Time", "value": res.timestamp.strftime("%Y-%m-%d"), "inline": True}
            ]
        }
        embeds.append(embed)

    return {
        "content": f"Stock Analysis Report ({len(results)} items)",
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
