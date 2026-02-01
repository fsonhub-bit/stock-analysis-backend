
import requests
import sys

BASE_URL = "http://127.0.0.1:8001"

def test_api():
    print(f"Testing API at {BASE_URL}...")
    
    # 1. Test Recommend Mode
    print("\n[Testing mode='recommend']")
    try:
        res = requests.get(f"{BASE_URL}/api/latest?mode=recommend")
        if res.status_code == 200:
            data = res.json()
            print(f"✅ Success. Count: {data.get('count')}")
            # Verify signals
            signals = set(s['signal'] for s in data['stocks'])
            print(f"   Signals present: {signals}")
        else:
            print(f"❌ Failed: {res.status_code} {res.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # 2. Test All Mode (might be large)
    print("\n[Testing mode='all']")
    try:
        # Just check if it returns more than recommend
        res = requests.get(f"{BASE_URL}/api/latest?mode=all")
        if res.status_code == 200:
            data = res.json()
            count = data.get('count')
            print(f"✅ Success. Count: {count}")
            if count > 100:
                print("   Confirmed 'all' mode returns significantly more data.")
        else:
            print(f"❌ Failed: {res.status_code} {res.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api()
