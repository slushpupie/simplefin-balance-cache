import requests
import base64
import json
import os

def setup():
    setup_token = input('Enter your SimpleFIN Setup Token: ').strip()
    
    try:
        # 1. Decode the setup token to get the claim URL
        claim_url = base64.b64decode(setup_token).decode('utf-8')
        print(f"Claiming Access URL from: {claim_url}")
        
        # 2. Exchange setup token for access URL
        # SimpleFIN expects a POST with Content-Length: 0
        response = requests.post(claim_url, headers={'Content-Length': '0'})
        response.raise_for_status()
        access_url = response.text.strip()
        
        # 3. Save to config.json
        config = {'access_url': access_url}
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        
        # Restrict permissions: only the current user can read/write
        os.chmod('config.json', 0o600)
        
        print("\nSuccess! Access URL saved to config.json")
        print("You can now run collector.py to fetch your balances.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    setup()
