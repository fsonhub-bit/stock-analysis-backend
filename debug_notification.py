
import asyncio
import os
from app.config import config
from app.services import notifier
from app.models import AnalysisResult
from datetime import datetime

async def main():
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"Loading Config...")
    webhook_url = config.DISCORD_WEBHOOK_URL
    
    if not webhook_url:
        print("ERROR: DISCORD_WEBHOOK_URL is empty! Please check your .env file.")
        return
    
    print(f"Webhook URL found: {webhook_url[:10]}...{webhook_url[-5:]}")
    
    print("Creating dummy analysis result...")
    dummy_results = [
        AnalysisResult(
            ticker="TEST.T",
            current_price=1000.0,
            rsi=25.0,
            signal="BUY",
            timestamp=datetime.now()
        )
    ]
    
    print("Formatting message...")
    content = notifier.format_discord_message(dummy_results)
    print(f"Message content: {content}")
    
    print("Sending notification...")
    await notifier.send_notification(content)
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
