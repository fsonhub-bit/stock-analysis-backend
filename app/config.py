import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
    TARGET_TICKERS = ["7203.T", "9984.T", "8306.T"]
    RSI_PERIOD = 14
    RSI_OVERBOUGHT = 70
    RSI_OVERSOLD = 30

config = Config()
