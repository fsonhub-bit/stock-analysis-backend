
import feedparser
from datetime import datetime, timedelta

def fetch_historical_headlines(target_date: datetime) -> str:
    """
    Fetch historical headlines using Google News RSS Search with date range.
    """
    try:
        next_day = target_date + timedelta(days=1)
        
        # Query: stock market news around target date
        # syntax: after:YYYY-MM-DD before:YYYY-MM-DD
        query = f"stock market after:{target_date.strftime('%Y-%m-%d')} before:{next_day.strftime('%Y-%m-%d')}"
        query_encoded = query.replace(" ", "+")
        
        url = f"https://news.google.com/rss/search?q={query_encoded}&ceid=US:en&hl=en-US&gl=US"
        print(f"    Fetching Historical RSS: {url}")
        
        feed = feedparser.parse(url)
        
        if not feed.entries:
            print("    No entries found in Google RSS.")
            return "No historical news found."
            
        headlines = []
        seen = set()
        
        for entry in feed.entries[:20]: # Top 20
            title = entry.title
            # Dedup
            if title in seen:
                continue
            seen.add(title)
            
            # Add date if available to help AI context
            published = entry.get('published', '')
            if published:
                # published is usually "Thu, 01 Feb 2024 ..."
                # Shorten it? AI can parse it.
                headlines.append(f"- [{published}] {title}")
            else:
                headlines.append(f"- {title}")
                
        return "\n".join(headlines)

    except Exception as e:
        print(f"    Error fetching historical RSS: {e}")
        return "Error fetching historical news."
