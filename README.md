# APEX Market Intelligence

> Institutional-grade market intelligence platform — social sentiment, technical screening, backtesting, options flow, portfolio tracking, and AI-powered analysis.

---

## 🚀 Deploy to Streamlit Cloud (5 minutes)

### 1. Fork / upload to GitHub

Put these two files in a public (or private) GitHub repo:
```
your-repo/
├── app.py              ← rename market_intelligence_app.py to app.py
└── requirements.txt
```

### 2. Connect to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
2. Click **New app**
3. Select your repo, branch (`main`), and set **Main file path** to `app.py`
4. Click **Deploy**

That's it — no secrets required. Users enter their own Gemini key in the sidebar.

---

## 🔑 Gemini API Key

All market data features work without a key. AI features require a **free** Gemini key.

**Users** enter their key in the sidebar → `🔑 Gemini API Key` → paste → **Save & Test**.  
The key lives in the browser session only and is never stored server-side.

**Host (optional):** If you want to pre-supply a key for all users, add it as a Streamlit Cloud secret:
1. In your app dashboard → **Settings → Secrets**
2. Add:
```toml
GEMINI_API_KEY = "AIza..."
```
Users can still override with their own key.

**Get a free key:** [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

---

## 📦 Features

| Page | Description |
|------|-------------|
| 🌐 Intelligence | Scrape Reddit + Twitter → Gemini-powered hedge fund report |
| 📈 Screener | EMA / RSI / MACD / Bollinger / VWAP / ATR across 35+ tickers |
| 🔬 Deep Dive | Single-stock 4-panel chart + full AI analysis with entry/stop/target |
| 🎯 Options Flow | P/C ratio, unusual activity, max pain, full option chain |
| 🚨 Alert Engine | 15 configurable conditions, auto-scans watchlist, AI commentary |
| 💼 Portfolio | Live P&L, allocation charts, AI portfolio review |
| 📰 News & Earnings | Yahoo Finance RSS + AI sentiment + earnings countdown |
| ⚗️ Backtester | 6 strategies, equity curve, drawdown chart, Sharpe, AI analysis |

---

## 🛠 Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

To set the API key locally, create `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "AIza..."
```

---

## ⚠️ Disclaimer

AI-generated content only. Not financial advice. Past backtest performance does not guarantee future results.
