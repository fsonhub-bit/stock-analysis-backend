
from typing import List, Dict, Any
import httpx
from app.models import AnalysisResult
from app.config import config

def format_discord_message(results: List[AnalysisResult]) -> Dict[str, Any]:
    """
    Format analysis results into a Discord embed message with S-Stock details.
    """
    embeds = []
    
    for res in results:
        color = 0x808080 # Gray for WAIT
        title_prefix = ""
        
        if res.signal == "BUY":
            color = 0xE74C3C # Red
            title_prefix = "🚨 ALERT: "
        elif res.signal == "SELL":
            color = 0x2ECC71 # Green
        
        # Build description with S-Stock specific fields
        description = (
            f"**Price:** {res.current_price:,.1f}\n"
            f"**Analysis Reason:**\n{res.reason}\n\n"
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
