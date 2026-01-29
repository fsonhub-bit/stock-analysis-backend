
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import io

def fetch_prime_tickers():
    # URL of "Others Statistics" page which links to the file
    base_url = "https://www.jpx.co.jp"
    page_url = base_url + "/english/markets/statistics-equities/misc/01.html"
    
    print(f"Fetching page: {page_url}")
    response = requests.get(page_url)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find link to "data_e.xls" (English) or "data_j.xls" (Japanese)
    # The link text usually contains "List of TSE-listed Issues"
    target_link = None
    for a in soup.find_all("a", href=True):
        if "data_e.xls" in a["href"] or "data_j.xls" in a["href"]:
            target_link = a["href"]
            break
            
    if not target_link:
        # Fallback: try to guess static URL if scraping fails?
        # Or look for specific text
        print("Direct link not found by simple scan. Searching for 'List of TSE-listed Issues'...")
        for a in soup.find_all("a", href=True):
            if "List of TSE-listed Issues" in a.text:
                target_link = a["href"]
                break
    
    if not target_link:
        raise ValueError("Could not find download link for TSE-listed Issues.")
        
    # Handle relative URL
    if not target_link.startswith("http"):
        target_link = base_url + target_link
        
    print(f"Downloading Excel from: {target_link}")
    
    # Download file
    # Note: verify ssl=False if needed, but jpx should be fine
    file_resp = requests.get(target_link)
    file_resp.raise_for_status()
    
    # Read Excel
    # Requires xlrd
    print("Parsing Excel...")
    try:
        # The file is .xls, so engine='xlrd' is typically required, or usually auto-detected if installed.
        df = pd.read_excel(io.BytesIO(file_resp.content))
    except Exception as e:
        print(f"Error reading Excel: {e}")
        print("Try installing xlrd: pip install xlrd")
        return

    # Check columns. usually row 0 or 1 is header.
    # English columns: "Local Code", "Name (English)", "Section/Products", "33 Sector(Code)", "33 Sector(Name)"
    # Japanese columns: "コード", "銘柄名", "市場・商品区分", "33業種コード", "33業種区分"
    
    # Normalize headers
    # Find header row
    # Just look for 'Code' or 'コード'
    header_row = 0
    for i in range(5):
        row_vals = df.iloc[i].astype(str).values
        if "Code" in row_vals or "コード" in row_vals:
            header_row = i
            break
            
    df = pd.read_excel(io.BytesIO(file_resp.content), header=header_row)
    
    # Identify relevant columns
    cols = [str(c) for c in df.columns]
    code_col = next((c for c in cols if "Code" in c and "Local" in c or "コード" in c), None) # Local Code
    name_col = next((c for c in cols if "Name" in c or "銘柄名" in c), None)
    market_col = next((c for c in cols if "Section" in c or "区分" in c), None)
    # Exclude "Code" to find "name" or "区分"
    sector_col = next((c for c in cols if ("33 Sector" in c or "33業種区分" in c) and "Code" not in c and "コード" not in c), None)

    if not (code_col and name_col and market_col and sector_col):
        print("Could not identify columns.")
        print(df.columns)
        return

    print("Filtering for 'Prime' market...")
    # Market values: "Prime (Standard)", "Prime (Growth)" ?? No, usually just "Prime Market"
    # English: "Prime Market"
    # Japanese: "プライム市場"
    
    prime_df = df[df[market_col].astype(str).str.contains("Prime|プライム", case=False, na=False)]
    
    print(f"Found {len(prime_df)} Prime listings.")
    
    # Format Ticker: Code + ".T"
    # Code might be numeric or string. ensure 4 digits?
    # Actually JPX codes can be 4 digits.
    # remove rows where code is NaN
    prime_df = prime_df.dropna(subset=[code_col])
    
    # Create final dataframe
    output_df = pd.DataFrame()
    output_df['ticker'] = prime_df[code_col].astype(str).str.replace(".0", "").str.zfill(4) + ".T"
    output_df['name'] = prime_df[name_col]
    output_df['sector'] = prime_df[sector_col]
    
    # Save
    os.makedirs("batch_jobs/data", exist_ok=True)
    out_path = "batch_jobs/data/prime_tickers.csv"
    output_df.to_csv(out_path, index=False)
    print(f"Saved to {out_path}")
    
    # Verify
    print(output_df.head())

if __name__ == "__main__":
    fetch_prime_tickers()
