import argparse
import csv
import json
import os
import sys
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

def load_config():
    config_path = 'config.json'
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found. Please run setup.py first.")
        sys.exit(1)
    with open(config_path, 'r') as f:
        return json.load(f)

def parse_column(row, col_spec, header):
    """Get value from row based on index (0-based) or header name."""
    try:
        if isinstance(col_spec, int):
            return row[col_spec]
        elif isinstance(col_spec, str):
            if col_spec in header:
                return row[header.index(col_spec)]
            else:
                # Try to treat string as index if it's numeric
                return row[int(col_spec)]
    except (IndexError, ValueError):
        return None

def import_csv():
    parser = argparse.ArgumentParser(description="Import historical balance data from CSV to InfluxDB")
    parser.add_argument("--account", required=True, help="Account name (will be mapped via config.json nicknames)")
    parser.add_argument("--file", required=True, help="Path to the CSV file")
    parser.add_argument("--date-col", required=True, help="Column name or 0-based index for the date")
    parser.add_argument("--balance-col", required=True, help="Column name or 0-based index for the balance")
    
    args = parser.parse_args()
    config = load_config()
    
    # 1. Resolve Account Name / Nickname
    # If the provided name is a key in nicknames, use the value (the nickname)
    # If it's a value, we'll just use it as is.
    nicknames = config.get('nicknames', {})
    display_name = nicknames.get(args.account, args.account)
    
    # 2. InfluxDB Config
    influx_cfg = config.get('influxdb', {})
    required_influx = ['url', 'token', 'org', 'bucket']
    if not all(influx_cfg.get(f) for f in required_influx):
        print("Error: InfluxDB configuration incomplete in config.json")
        sys.exit(1)

    try:
        with open(args.file, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            # Determine column indices
            try:
                date_idx = int(args.date_col) if args.date_col.isdigit() else header.index(args.date_col)
                bal_idx = int(args.balance_col) if args.balance_col.isdigit() else header.index(args.balance_col)
            except ValueError as e:
                print(f"Error: Could not find specified columns in CSV header: {header}")
                print(f"Details: {e}")
                sys.exit(1)

            # Prepare InfluxDB Client
            client = InfluxDBClient(url=influx_cfg['url'], token=influx_cfg['token'], org=influx_cfg['org'])
            write_api = client.write_api(write_options=SYNCHRONOUS)
            
            points = []
            count = 0
            
            for row in reader:
                if not row: continue
                
                date_val = row[date_idx]
                bal_val = row[bal_idx]
                
                try:
                    # Clean balance string (remove currency symbols, commas)
                    clean_bal = float(bal_val.replace('$', '').replace(',', '').strip())
                    
                    # Try common date formats
                    dt = None
                    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
                        try:
                            dt = datetime.strptime(date_val.strip(), fmt)
                            break
                        except ValueError:
                            continue
                    
                    if dt is None:
                        continue # Skip rows with unparseable dates

                    point = Point("account_balances") \
                        .tag("account_name", display_name) \
                        .tag("currency", "USD") \
                        .field("balance", clean_bal) \
                        .time(int(dt.timestamp()), WritePrecision.S)
                    
                    points.append(point)
                    count += 1
                except (ValueError, TypeError):
                    continue # Skip malformed rows

                # Write in batches to avoid memory issues with huge CSVs
                if len(points) >= 500:
                    write_api.write(bucket=influx_cfg['bucket'], record=points)
                    points = []

            if points:
                write_api.write(bucket=influx_cfg['bucket'], record=points)
            
            print(f"Successfully imported {count} historical records for '{display_name}' to InfluxDB.")
            client.close()

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import_csv()
