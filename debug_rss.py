
import feedparser
from app.config import config
import datetime

def debug_rss():
    print(f"Current System Time: {datetime.datetime.now()}")
    print("Checking Configured RSS Feeds...")
    
    for url in config.RSS_FEEDS:
        print(f"\nScanning: {url}")
        try:
            feed = feedparser.parse(url)
            print(f"  Status: {feed.get('status', 'Unknown')}")
            print(f"  Entries Found: {len(feed.entries)}")
            
            if feed.entries:
                print("  Top 3 Headlines:")
                for entry in feed.entries[:3]:
                    published = entry.get('published', entry.get('updated', 'No Date'))
                    print(f"    - [{published}] {entry.title}")
            else:
                print("  !!! NO ENTRIES FOUND !!!")
                
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    debug_rss()
