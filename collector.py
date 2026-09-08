import requests
import json
import os
import datetime

def fetch_balances():
    # 1. Load config
    config_path = 'config.json'
    if not os.path.exists(config_path):
        print("Error: config.json not found. Please run setup.py first.")
        return

    with open(config_path, 'r') as f:
        config = json.load(f)
    
    access_url = config.get('access_url')
    if not access_url:
        print("Error: No access_url found in config.json")
        return

    try:
        # 2. Parse Access URL for credentials
        # Format: https://username:password@host/path
        scheme, rest = access_url.split('//', 1)
        auth, rest = rest.split('@', 1)
        url_base = scheme + '//' + rest
        username, password = auth.split(':', 1)
        
        # The accounts endpoint
        endpoint = f"{url_base.rstrip('/')}/accounts"
        
        # 3. Fetch data
        # SimpleFIN v2 requires ?version=2
        response = requests.get(endpoint, auth=(username, password), params={'version': '2'})
        response.raise_for_status()
        data = response.json()
        
        # 4. Extract just the balances for the dashboard
        # We want a clean list of: { account_name: str, balance: float, date: str }
        balances = []
        for acc in data.get('accounts', []):
            balances.append({
                'name': acc.get('name'),
                'balance': acc.get('balance'),
                'currency': acc.get('currency'),
                'date': datetime.datetime.fromtimestamp(acc.get('balance-date', 0)).isoformat(),
                'updated_at': datetime.datetime.utcnow().isoformat()
            })
        
        # 5. Save to balances.json for Grafana
        output_path = 'balances.json'
        with open(output_path, 'w') as f:
            json.dump({'accounts': balances}, f, indent=4)
            
        print(f"Successfully updated balances at {datetime.datetime.now()}")
        print(f"Data saved to {output_path}")

    except Exception as e:
        print(f"Failed to fetch balances: {e}")

if __name__ == "__main__":
    fetch_balances()
