import requests
import base64
import json
import os
import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

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
        # We initialize with an empty influx section and nicknames mapping
        config = {
            'access_url': access_url,
            'nicknames': {},
            'influxdb': {
                'url': '',
                'token': '',
                'org': '',
                'bucket': ''
            }
        }
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        
        os.chmod('config.json', 0o600)
        
        print("\nSuccess! Access URL saved to config.json")
        print("Please edit config.json to add your InfluxDB credentials before running 'simplefin-collect'.")
        
    except Exception as e:
        print(f"Error: {e}")

def collect():
    """Fetch account balances and write to InfluxDB."""
    config_path = 'config.json'
    if not os.path.exists(config_path):
        print("Error: config.json not found. Please run 'simplefin-setup' first.")
        return

    with open(config_path, 'r') as f:
        config = json.load(f)
    
    access_url = config.get('access_url')
    influx_cfg = config.get('influxdb', {})
    
    if not access_url:
        print("Error: No access_url found in config.json")
        return
    
    # Validate InfluxDB config
    required_influx = ['url', 'token', 'org', 'bucket']
    missing = [field for field in required_influx if not influx_cfg.get(field)]
    if missing:
        print(f"Error: Missing InfluxDB configuration: {', '.join(missing)}")
        print("Please update config.json with these values.")
        return

    try:
        # 1. Parse Access URL for credentials
        scheme, rest = access_url.split('//', 1)
        auth, rest = rest.split('@', 1)
        url_base = scheme + '//' + rest
        username, password = auth.split(':', 1)
        
        endpoint = f"{url_base.rstrip('/')}/accounts"
        
        # 2. Fetch data from SimpleFIN
        response = requests.get(endpoint, auth=(username, password), params={'version': '2'})
        response.raise_for_status()
        data = response.json()
        
        # 3. Prepare InfluxDB Client
        client = InfluxDBClient(
            url=influx_cfg['url'], 
            token=influx_cfg['token'], 
            org=influx_cfg['org']
        )
        write_api = client.write_api(write_options=SYNCHRONOUS)
        
        points = []
        nicknames = config.get('nicknames', {})
        for acc in data.get('accounts', []):
            # Create a point for each account
            # Measurement: account_balances
            # Tags: account_name (use nickname if available), currency
            # Field: balance
            # Timestamp: Use the balance-date provided by SimpleFIN
            
            raw_name = acc.get('name')
            display_name = nicknames.get(raw_name, raw_name)
            balance_ts = acc.get('balance-date', 0)
            
            point = Point("account_balances") \
                .tag("account_name", display_name) \
                .tag("currency", acc.get('currency')) \
                .field("balance", float(acc.get('balance', 0))) \
                .time(balance_ts, WritePrecision.S)
            
            points.append(point)
        
        # 4. Write to InfluxDB
        write_api.write(bucket=influx_cfg['bucket'], record=points)
        
        print(f"Successfully wrote {len(points)} account balances to InfluxDB at {datetime.datetime.now()}")
        
        client.close()

    except Exception as e:
        print(f"Failed to collect and write balances: {e}")
