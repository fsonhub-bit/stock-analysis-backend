import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    TARGET_TICKERS = ["7203.T", "9984.T", "8306.T"]
    
    # RSS Feeds for Market Sentiment
    RSS_FEEDS = [
        "https://feeds.reuters.com/reuters/JAPANTopNews", # Reuters Japan Top News
        "https://www3.nhk.or.jp/rss/news/cat0.xml",       # NHK Top News
        # Add more reliable feeds here
    ]
    
    # Ticker to Sector Mapping
    TICKER_SECTOR_MAP = {
        "7203.T": "自動車・輸送機",
        "8306.T": "銀行・金融",
        "9984.T": "通信・投資",
    }

    # Global Indicators
    GLOBAL_TICKERS = {
        "^GSPC": "S&P 500",
        "^IXIC": "NASDAQ Composite",
        "^SOX": "PHLX Semiconductor (SOX)", 
        "JPY=X": "USD/JPY"
    }
    GLOBAL_DATA_PERIOD = "5d"

    RSI_PERIOD = 14
    RSI_OVERBOUGHT = 70
    RSI_OVERSOLD = 30

config = Config()
