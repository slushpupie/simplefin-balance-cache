# AGENTS.md - Project Context for AI Assistants

This project is a financial data bridge between SimpleFIN and Grafana.

## 🎯 Project Goal
To provide a low-frequency, rate-limit-safe way to visualize bank account balances in a Grafana dashboard.

## ⚠️ CRITICAL CONSTRAINT: Rate Limits
**SimpleFIN allows approximately 24 requests per day.**
- **DO NOT** implement a real-time scraper or a Prometheus exporter that polls the API frequently.
- **DO NOT** suggest changes that increase the frequency of API calls without a very strong reason.
- **Always** adhere to the **Collector Pattern**: fetch once $\rightarrow$ save to file $\rightarrow$ read from file.

## 📁 File Architecture
- `setup.py`: One-time utility to exchange the Setup Token for an Access URL.
- `collector.py`: The main engine. Fetches data and writes to `balances.json`.
- `config.json`: (Git ignored) Stores the sensitive `Access URL`. Permissions should be `0600`.
- `balances.json`: The output file intended for the Grafana Infinity plugin.
- `README.md`: User documentation.

## 🛠️ Development Guidelines for Agents
1. **Security First:** Never log or commit the `Access URL` or the contents of `config.json`.
2. **Data Integrity:** When updating `collector.py`, ensure the output format of `balances.json` remains compatible with the existing Grafana dashboard mapping.
3. **Dependency Management:** Keep dependencies minimal. Only `requests` is currently required.
4. **Testing:** Since API calls are limited, prefer using mock data or a local JSON file for testing logic changes before running against the live bridge.

## 📈 Future Roadmap
- Implement a small HTTP wrapper (e.g., FastAPI or Flask) to serve `balances.json` if the Grafana instance is on a different host.
- Add support for transaction history summaries (though this will consume more of the daily quota).
