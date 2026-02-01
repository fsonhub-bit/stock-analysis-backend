import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    TARGET_TICKERS = ["7203.T", "9984.T", "8306.T"]
    
    # RSS Feeds (English Sources for Speed & Accuracy)
    RSS_FEEDS = [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114", # CNBC Top News
        "https://www.investing.com/rss/news.rss",       # Investing.com Headlines
        "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en" # Google News Business (US)
    ]
    
    # Ticker to Sector Mapping
    TICKER_SECTOR_MAP = {
        "7203.T": "自動車・輸送機",
        "8306.T": "銀行・金融",
        "9984.T": "通信・投資",
    }

    # Global The Macro Monitor Tickeres
    # Keys are Yahoo Finance Symbols, Values are display names/labels for AI
    GLOBAL_TICKERS = {
        # A. Major Indices
        "^GSPC": "S&P500",
        "^NDX": "NASDAQ100",
        "^RUT": "Russell2000(SmallCap)",
        
        # B. Rates & Bonds
        "^TNX": "US10Y_Yield",
        "^IRX": "US02Y_Yield",
        
        # C. Risk & Sentiment
        "^VIX": "VIX(Fear_Index)",
        "HYG":  "HYG(High_Yield_Bond_Risk_Appetite)",
        
        # D. Commodities & FX
        "CL=F":     "Crude_Oil_WTI",
        "GC=F":     "Gold",
        "DX-Y.NYB": "DXY(Dollar_Index)",
        "BTC-USD":  "Bitcoin",
        "JPY=X":    "USD/JPY",
        
        # E. Sector Indices (Leading Indicators for JP Sectors)
        "SOXX": "SOXX(Semiconductor)",
        "XLF":  "XLF(US_Financials)",
        "XLE":  "XLE(US_Energy)"
    }
    GLOBAL_DATA_PERIOD = "5d"

    RSI_PERIOD = 14
    RSI_OVERBOUGHT = 70
    RSI_OVERSOLD = 30

config = Config()
