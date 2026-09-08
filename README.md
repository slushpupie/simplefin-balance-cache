# SimpleFIN Grafana Bridge

A simple Python application that fetches financial account balances from the [SimpleFIN Bridge](https://beta-bridge.simplefin.org/) and exports them to a JSON file for visualization in Grafana.

## 📌 Overview

SimpleFIN provides a standardized API for financial data, but it enforces a strict rate limit (approximately 24 requests per day). To avoid exceeding this limit, this app uses a **Collector Pattern**:
1. It fetches data on a schedule (e.g., every 6 hours).
2. It saves the data to a local `balances.json` file.
3. Grafana reads the local file instead of hitting the API directly.

## 🚀 Quick Start

### 1. Prerequisites
Ensure you have Python 3 and the `requests` library installed:
```bash
pip install requests
```

### 2. Configuration
First, you need a **Setup Token** from the SimpleFIN Bridge:
1. Visit [bridge.simplefin.org/simplefin/create](https://bridge.simplefin.org/simplefin/create).
2. Generate a token.
3. Run the setup script:
   ```bash
   python3 setup.py
   ```
   This will exchange your setup token for a permanent `Access URL` and save it securely in `config.json`.

### 3. Fetching Balances
Run the collector to fetch your current balances:
```bash
python3 collector.py
```
This creates (or updates) `balances.json` with your latest account data.

## 📊 Grafana Integration

To visualize this data, use the [Infinity Datasource](https://grafana.com/grafana/plugins/yesorehounds-infinity-datasource/) plugin:

1. **Install Infinity** in your Grafana instance.
2. **Configure a Source** pointing to the `balances.json` file.
3. **Create a Dashboard** using the `accounts` array to display account names and balances.

## ⏰ Automation

Avoid exceeding rate limits by scheduling the collector via cron. Example for every 6 hours:

```bash
0 */6 * * * /usr/bin/python3 /home/jay/git/simplefin-grafana/collector.py
```
