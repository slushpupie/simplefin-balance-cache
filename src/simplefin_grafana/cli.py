import requests
import base64
import json
import os
import datetime

def setup():
    """Exchange a Setup Token for an Access URL."""
    setup_token = input('Enter your SimpleFIN Setup Token: ').strip()
    
    try:
        # 1. Decode the setup token to get the claim URL
        claim_url = base64.b64decode(setup_token).decode('utf-8')
        print(f"Claiming Access URL from: {claim_url}")
        
        # 2. Exchange setup token for access URL
        response = requests.post(claim_url, headers={'Content-Length': '0'})
        response.raise_for_status()
        access_url = response.text.strip()
        
        # 3. Save to config.json
        config = {'access_url': access_url}
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        
        os.chmod('config.json', 0o600)
        
        print("\nSuccess! Access URL saved to config.json")
        print("You can now run 'simplefin-collect' to fetch your balances.")
        
    except Exception as e:
        print(f"Error: {e}")

def collect():
    """Fetch account balances and save to balances.json."""
    config_path = 'config.json'
    if not os.path.exists(config_path):
        print("Error: config.json not found. Please run 'simplefin-setup' first.")
        return

    with open(config_path, 'r') as f:
        config = json.load(f)
    
    access_url = config.get('access_url')
    if not access_url:
        print("Error: No access_url found in config.json")
        return

    try:
        # Parse Access URL for credentials
        scheme, rest = access_url.split('//', 1)
        auth, rest = rest.split('@', 1)
        url_base = scheme + '//' + rest
        username, password = auth.split(':', 1)
        
        endpoint = f"{url_base.rstrip('/')}/accounts"
        
        # Fetch data
        response = requests.get(endpoint, auth=(username, password), params={'version': '2'})
        response.raise_for_status()
        data = response.json()
        
        balances = []
        for acc in data.get('accounts', []):
            balances.append({
                'name': acc.get('name'),
                'balance': acc.get('balance'),
                'currency': acc.get('currency'),
                'date': datetime.datetime.fromtimestamp(acc.get('balance-date', 0)).isoformat(),
                'updated_at': datetime.datetime.utcnow().isoformat()
            })
        
        output_path = 'balances.json'
        with open(output_path, 'w') as f:
            json.dump({'accounts': balances}, f, indent=4)
            
        print(f"Successfully updated balances at {datetime.datetime.now()}")
        print(f"Data saved to {output_path}")

    except Exception as e:
        print(f"Failed to fetch balances: {e}")
