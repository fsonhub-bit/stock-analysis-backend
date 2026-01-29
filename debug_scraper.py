
import requests
from bs4 import BeautifulSoup
import re
import json

def get_yahoo_finance_data(ticker):
    """
    Scrape Profile, Earnings Date, and Finance Highlights from Yahoo! Finance Japan.
    (Debug version with logging)
    """
    code = ticker.split('.')[0]
    base_url = f"https://finance.yahoo.co.jp/quote/{code}"
    
    data = {"profile": "", "finance": "", "earnings_date": ""}
    print(f"Testing URL: {base_url}")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        
        # 1. Main Page
        res = requests.get(base_url, headers=headers, timeout=10)
        print(f"Status Code: {res.status_code}")
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Profile
            profile_el = soup.find('p', class_='_6YdC6U3')
            if profile_el:
                print("Found profile by class")
                data['profile'] = profile_el.text.strip()
            else:
                print("Profile class not found, trying meta description")
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc:
                    print("Found meta description")
                    data['profile'] = meta_desc.get('content', '')
            
            # Earnings Date
            text_el = soup.find(string=re.compile("決算発表予定日"))
            if text_el:
                print("Found '決算発表予定日' string")
                try:
                    # Depending on structure, might be parent or grandparent
                    # Debugging structure
                    parent = text_el.parent
                    grandparent = parent.parent
                    print(f"Context text: {grandparent.text[:100]}")
                    
                    match = re.search(r'\d{4}/\d{2}/\d{2}', grandparent.text)
                    if match:
                        data['earnings_date'] = match.group(0)
                        print(f"Extracted date: {match.group(0)}")
                    else:
                        print("Date regex match failed")
                except Exception as e:
                    print(f"Error parse date: {e}")
            else:
                print("'決算発表予定日' not found")

        # 2. Performance Page
        perf_url = f"{base_url}/performance"
        print(f"Testing Performance URL: {perf_url}")
        res_perf = requests.get(perf_url, headers=headers, timeout=10)
        if res_perf.status_code == 200:
            soup_perf = BeautifulSoup(res_perf.text, 'html.parser')
            rows = soup_perf.find_all('tr')
            print(f"Found {len(rows)} rows in performance table")
            perf_text_list = []
            for row in rows[:5]:
                cols = [c.text.strip() for c in row.find_all(['th', 'td'])]
                if cols:
                    perf_text_list.append(" | ".join(cols))
            data['finance'] = "\n".join(perf_text_list)

    except Exception as e:
        print(f"Scraping Error: {e}")
        
    return data

if __name__ == "__main__":
    # Test with Softbank and SourceNext (Aggressive)
    tickers = ["9984.T", "4344.T"]
    for t in tickers:
        print(f"\n--- {t} ---")
        result = get_yahoo_finance_data(t)
        print(json.dumps(result, indent=2, ensure_ascii=False))
