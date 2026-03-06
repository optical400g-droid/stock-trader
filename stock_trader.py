"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          APEX MARKET INTELLIGENCE — v3.0                                    ║
║          UI Overhaul · Backtesting · Auto-Refresh · Deep AI                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import streamlit as st
import base64
import json
import re
import time
import logging
import requests
import pandas as pd
import numpy as np
import feedparser
import google.generativeai as genai
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ──────────────────────────────────────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  ←  must be first Streamlit call
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="APEX Market Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS — dark terminal aesthetic, custom fonts, animated elements
# ──────────────────────────────────────────────────────────────────────────────
GLOBAL_CSS = """
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Syne:wght@700;800&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background: #040810 !important;
    color: #e2e8f0 !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #070d1a !important;
    border-right: 1px solid #1e2d45 !important;
}
[data-testid="stSidebar"] * { color: #94a3b8 !important; }
[data-testid="stSidebar"] .stRadio label { 
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.5px;
    padding: 6px 0;
    transition: color 0.2s;
}
[data-testid="stSidebar"] .stRadio label:hover { color: #38bdf8 !important; }

/* ── Top header bar ── */
.apex-header {
    background: linear-gradient(135deg, #040810 0%, #071422 50%, #040810 100%);
    border-bottom: 1px solid #1e3a5f;
    padding: 18px 32px 14px;
    margin: -1rem -1rem 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
}
.apex-header::before {
    content: '';
    position: absolute; inset: 0;
    background: repeating-linear-gradient(
        90deg, transparent, transparent 80px,
        rgba(56,189,248,0.03) 80px, rgba(56,189,248,0.03) 81px
    );
}
.apex-logo {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem; font-weight: 800;
    background: linear-gradient(135deg, #38bdf8, #818cf8, #f472b6);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    letter-spacing: -1px;
}
.apex-logo span { color: #38bdf8; }
.apex-tagline {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; color: #475569;
    letter-spacing: 2px; text-transform: uppercase;
    margin-top: 2px;
}
.apex-time {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem; color: #38bdf8;
    letter-spacing: 1px;
}

/* ── Ticker strip ── */
.ticker-strip {
    background: #07111f;
    border-top: 1px solid #1e3a5f;
    border-bottom: 1px solid #1e3a5f;
    padding: 8px 0;
    overflow: hidden;
    white-space: nowrap;
    margin: 0 -1rem;
}
.ticker-item {
    display: inline-block;
    margin: 0 28px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    letter-spacing: 0.5px;
}
.ticker-up   { color: #34d399; }
.ticker-down { color: #f87171; }
.ticker-name { color: #94a3b8; margin-right: 6px; }

/* ── Metric cards ── */
.metric-card {
    background: linear-gradient(135deg, #0a1628, #0d1f35);
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 16px 20px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s, transform 0.2s;
}
.metric-card:hover { border-color: #38bdf8; transform: translateY(-2px); }
.metric-card::after {
    content: '';
    position: absolute; top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #38bdf8, #818cf8);
}
.metric-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem; color: #64748b;
    text-transform: uppercase; letter-spacing: 1.5px;
    margin-bottom: 6px;
}
.metric-value {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem; font-weight: 700;
    color: #f1f5f9; line-height: 1;
}
.metric-delta { font-size: 0.78rem; margin-top: 4px; font-weight: 500; }
.delta-up   { color: #34d399; }
.delta-down { color: #f87171; }
.delta-neu  { color: #94a3b8; }

/* ── Section headers ── */
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.15rem; font-weight: 700;
    color: #f1f5f9;
    border-left: 3px solid #38bdf8;
    padding-left: 12px;
    margin: 24px 0 14px;
    letter-spacing: -0.3px;
}
.section-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem; color: #475569;
    text-transform: uppercase; letter-spacing: 1.5px;
    margin-bottom: 16px;
}

/* ── Signal badges ── */
.badge {
    display: inline-block;
    padding: 3px 10px; border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem; font-weight: 700;
    letter-spacing: 0.5px; text-transform: uppercase;
}
.badge-strong-buy  { background: #052e16; color: #34d399; border: 1px solid #166534; }
.badge-buy         { background: #052e16; color: #4ade80; border: 1px solid #166534; }
.badge-hold        { background: #1c1a03; color: #facc15; border: 1px solid #713f12; }
.badge-sell        { background: #2d0a0a; color: #f87171; border: 1px solid #7f1d1d; }
.badge-strong-sell { background: #1a0000; color: #ef4444; border: 1px solid #991b1b; }

/* ── Alert cards ── */
.alert-card {
    background: #07111f;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 10px;
    border-left: 4px solid #38bdf8;
    transition: border-color 0.3s;
}
.alert-card.bullish { border-left-color: #34d399; }
.alert-card.bearish { border-left-color: #f87171; }
.alert-card.warning { border-left-color: #facc15; }
.alert-ticker {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem; font-weight: 800;
    color: #38bdf8;
}
.alert-conditions {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem; color: #64748b;
    margin-top: 4px;
}

/* ── Auto-refresh badge ── */
.refresh-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #052e16; border: 1px solid #166534;
    border-radius: 20px; padding: 4px 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem; color: #34d399;
}
.refresh-dot {
    width: 8px; height: 8px;
    background: #34d399; border-radius: 50%;
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.4; transform: scale(0.8); }
}

/* ── News cards ── */
.news-card {
    background: #07111f;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    transition: border-color 0.2s;
}
.news-card:hover { border-color: #38bdf8; }
.news-title { color: #93c5fd; font-weight: 600; font-size: 0.92rem; text-decoration: none; }
.news-meta  { font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #475569; margin-top: 4px; }

/* ── Earnings countdown ── */
.earnings-chip {
    display: inline-flex; align-items: center; gap: 10px;
    background: #07111f; border: 1px solid #1e3a5f;
    border-radius: 8px; padding: 10px 16px; margin-bottom: 8px;
    width: 100%;
}
.earnings-chip.urgent { border-color: #f59e0b; background: #1c1200; }
.earnings-chip.soon   { border-color: #34d399; background: #031a0e; }

/* ── Backtest result ── */
.bt-stat {
    background: #0a1628;
    border: 1px solid #1e3a5f; border-radius: 8px;
    padding: 14px; text-align: center;
}
.bt-stat-val {
    font-family: 'Syne', sans-serif;
    font-size: 1.4rem; font-weight: 700;
}
.bt-stat-lbl {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem; color: #64748b;
    text-transform: uppercase; letter-spacing: 1px;
    margin-top: 4px;
}

/* ── Dataframes ── */
[data-testid="stDataFrame"] { background: #07111f !important; }
.stDataFrame { font-family: 'JetBrains Mono', monospace !important; font-size: 0.8rem !important; }

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #0f3460, #1a4a8a) !important;
    color: #e2e8f0 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.5px;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #1a4a8a, #2563eb) !important;
    border-color: #38bdf8 !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0369a1, #0ea5e9) !important;
    border-color: #38bdf8 !important;
}

/* ── Inputs ── */
.stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
    background: #07111f !important;
    border: 1px solid #1e3a5f !important;
    color: #e2e8f0 !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #07111f !important;
    border-bottom: 1px solid #1e3a5f !important;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #64748b !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important;
    padding: 10px 20px !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    letter-spacing: 0.5px;
}
.stTabs [aria-selected="true"] {
    color: #38bdf8 !important;
    border-bottom: 2px solid #38bdf8 !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    background: #07111f !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 8px !important;
}

/* ── Divider ── */
hr { border-color: #1e3a5f !important; }

/* ── Progress bar ── */
.stProgress > div > div { background: linear-gradient(90deg, #38bdf8, #818cf8) !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #040810; }
::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #38bdf8; }
</style>
"""

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# CONSTANTS & CONFIG
# ──────────────────────────────────────────────────────────────────────────────
REDDIT_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
]

DEFAULT_SUBREDDITS = sorted(set([
    "wallstreetbets", "stocks", "investing", "StockMarket", "options",
    "daytrading", "pennystocks", "valueinvesting", "dividends",
    "SecurityAnalysis", "FinancialIndependence", "ETFs", "Bogleheads",
    "RealEstateInvesting", "AlgorithmicTrading", "QuantTrading",
    "smallstreetbets", "thetagang", "WallStreet", "Finance",
    "EquityResearch", "Economics", "Business", "FinTech",
    "CryptoMarkets", "BTC", "Trading", "StockPicks",
]))

DEFAULT_TWITTER = [
    "MarketWatch", "CNBCnow", "zerohedge", "OptionsHawk",
    "CharlieBilello", "PeterLBrandt", "TaviCosta", "Ritholtz",
    "BespokeInvest", "MktOutperform", "ARKInvest", "CathieDWood",
]

DEFAULT_TICKERS = [
    "AAPL","MSFT","GOOGL","AMZN","META","NVDA","TSLA","AVGO","AMD","ARM",
    "JPM","V","BRK-B","GS","MS",
    "JNJ","UNH","LLY","ABBV","PFE",
    "XOM","CVX","COP",
    "WMT","KO","PEP","PG","COST","MCD",
    "HD","DIS","AMZN",
    "PLTR","SMCI","COIN","MSTR",
]

SECTOR_MAP = {
    "AAPL":"Technology","MSFT":"Technology","GOOGL":"Technology",
    "META":"Technology","NVDA":"Technology","AVGO":"Technology",
    "AMD":"Technology","ARM":"Technology","PLTR":"Technology","SMCI":"Technology",
    "AMZN":"Consumer Discretionary","TSLA":"Consumer Discretionary",
    "HD":"Consumer Discretionary","MCD":"Consumer Discretionary","DIS":"Communication Services",
    "JPM":"Financials","V":"Financials","BRK-B":"Financials","GS":"Financials","MS":"Financials",
    "COIN":"Financials","MSTR":"Financials",
    "JNJ":"Healthcare","UNH":"Healthcare","LLY":"Healthcare","ABBV":"Healthcare","PFE":"Healthcare",
    "XOM":"Energy","CVX":"Energy","COP":"Energy",
    "WMT":"Consumer Staples","KO":"Consumer Staples","PEP":"Consumer Staples",
    "PG":"Consumer Staples","COST":"Consumer Staples",
}

PLOTLY_DARK = dict(
    template="plotly_dark",
    paper_bgcolor="#07111f",
    plot_bgcolor="#07111f",
    font=dict(family="JetBrains Mono, monospace", color="#94a3b8", size=11),
    xaxis=dict(gridcolor="#1e2d45", linecolor="#1e2d45"),
    yaxis=dict(gridcolor="#1e2d45", linecolor="#1e2d45"),
)

# ──────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ──────────────────────────────────────────────────────────────────────────────
for key, val in {
    "ai_df":            None,
    "portfolio":        [],
    "_cached_screener": None,
    "alerts_run":       False,
    "last_refresh":     None,
    "refresh_count":    0,
    "gemini_api_key":   "",
    "gemini_validated": False,
    "gemini_model_obj": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ──────────────────────────────────────────────────────────────────────────────
# GEMINI — user-supplied key (works on Streamlit Cloud with no secrets needed)
# ──────────────────────────────────────────────────────────────────────────────

def _resolve_api_key() -> str:
    """
    Priority order:
    1. Key entered by user in the UI this session
    2. GEMINI_API_KEY from st.secrets (set by host / Streamlit Cloud env var)
    3. Empty string → no key available
    """
    if st.session_state.get("gemini_api_key"):
        return st.session_state["gemini_api_key"].strip()
    try:
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return ""

def get_gemini_model():
    """Return a live GenerativeModel or None. Uses session-scoped key."""
    key = _resolve_api_key()
    if not key:
        return None
    # Rebuild model if key changed since last call
    cached_key = st.session_state.get("_gemini_key_used", "")
    if st.session_state.get("gemini_model_obj") is None or cached_key != key:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            st.session_state["gemini_model_obj"] = model
            st.session_state["_gemini_key_used"]  = key
        except Exception as e:
            logger.error("Gemini init: %s", e)
            st.session_state["gemini_model_obj"] = None
    return st.session_state.get("gemini_model_obj")

def validate_gemini_key(key: str) -> tuple[bool, str]:
    """Send a cheap test request to verify the key works. Returns (ok, message)."""
    if not key or len(key) < 20:
        return False, "Key looks too short — please double-check."
    try:
        genai.configure(api_key=key.strip())
        m = genai.GenerativeModel("gemini-2.5-flash")
        resp = m.generate_content("Reply with the single word: OK")
        if resp and resp.text:
            return True, "✅ API key validated successfully!"
        return False, "Key accepted but model returned empty response."
    except Exception as e:
        msg = str(e)
        if "API_KEY_INVALID" in msg or "invalid" in msg.lower():
            return False, "❌ Invalid API key — please check and re-enter."
        if "quota" in msg.lower():
            return False, "⚠️ Key valid but quota exceeded on your account."
        return False, f"❌ Error: {msg}"

def call_gemini(prompt: str, max_chars: int = 30_000) -> str:
    model = get_gemini_model()
    if not model:
        return (
            "⚠️ **Gemini API key not set.**\n\n"
            "Enter your key in the **sidebar → 🔑 API Key** section, then retry."
        )
    try:
        resp = model.generate_content(prompt[:max_chars])
        return resp.text if resp and resp.text else "No response from model."
    except Exception as e:
        err = str(e)
        if "API_KEY_INVALID" in err:
            st.session_state["gemini_validated"] = False
            return "❌ API key rejected. Please re-enter a valid key in the sidebar."
        return f"Gemini error: {err}"

def render_api_key_sidebar():
    """
    Sidebar widget for entering and validating the Gemini API key.
    Called once near the top of sidebar rendering.
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.68rem;'
        'color:#475569;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px;">'
        '🔑 Gemini API Key</div>',
        unsafe_allow_html=True,
    )

    current_key = st.session_state.get("gemini_api_key", "")
    display_key = current_key  # show full key so user can edit; masked by password type

    new_key = st.sidebar.text_input(
        "API Key",
        value=current_key,
        type="password",
        placeholder="AIza...",
        label_visibility="collapsed",
        key="api_key_input",
    )

    col_save, col_clear = st.sidebar.columns(2)
    with col_save:
        if st.button("Save & Test", key="api_save", use_container_width=True):
            if new_key.strip():
                with st.spinner("Validating…"):
                    ok, msg = validate_gemini_key(new_key.strip())
                st.session_state["gemini_api_key"]   = new_key.strip() if ok else current_key
                st.session_state["gemini_validated"]  = ok
                st.session_state["gemini_model_obj"]  = None  # force rebuild
                if ok:
                    st.sidebar.success(msg)
                else:
                    st.sidebar.error(msg)
            else:
                st.sidebar.warning("Enter a key first.")
    with col_clear:
        if st.button("Clear", key="api_clear", use_container_width=True):
            st.session_state["gemini_api_key"]  = ""
            st.session_state["gemini_validated"] = False
            st.session_state["gemini_model_obj"] = None
            st.rerun()

    # Status indicator
    key_active = bool(_resolve_api_key())
    if key_active and st.session_state.get("gemini_validated"):
        st.sidebar.markdown(
            '<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.7rem;'
            'color:#34d399;margin-top:4px;">● Key active &amp; validated</div>',
            unsafe_allow_html=True,
        )
    elif key_active:
        st.sidebar.markdown(
            '<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.7rem;'
            'color:#fbbf24;margin-top:4px;">● Key set (not yet tested)</div>',
            unsafe_allow_html=True,
        )
    else:
        # Check if a host-level secret exists
        try:
            host_key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            host_key = ""
        if host_key:
            st.sidebar.markdown(
                '<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.7rem;'
                'color:#34d399;margin-top:4px;">● Using host-configured key</div>',
                unsafe_allow_html=True,
            )
        else:
            st.sidebar.markdown(
                '<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.7rem;'
                'color:#f87171;margin-top:4px;">● No key — AI features disabled</div>',
                unsafe_allow_html=True,
            )

    st.sidebar.markdown(
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.65rem;'
        'color:#334155;margin-top:6px;">Key is stored in your browser session only.<br>'
        'Get a free key at <a href="https://aistudio.google.com/app/apikey" '
        'target="_blank" style="color:#38bdf8;">aistudio.google.com</a></div>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")

def render_no_key_banner():
    """Show a helpful onboarding banner when no AI key is present."""
    key_present = bool(_resolve_api_key())
    if key_present:
        return  # nothing to show

    st.markdown("""
    <div style="background:linear-gradient(135deg,#071422,#0a1f35);border:1px solid #1e3a5f;
    border-left:4px solid #38bdf8;border-radius:8px;padding:20px 24px;margin:12px 0 20px;">
    <div style="font-family:'Syne',sans-serif;font-size:1.05rem;font-weight:700;color:#38bdf8;margin-bottom:8px;">
    🔑 Add your Gemini API Key to unlock AI features</div>
    <div style="font-family:'Space Grotesk',sans-serif;font-size:0.88rem;color:#94a3b8;line-height:1.6;">
    All market data, charts, screener, backtester, options flow, and portfolio tracker work without a key.<br>
    AI-powered features (report generation, trade commentary, news sentiment, deep dive analysis) require a
    <strong style="color:#e2e8f0;">free Gemini API key</strong>.<br><br>
    <strong style="color:#e2e8f0;">How to get one (free):</strong><br>
    1. Visit <a href="https://aistudio.google.com/app/apikey" target="_blank"
       style="color:#38bdf8;">aistudio.google.com/app/apikey</a><br>
    2. Sign in with Google → click <em>Create API Key</em><br>
    3. Copy the key and paste it into the <strong style="color:#e2e8f0;">🔑 Gemini API Key</strong> field in the sidebar → click <em>Save &amp; Test</em>
    </div>
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# TECHNICAL INDICATORS
# ──────────────────────────────────────────────────────────────────────────────
def calc_rsi(s: pd.Series, period=14) -> pd.Series:
    d = s.diff(1)
    g = d.where(d > 0, 0.0).rolling(period).mean()
    l = (-d.where(d < 0, 0.0)).rolling(period).mean()
    return 100 - 100 / (1 + g / l.replace(0, np.nan))

def calc_macd(s: pd.Series):
    e12 = s.ewm(span=12, adjust=False).mean()
    e26 = s.ewm(span=26, adjust=False).mean()
    m = e12 - e26
    sig = m.ewm(span=9, adjust=False).mean()
    return m, sig, m - sig

def calc_bb(s: pd.Series, period=20, std=2.0):
    sma = s.rolling(period).mean()
    sd  = s.rolling(period).std()
    return sma + std*sd, sma, sma - std*sd

def calc_atr(h: pd.DataFrame, period=14) -> pd.Series:
    hl = h["High"] - h["Low"]
    hc = (h["High"] - h["Close"].shift()).abs()
    lc = (h["Low"]  - h["Close"].shift()).abs()
    return pd.concat([hl, hc, lc], axis=1).max(axis=1).rolling(period).mean()

def compute_technicals(hist: pd.DataFrame) -> pd.DataFrame:
    h = hist.copy()
    h["EMA_9"]   = h["Close"].ewm(span=9,   adjust=False).mean()
    h["EMA_21"]  = h["Close"].ewm(span=21,  adjust=False).mean()
    h["EMA_50"]  = h["Close"].ewm(span=50,  adjust=False).mean()
    h["EMA_200"] = h["Close"].ewm(span=200, adjust=False).mean()
    h["RSI"]     = calc_rsi(h["Close"])
    h["TP"]      = (h["High"] + h["Low"] + h["Close"]) / 3
    h["VWAP"]    = (h["TP"] * h["Volume"]).cumsum() / h["Volume"].cumsum()
    h["MACD"], h["MACD_Sig"], h["MACD_Hist"] = calc_macd(h["Close"])
    h["BB_Up"], h["BB_Mid"], h["BB_Lo"] = calc_bb(h["Close"])
    h["ATR"]     = calc_atr(h)
    h["VolMA20"] = h["Volume"].rolling(20).mean()
    h["VolSpike"]= h["Volume"] / h["VolMA20"]
    rsi_min = h["RSI"].rolling(14).min()
    rsi_max = h["RSI"].rolling(14).max()
    h["StochRSI"]= (h["RSI"] - rsi_min) / (rsi_max - rsi_min + 1e-10) * 100
    return h

def calc_support_resistance(hist: pd.DataFrame) -> dict:
    r = hist.tail(60)
    pivot = float((r["High"].iloc[-1] + r["Low"].iloc[-1] + r["Close"].iloc[-1]) / 3)
    return {
        "resistance": float(r["High"].nlargest(3).mean()),
        "support":    float(r["Low"].nsmallest(3).mean()),
        "pivot": pivot,
        "r1": float(2*pivot - r["Low"].iloc[-1]),
        "s1": float(2*pivot - r["High"].iloc[-1]),
    }

def calc_momentum(hist: pd.DataFrame) -> dict:
    c = hist["Close"]
    n = len(c)
    def p(d): return float((c.iloc[-1]/c.iloc[-d]-1)*100) if n > d else float("nan")
    return {"1W": p(5), "1M": p(21), "3M": p(63), "6M": p(126)}

def generate_signal(price, e9, e21, e50, rsi, vwap, macd, msig, bbu, bbl, vspike):
    score = sum([e9>e21, e21>e50, price>vwap, macd>msig, vspike>1.5])
    ob = rsi >= 70; os = rsi <= 30
    if score >= 4 and not ob: return "STRONG BUY", score
    if score >= 3 and not ob: return "BUY", score
    if score == 0 or (e9 < e21 < e50): return "STRONG SELL", score
    if score <= 1: return "SELL", score
    if ob or price > bbu: return "HOLD (Overbought)", score
    if os or price < bbl: return "BUY", score
    return "HOLD", score

# ──────────────────────────────────────────────────────────────────────────────
# LIVE DATA FETCHERS
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=120)
def fetch_market_overview():
    indices = {"SPY":"SPY","QQQ":"QQQ","IWM":"IWM","GLD":"GLD","BTC":"BTC-USD","VIX":"^VIX"}
    out = {}
    for name, t in indices.items():
        try:
            h = yf.Ticker(t).history(period="5d")
            if len(h) >= 2:
                c = float(h["Close"].iloc[-1])
                p = float(h["Close"].iloc[-2])
                out[name] = {"price": c, "change": (c/p-1)*100, "ticker": t}
        except Exception: pass
    return out

@st.cache_data(ttl=3600)
def fetch_stock_data_all(tickers: tuple) -> pd.DataFrame:
    results, errors = [], []
    prog = st.progress(0, text="Loading ticker data…")
    for i, ticker in enumerate(tickers):
        try:
            stk  = yf.Ticker(ticker)
            hist = stk.history(period="6mo")
            if hist.empty: errors.append(f"{ticker}: empty"); continue
            hist = compute_technicals(hist)
            last = hist.iloc[-1]
            info = stk.info
            def g(k, d=float("nan")): return info.get(k, d)
            price  = float(last["Close"])
            e9,e21,e50 = float(last["EMA_9"]),float(last["EMA_21"]),float(last["EMA_50"])
            rsi  = float(last["RSI"])
            vwap = float(last["VWAP"])
            macd = float(last["MACD"])   if not pd.isna(last["MACD"])   else 0.
            msig = float(last["MACD_Sig"]) if not pd.isna(last["MACD_Sig"]) else 0.
            bbu  = float(last["BB_Up"])  if not pd.isna(last["BB_Up"])  else price
            bbl  = float(last["BB_Lo"])  if not pd.isna(last["BB_Lo"])  else price
            vs   = float(last["VolSpike"]) if not pd.isna(last["VolSpike"]) else 1.
            sig, score = generate_signal(price,e9,e21,e50,rsi,vwap,macd,msig,bbu,bbl,vs)
            sr  = calc_support_resistance(hist)
            mom = calc_momentum(hist)
            dy  = g("dividendYield")
            tp  = g("targetMeanPrice")
            ets = g("earningsTimestamp")
            esoon = False
            if ets:
                try:
                    ed = datetime.fromtimestamp(ets)
                    esoon = 0 <= (ed - datetime.now()).days <= 30
                except Exception: pass
            results.append({
                "Ticker":       ticker,
                "Company":      g("shortName", ticker),
                "Sector":       g("sector", SECTOR_MAP.get(ticker,"Unknown")),
                "Price":        price, "Signal": sig, "Score": score,
                "EMA 9":e9,"EMA 21":e21,"EMA 50":e50,
                "RSI":rsi,"VWAP":vwap,"MACD":macd,
                "BB Up":bbu,"BB Lo":bbl,"ATR":float(last["ATR"]) if not pd.isna(last["ATR"]) else np.nan,
                "Vol Spike":vs,
                "Support":sr["support"],"Resistance":sr["resistance"],"Pivot":sr["pivot"],
                "1W%":mom["1W"],"1M%":mom["1M"],"3M%":mom["3M"],"6M%":mom["6M"],
                "Fwd PE":g("forwardPE") or np.nan,
                "Target":tp if tp else np.nan,
                "Upside%":((tp/price-1)*100) if tp and price else np.nan,
                "Rating":g("recommendationKey","N/A").upper(),
                "DivYield%": round(dy*100,3) if dy else 0.,
                "MktCap$B":(g("marketCap") or 0)/1e9,
                "Beta":g("beta",np.nan),
                "ShortRatio":g("shortRatio",np.nan),
                "EarningsSoon":"⚠️" if esoon else "—",
            })
        except Exception as e:
            errors.append(f"{ticker}: {e}")
        prog.progress((i+1)/len(tickers), text=f"  {ticker} ({i+1}/{len(tickers)})")
    prog.empty()
    if errors:
        with st.expander(f"⚠️ {len(errors)} failed"):
            for e in errors: st.caption(e)
    if not results: return pd.DataFrame()
    df = pd.DataFrame(results)
    num = ["Price","EMA 9","EMA 21","EMA 50","RSI","VWAP","MACD","BB Up","BB Lo",
           "ATR","Vol Spike","Support","Resistance","Pivot",
           "1W%","1M%","3M%","6M%","Fwd PE","Target","Upside%","DivYield%","MktCap$B","Beta","ShortRatio"]
    for c in num:
        if c in df: df[c] = pd.to_numeric(df[c], errors="coerce")
    st.session_state["_cached_screener"] = df
    return df

@st.cache_data(ttl=300)
def fetch_live_quote(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).info
        return {k: info.get(k, np.nan) for k in [
            "bid","ask","dayLow","dayHigh","fiftyTwoWeekLow","fiftyTwoWeekHigh",
            "marketCap","beta","averageVolume","targetMeanPrice",
            "recommendationKey","shortRatio","sector","industry",
            "earningsTimestamp","shortName","forwardPE","trailingEps",
        ]}
    except Exception: return {}

# ──────────────────────────────────────────────────────────────────────────────
# SCRAPING
# ──────────────────────────────────────────────────────────────────────────────
def scrape_reddit(sub, limit=25):
    out = []
    try:
        r = requests.get(f"https://www.reddit.com/r/{sub}/new.json?limit={limit}",
                         headers=REDDIT_HEADERS, timeout=10)
        r.raise_for_status()
        for p in r.json()["data"]["children"]:
            d = p["data"]
            out.append({"Platform":"Reddit","Source":f"r/{sub}","Content":d["title"],
                        "Created":datetime.fromtimestamp(d["created_utc"]),
                        "URL":"https://reddit.com"+d["permalink"]})
    except Exception as e: logger.warning("Reddit r/%s: %s", sub, e)
    return out

def scrape_twitter(user, limit=10):
    for inst in NITTER_INSTANCES:
        try:
            feed = feedparser.parse(f"{inst}/{user}/rss")
            if not feed.entries: continue
            return [{"Platform":"Twitter","Source":f"@{user}","Content":e.title,
                     "Created":datetime(*e.published_parsed[:6]) if hasattr(e,"published_parsed") and e.published_parsed else None,
                     "URL":e.link} for e in feed.entries[:limit]]
        except Exception: continue
    return []

def scrape_all(subs, users, limit, workers=12):
    posts = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        fs = {**{ex.submit(scrape_reddit,s,limit):f"r/{s}" for s in subs},
              **{ex.submit(scrape_twitter,u,limit):f"@{u}" for u in users}}
        for f in as_completed(fs):
            try: posts.extend(f.result())
            except Exception: pass
    if not posts: return pd.DataFrame()
    df = pd.DataFrame(posts)
    df["Created"] = pd.to_datetime(df["Created"], errors="coerce")
    return df.sort_values("Created", ascending=False).reset_index(drop=True)

# ──────────────────────────────────────────────────────────────────────────────
# UI HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def metric_card(label: str, value: str, delta: str = "", delta_up: bool = True):
    delta_class = "delta-up" if delta_up else "delta-down"
    delta_html  = f'<div class="metric-delta {delta_class}">{delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>""", unsafe_allow_html=True)

def signal_badge(sig: str) -> str:
    cls = {
        "STRONG BUY":"strong-buy","BUY":"buy","HOLD":"hold",
        "HOLD (Overbought)":"hold","SELL":"sell","SELL (RSI High)":"sell",
        "STRONG SELL":"strong-sell",
    }.get(sig, "hold")
    return f'<span class="badge badge-{cls}">{sig}</span>'

def hl_signal(val):
    m = {
        "STRONG BUY": ("bg:#052e16", "color:#34d399"),
        "BUY":        ("bg:#052e16", "color:#4ade80"),
        "HOLD":       ("bg:#1c1a03", "color:#facc15"),
        "HOLD (Overbought)":("bg:#1c1a03","color:#facc15"),
        "SELL":       ("bg:#2d0a0a", "color:#f87171"),
        "SELL (RSI High)":("bg:#2d0a0a","color:#f87171"),
        "STRONG SELL":("bg:#1a0000", "color:#ef4444"),
    }
    if val in m:
        bg_s, c_s = m[val]
        bg = bg_s.split(":")[1]; c = c_s.split(":")[1]
        return f"background-color:{bg};color:{c};font-weight:700;font-family:'JetBrains Mono',monospace;"
    return ""

def hl_mom(val):
    if pd.isna(val): return ""
    return f"color:{'#34d399' if val>0 else '#f87171'};font-weight:600"

def render_plotly(fig, **kwargs):
    fig.update_layout(**PLOTLY_DARK, **kwargs)
    st.plotly_chart(fig, use_container_width=True)

def section(title: str, sub: str = ""):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if sub: st.markdown(f'<div class="section-sub">{sub}</div>', unsafe_allow_html=True)

def render_header():
    now = datetime.utcnow().strftime("%Y-%m-%d  %H:%M UTC")
    st.markdown(f"""
    <div class="apex-header">
        <div>
            <div class="apex-logo">APEX<span>.</span>MI</div>
            <div class="apex-tagline">Institutional Market Intelligence Platform</div>
        </div>
        <div class="apex-time">🟢 LIVE &nbsp;·&nbsp; {now}</div>
    </div>""", unsafe_allow_html=True)

def render_ticker_strip(overview: dict):
    if not overview: return
    items = ""
    for name, d in overview.items():
        chg = d.get("change", 0)
        cls = "ticker-up" if chg >= 0 else "ticker-down"
        arrow = "▲" if chg >= 0 else "▼"
        p = d.get("price", 0)
        pstr = f"${p:,.0f}" if p > 1000 else f"${p:,.2f}"
        items += f'<span class="ticker-item"><span class="ticker-name">{name}</span><span class="{cls}">{pstr} {arrow}{abs(chg):.2f}%</span></span>'
    st.markdown(f'<div class="ticker-strip">{items}</div>', unsafe_allow_html=True)

def render_auto_refresh_control():
    col1, col2, col3 = st.columns([2,2,4])
    with col1:
        enabled = st.checkbox("🔄 Auto-Refresh", value=st.session_state.get("auto_refresh", False))
        st.session_state["auto_refresh"] = enabled
    with col2:
        interval = st.selectbox("Interval", [30, 60, 120, 300], index=1,
                                 format_func=lambda x: f"{x}s", key="refresh_interval")
    with col3:
        if enabled:
            last = st.session_state.get("last_refresh")
            count = st.session_state.get("refresh_count", 0)
            last_str = last.strftime("%H:%M:%S") if last else "never"
            st.markdown(f'<div class="refresh-badge"><div class="refresh-dot"></div>LIVE · refreshed {last_str} · #{count}</div>',
                        unsafe_allow_html=True)
    if enabled:
        time.sleep(interval)
        st.session_state["last_refresh"] = datetime.utcnow()
        st.session_state["refresh_count"] = st.session_state.get("refresh_count", 0) + 1
        fetch_market_overview.clear()
        st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# 4-PANEL CHART
# ──────────────────────────────────────────────────────────────────────────────
def render_full_chart(ticker: str, hist: pd.DataFrame):
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03, row_heights=[0.50,0.18,0.18,0.14],
                        subplot_titles=(f"{ticker} — Price · EMAs · Bollinger Bands",
                                        "MACD","RSI (14)","Volume"))
    fig.add_trace(go.Candlestick(x=hist.index,
        open=hist["Open"],high=hist["High"],low=hist["Low"],close=hist["Close"],
        name="Price", increasing_line_color="#34d399", decreasing_line_color="#f87171",
        increasing_fillcolor="#052e16", decreasing_fillcolor="#2d0a0a"), row=1,col=1)
    for col,color,name in [("EMA_9","#38bdf8","EMA 9"),("EMA_21","#fb923c","EMA 21"),
                            ("EMA_50","#a78bfa","EMA 50"),("VWAP","#f472b6","VWAP")]:
        fig.add_trace(go.Scatter(x=hist.index,y=hist[col],
            line=dict(color=color,width=1.5),name=name),row=1,col=1)
    fig.add_trace(go.Scatter(x=hist.index,y=hist["BB_Up"],
        line=dict(color="rgba(56,189,248,0.35)",width=1),name="BB Up"),row=1,col=1)
    fig.add_trace(go.Scatter(x=hist.index,y=hist["BB_Lo"],
        fill="tonexty",fillcolor="rgba(56,189,248,0.04)",
        line=dict(color="rgba(56,189,248,0.35)",width=1),name="BB Lo"),row=1,col=1)
    bar_c = ["#34d399" if v>=0 else "#f87171" for v in hist["MACD_Hist"].fillna(0)]
    fig.add_trace(go.Bar(x=hist.index,y=hist["MACD_Hist"],marker_color=bar_c,name="MACD Hist"),row=2,col=1)
    fig.add_trace(go.Scatter(x=hist.index,y=hist["MACD"],line=dict(color="#38bdf8",width=1.5),name="MACD"),row=2,col=1)
    fig.add_trace(go.Scatter(x=hist.index,y=hist["MACD_Sig"],line=dict(color="#fb923c",width=1.5),name="Signal"),row=2,col=1)
    fig.add_trace(go.Scatter(x=hist.index,y=hist["RSI"],line=dict(color="#f472b6",width=1.5),name="RSI"),row=3,col=1)
    fig.add_hrect(y0=70,y1=100,fillcolor="rgba(248,113,113,0.08)",line_width=0,row=3,col=1)
    fig.add_hrect(y0=0,y1=30,fillcolor="rgba(52,211,153,0.08)",line_width=0,row=3,col=1)
    fig.add_hline(y=70,line_dash="dot",line_color="rgba(248,113,113,0.5)",row=3,col=1)
    fig.add_hline(y=30,line_dash="dot",line_color="rgba(52,211,153,0.5)",row=3,col=1)
    vc = ["#34d399" if c>=o else "#f87171" for c,o in zip(hist["Close"],hist["Open"])]
    fig.add_trace(go.Bar(x=hist.index,y=hist["Volume"],marker_color=vc,name="Volume",opacity=0.7),row=4,col=1)
    fig.add_trace(go.Scatter(x=hist.index,y=hist["VolMA20"],
        line=dict(color="white",width=1,dash="dot"),name="Vol MA20"),row=4,col=1)
    fig.update_layout(**PLOTLY_DARK, height=850, xaxis_rangeslider_visible=False,
                      legend=dict(orientation="h",y=1.02,x=0,font_size=10),
                      margin=dict(l=10,r=10,t=60,b=10))
    st.plotly_chart(fig, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# BACKTESTING ENGINE
# ──────────────────────────────────────────────────────────────────────────────
def backtest_strategy(hist: pd.DataFrame, strategy: str, initial_capital: float = 10_000.0) -> dict:
    """
    Vectorised backtest of several EMA/RSI/MACD strategies.
    Returns metrics dict + equity curve + trade log.
    """
    h = hist.copy()
    h = compute_technicals(h)
    h = h.dropna(subset=["EMA_9","EMA_21","RSI","MACD","MACD_Sig"]).reset_index()

    # ── Generate raw signals ────────────────────────────────────
    if strategy == "EMA Crossover (9/21)":
        h["entry"] = (h["EMA_9"] > h["EMA_21"]) & (h["EMA_9"].shift(1) <= h["EMA_21"].shift(1))
        h["exit"]  = (h["EMA_9"] < h["EMA_21"]) & (h["EMA_9"].shift(1) >= h["EMA_21"].shift(1))

    elif strategy == "RSI Mean Reversion":
        h["entry"] = (h["RSI"] < 30) & (h["RSI"].shift(1) >= 30)
        h["exit"]  = (h["RSI"] > 70) & (h["RSI"].shift(1) <= 70)

    elif strategy == "MACD Signal Cross":
        h["entry"] = (h["MACD"] > h["MACD_Sig"]) & (h["MACD"].shift(1) <= h["MACD_Sig"].shift(1))
        h["exit"]  = (h["MACD"] < h["MACD_Sig"]) & (h["MACD"].shift(1) >= h["MACD_Sig"].shift(1))

    elif strategy == "EMA + RSI Confluence":
        h["entry"] = (h["EMA_9"] > h["EMA_21"]) & (h["RSI"] > 50) & (h["RSI"] < 65)
        h["exit"]  = (h["EMA_9"] < h["EMA_21"]) | (h["RSI"] > 75)

    elif strategy == "Bollinger Bounce":
        h["entry"] = h["Close"] < h["BB_Lo"]
        h["exit"]  = h["Close"] > h["BB_Mid"]

    elif strategy == "Triple EMA Trend (9/21/50)":
        h["entry"] = (h["EMA_9"] > h["EMA_21"]) & (h["EMA_21"] > h["EMA_50"]) & \
                     (~((h["EMA_9"].shift(1) > h["EMA_21"].shift(1)) & (h["EMA_21"].shift(1) > h["EMA_50"].shift(1))))
        h["exit"]  = (h["EMA_9"] < h["EMA_21"]) | (h["EMA_21"] < h["EMA_50"])

    else:
        return {}

    # ── Simulate trades ─────────────────────────────────────────
    capital   = initial_capital
    position  = 0.0          # shares held
    entry_px  = 0.0
    equity    = []
    trades    = []
    in_trade  = False

    for _, row in h.iterrows():
        price = float(row["Close"])
        date  = row.get("Date", row.get("Datetime", pd.NaT))

        if not in_trade and row["entry"]:
            shares   = capital / price
            position = shares
            entry_px = price
            in_trade = True
            trades.append({"Date":date,"Action":"BUY","Price":price,"Shares":round(shares,4),"PnL":0})

        elif in_trade and row["exit"]:
            pnl      = (price - entry_px) * position
            capital += pnl
            trades.append({"Date":date,"Action":"SELL","Price":price,
                           "Shares":round(position,4),"PnL":round(pnl,2)})
            position = 0.; in_trade = False

        cur_val = capital + (position * price if in_trade else 0)
        equity.append({"Date":date,"Equity":cur_val})

    if in_trade and position > 0:
        last_price = float(h["Close"].iloc[-1])
        pnl = (last_price - entry_px) * position
        capital += pnl
        trades.append({"Date":h.iloc[-1].get("Date",pd.NaT),"Action":"SELL (EOD)",
                       "Price":last_price,"Shares":round(position,4),"PnL":round(pnl,2)})

    # Buy & Hold benchmark
    bh_return = float(h["Close"].iloc[-1] / h["Close"].iloc[0] - 1) * 100

    # ── Metrics ─────────────────────────────────────────────────
    total_return = (capital / initial_capital - 1) * 100
    trade_df     = pd.DataFrame(trades)
    sell_trades  = trade_df[trade_df["Action"].str.startswith("SELL")] if not trade_df.empty else pd.DataFrame()
    n_trades     = len(sell_trades)
    n_wins       = int((sell_trades["PnL"] > 0).sum()) if not sell_trades.empty else 0
    win_rate     = n_wins / n_trades * 100 if n_trades > 0 else 0.
    avg_win      = float(sell_trades[sell_trades["PnL"]>0]["PnL"].mean()) if n_wins > 0 else 0.
    avg_loss     = float(sell_trades[sell_trades["PnL"]<=0]["PnL"].mean()) if n_trades-n_wins>0 else 0.
    profit_factor= abs(avg_win/avg_loss) if avg_loss!=0 else float("inf")
    equity_s     = pd.Series([e["Equity"] for e in equity])
    peak         = equity_s.cummax()
    drawdown     = (equity_s - peak) / peak * 100
    max_dd       = float(drawdown.min())

    # Sharpe (daily returns, annualised)
    eq_series    = equity_s.pct_change().dropna()
    sharpe       = float(eq_series.mean() / eq_series.std() * np.sqrt(252)) if eq_series.std()>0 else 0.

    return {
        "total_return":   round(total_return, 2),
        "bh_return":      round(bh_return, 2),
        "alpha":          round(total_return - bh_return, 2),
        "n_trades":       n_trades,
        "win_rate":       round(win_rate, 1),
        "profit_factor":  round(profit_factor, 2),
        "max_drawdown":   round(max_dd, 2),
        "sharpe":         round(sharpe, 2),
        "final_capital":  round(capital, 2),
        "equity_curve":   equity,
        "trade_log":      trades,
        "strategy":       strategy,
    }

def render_backtest_page():
    section("Strategy Backtester", "test signal quality against real historical data")

    col_t, col_s, col_p, col_d = st.columns(4)
    with col_t: bt_ticker = st.text_input("Ticker", "NVDA", key="bt_tick").strip().upper()
    with col_s:
        strategy = st.selectbox("Strategy", [
            "EMA Crossover (9/21)",
            "RSI Mean Reversion",
            "MACD Signal Cross",
            "EMA + RSI Confluence",
            "Bollinger Bounce",
            "Triple EMA Trend (9/21/50)",
        ])
    with col_p: period = st.selectbox("Period", ["1y","2y","3y","5y"], index=1)
    with col_d: capital = st.number_input("Starting Capital $", value=10000, step=1000)

    run_bt = st.button("▶  Run Backtest", type="primary")

    if not run_bt: return

    with st.spinner(f"Running {strategy} on {bt_ticker} ({period})…"):
        stk  = yf.Ticker(bt_ticker)
        hist = stk.history(period=period)
        if hist.empty:
            st.error("No data returned."); return
        res = backtest_strategy(hist, strategy, float(capital))

    if not res:
        st.error("Backtest failed."); return

    # ── KPI row ────────────────────────────────────────────────
    st.markdown("")
    k1,k2,k3,k4,k5,k6,k7,k8 = st.columns(8)
    def bt_kpi(col, label, val, good_positive=True):
        is_num = isinstance(val, (int,float))
        color = ""
        if is_num:
            color = "#34d399" if (val>0)==good_positive else "#f87171"
        col.markdown(f"""<div class="bt-stat">
            <div class="bt-stat-val" style="color:{color};">{val}{'%' if isinstance(val,float) and 'Capital' not in label else ''}</div>
            <div class="bt-stat-lbl">{label}</div></div>""", unsafe_allow_html=True)

    bt_kpi(k1,"Strategy Return",  f"{res['total_return']:+.1f}%")
    bt_kpi(k2,"Buy & Hold",       f"{res['bh_return']:+.1f}%")
    bt_kpi(k3,"Alpha vs B&H",     f"{res['alpha']:+.1f}%")
    bt_kpi(k4,"Win Rate",         f"{res['win_rate']:.1f}%")
    bt_kpi(k5,"# Trades",         str(res['n_trades']))
    bt_kpi(k6,"Profit Factor",    res['profit_factor'])
    bt_kpi(k7,"Max Drawdown",     f"{res['max_drawdown']:.1f}%", good_positive=False)
    bt_kpi(k8,"Sharpe Ratio",     res['sharpe'])

    st.markdown("")

    # ── Equity curve ───────────────────────────────────────────
    if res["equity_curve"]:
        eq_df = pd.DataFrame(res["equity_curve"])
        # also plot buy-and-hold
        hist2 = hist.copy().reset_index()
        bh_eq = capital * hist2["Close"] / float(hist2["Close"].iloc[0])

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=eq_df["Date"], y=eq_df["Equity"],
            line=dict(color="#38bdf8", width=2),
            fill="tozeroy", fillcolor="rgba(56,189,248,0.06)",
            name=f"{strategy}",
        ))
        fig.add_trace(go.Scatter(
            x=hist2["Date"] if "Date" in hist2 else hist2.index,
            y=bh_eq,
            line=dict(color="#64748b", width=1.5, dash="dot"),
            name="Buy & Hold",
        ))
        fig.add_hline(y=capital, line_dash="dash", line_color="#475569",
                      annotation_text="Start Capital")
        fig.update_layout(**PLOTLY_DARK, height=380,
                          title=f"{bt_ticker} — Equity Curve: {strategy} vs Buy & Hold",
                          yaxis_title="Portfolio Value ($)", margin=dict(l=10,r=10,t=50,b=10))
        st.plotly_chart(fig, use_container_width=True)

    # ── Drawdown chart ─────────────────────────────────────────
    if res["equity_curve"]:
        eq_s  = pd.Series([e["Equity"] for e in res["equity_curve"]])
        dd    = (eq_s - eq_s.cummax()) / eq_s.cummax() * 100
        dates = [e["Date"] for e in res["equity_curve"]]
        fig2  = go.Figure(go.Scatter(
            x=dates, y=dd,
            fill="tozeroy", fillcolor="rgba(248,113,113,0.1)",
            line=dict(color="#f87171", width=1.5), name="Drawdown %",
        ))
        fig2.update_layout(**PLOTLY_DARK, height=200,
                           title="Drawdown %",
                           yaxis_title="Drawdown %", margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(fig2, use_container_width=True)

    # ── Trade log ─────────────────────────────────────────────
    if res["trade_log"]:
        st.markdown("")
        section("Trade Log")
        tdf = pd.DataFrame(res["trade_log"])
        def hl_trade(val):
            if isinstance(val, (int,float)):
                return f"color:{'#34d399' if val>0 else '#f87171'};font-weight:600"
            return ""
        st.dataframe(
            tdf.style.map(hl_trade, subset=["PnL"] if "PnL" in tdf.columns else [])
               .format({"Price":"${:.2f}","PnL":"${:+.2f}"}),
            use_container_width=True, height=280,
        )

    # ── AI Strategy Commentary ─────────────────────────────────
    st.markdown("")
    section("AI Strategy Analysis")
    if st.button("Get AI Commentary", key="bt_ai"):
        prompt = f"""
You are a quantitative analyst reviewing a backtest result.

Strategy: {res['strategy']}
Ticker: {bt_ticker}, Period: {period}

Results:
- Strategy Return: {res['total_return']:+.1f}%
- Buy & Hold: {res['bh_return']:+.1f}%
- Alpha: {res['alpha']:+.1f}%
- Win Rate: {res['win_rate']}% over {res['n_trades']} trades
- Profit Factor: {res['profit_factor']}
- Max Drawdown: {res['max_drawdown']}%
- Sharpe Ratio: {res['sharpe']}
- Final Capital: ${res['final_capital']:,.2f} from ${capital:,.2f}

Provide:
1. **Performance Verdict**: Is this strategy viable? Compare to B&H.
2. **Strength Analysis**: What market conditions make this strategy excel?
3. **Weakness Analysis**: When does it fail? What are the key risk periods?
4. **Optimisation Suggestions**: 3 specific parameter changes that could improve it.
5. **Risk Warning**: Is the drawdown or win rate acceptable? Position sizing advice.
6. **Regime Dependency**: Does this work in trending vs ranging markets? How to filter?

Be quantitative and specific. Reference the actual numbers.
"""
        with st.spinner("Generating analysis…"):
            st.markdown(call_gemini(prompt))

# ──────────────────────────────────────────────────────────────────────────────
# OPTIONS FLOW
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=900)
def fetch_options_flow(ticker: str) -> dict:
    try:
        stk  = yf.Ticker(ticker)
        exps = stk.options
        if not exps: return {"error": "No options data"}
        all_c, all_p = [], []
        for exp in exps[:4]:
            try:
                chain = stk.option_chain(exp)
                c,p   = chain.calls.copy(), chain.puts.copy()
                c["expiry"] = p["expiry"] = exp
                all_c.append(c); all_p.append(p)
            except Exception: continue
        if not all_c: return {"error": "Chain load failed"}
        cdf = pd.concat(all_c, ignore_index=True)
        pdf = pd.concat(all_p, ignore_index=True)
        for df in [cdf,pdf]:
            for col in ["volume","openInterest","impliedVolatility","lastPrice"]:
                df[col] = pd.to_numeric(df.get(col,0), errors="coerce").fillna(0)
        tcv = cdf["volume"].sum(); tpv = pdf["volume"].sum()
        tco = cdf["openInterest"].sum(); tpo = pdf["openInterest"].sum()
        pcr_vol = tpv/tcv if tcv>0 else float("nan")
        pcr_oi  = tpo/tco if tco>0 else float("nan")
        cdf["unusual"] = (cdf["volume"]>2*cdf["openInterest"]) & (cdf["volume"]>500)
        pdf["unusual"] = (pdf["volume"]>2*pdf["openInterest"]) & (pdf["volume"]>500)
        uc = cdf[cdf["unusual"]].nlargest(10,"volume")[["expiry","strike","lastPrice","volume","openInterest","impliedVolatility"]]
        up = pdf[pdf["unusual"]].nlargest(10,"volume")[["expiry","strike","lastPrice","volume","openInterest","impliedVolatility"]]
        # Max pain
        try:
            near = stk.option_chain(exps[0])
            strikes = sorted(set(near.calls["strike"].tolist()+near.puts["strike"].tolist()))
            mp, mv = float("nan"), float("inf")
            for s in strikes:
                v = ((near.calls["strike"]-s).clip(lower=0)*near.calls["openInterest"]).sum() + \
                    ((s-near.puts["strike"]).clip(lower=0)*near.puts["openInterest"]).sum()
                if v < mv: mv,mp = v,s
        except Exception: mp = float("nan")
        pcr_sent = ("🚀 Extreme Bullish" if not pd.isna(pcr_vol) and pcr_vol<0.6 else
                    "🐂 Bullish" if not pd.isna(pcr_vol) and pcr_vol<0.9 else
                    "😐 Neutral" if not pd.isna(pcr_vol) and pcr_vol<1.1 else
                    "🐻 Bearish" if not pd.isna(pcr_vol) and pcr_vol<1.3 else
                    "💀 Extreme Bearish")
        return {"pcr_vol":round(pcr_vol,3),"pcr_oi":round(pcr_oi,3),"tcv":int(tcv),"tpv":int(tpv),
                "tco":int(tco),"tpo":int(tpo),"iv":round(cdf["impliedVolatility"].median()*100,1),
                "max_pain":mp,"sentiment":pcr_sent,"uc":uc,"up":up,"exps":list(exps[:5])}
    except Exception as e: return {"error":str(e)}

def render_options_page():
    section("Options Flow Scanner", "unusual activity · put/call ratio · max pain · smart money")

    c1,c2 = st.columns([3,1])
    with c1: ot = st.text_input("Ticker:", "NVDA", key="opt_in").strip().upper()
    with c2: st.markdown("<br>",unsafe_allow_html=True); run = st.button("🔍 Scan",type="primary",key="opt_run")

    if not ot: st.info("Enter a ticker above."); return

    with st.spinner(f"Loading {ot} options chain…"):
        data = fetch_options_flow(ot)

    if "error" in data: st.error(data["error"]); return

    k1,k2,k3,k4,k5,k6 = st.columns(6)
    def ok(l,v,h=""): metric_card(l,str(v),h)
    k1.markdown('<div class="metric-card"><div class="metric-label">P/C RATIO (VOL)</div>'
               f'<div class="metric-value">{data["pcr_vol"]}</div></div>',unsafe_allow_html=True)
    k2.markdown('<div class="metric-card"><div class="metric-label">P/C RATIO (OI)</div>'
               f'<div class="metric-value">{data["pcr_oi"]}</div></div>',unsafe_allow_html=True)
    k3.markdown(f'<div class="metric-card"><div class="metric-label">CALL VOL</div>'
               f'<div class="metric-value">{data["tcv"]:,}</div></div>',unsafe_allow_html=True)
    k4.markdown(f'<div class="metric-card"><div class="metric-label">PUT VOL</div>'
               f'<div class="metric-value">{data["tpv"]:,}</div></div>',unsafe_allow_html=True)
    k5.markdown(f'<div class="metric-card"><div class="metric-label">MEDIAN IV</div>'
               f'<div class="metric-value">{data["iv"]}%</div></div>',unsafe_allow_html=True)
    mp = data["max_pain"]; mp_str = f"${mp:.2f}" if not pd.isna(mp) else "N/A"
    k6.markdown(f'<div class="metric-card"><div class="metric-label">MAX PAIN</div>'
               f'<div class="metric-value">{mp_str}</div></div>',unsafe_allow_html=True)

    st.markdown(f"**Options Sentiment:** {data['sentiment']}")
    st.divider()

    pcr = data["pcr_vol"]
    if isinstance(pcr,(int,float)) and not pd.isna(pcr):
        col_g, col_bar = st.columns(2)
        with col_g:
            fig = go.Figure(go.Indicator(mode="gauge+number+delta",value=pcr,
                title={"text":"Put/Call Volume Ratio","font":{"size":13,"color":"#94a3b8"}},
                delta={"reference":1.0,"valueformat":".3f"},
                gauge={"axis":{"range":[0,2.5],"tickcolor":"#475569"},
                       "bar":{"color":"#38bdf8"},
                       "bgcolor":"#07111f",
                       "steps":[{"range":[0,0.6],"color":"#052e16"},
                                 {"range":[0.6,0.9],"color":"#14532d"},
                                 {"range":[0.9,1.1],"color":"#1c1a03"},
                                 {"range":[1.1,1.5],"color":"#431407"},
                                 {"range":[1.5,2.5],"color":"#2d0a0a"}],
                       "threshold":{"line":{"color":"white","width":3},"value":1.0}}))
            fig.update_layout(**PLOTLY_DARK,height=280,margin=dict(t=40,b=10,l=20,r=20))
            st.plotly_chart(fig,use_container_width=True)
        with col_bar:
            fig2 = go.Figure([
                go.Bar(name="Call OI",x=["OI"],y=[data["tco"]],marker_color="#34d399"),
                go.Bar(name="Put OI",x=["OI"],y=[data["tpo"]],marker_color="#f87171"),
                go.Bar(name="Call Vol",x=["Volume"],y=[data["tcv"]],marker_color="#4ade80"),
                go.Bar(name="Put Vol",x=["Volume"],y=[data["tpv"]],marker_color="#fca5a5"),
            ])
            fig2.update_layout(**PLOTLY_DARK,barmode="group",height=280,
                               margin=dict(t=10,b=10),title="Call vs Put OI & Volume")
            st.plotly_chart(fig2,use_container_width=True)

    st.divider()
    ca, pa = st.columns(2)
    with ca:
        section("🟢 Unusual CALL Activity")
        uc = data["uc"]
        if uc is not None and not uc.empty:
            uc2 = uc.copy(); uc2["impliedVolatility"] = (uc2["impliedVolatility"]*100).round(1).astype(str)+"%"
            uc2.columns=["Expiry","Strike","Last","Volume","OI","IV"]
            st.dataframe(uc2.style.format({"Strike":"${:.2f}","Last":"${:.2f}"}),use_container_width=True)
            st.caption("Vol > 2× OI — potential directional sweep")
        else: st.info("No unusual calls.")
    with pa:
        section("🔴 Unusual PUT Activity")
        up = data["up"]
        if up is not None and not up.empty:
            up2 = up.copy(); up2["impliedVolatility"] = (up2["impliedVolatility"]*100).round(1).astype(str)+"%"
            up2.columns=["Expiry","Strike","Last","Volume","OI","IV"]
            st.dataframe(up2.style.format({"Strike":"${:.2f}","Last":"${:.2f}"}),use_container_width=True)
            st.caption("Vol > 2× OI — potential hedge or directional put")
        else: st.info("No unusual puts.")

    st.divider()
    section(f"Full Chain — {data['exps'][0]}")
    try:
        chain = yf.Ticker(ot).option_chain(data["exps"][0])
        for name, df in [("Calls",chain.calls),("Puts",chain.puts)]:
            section(name)
            df2 = df[["strike","lastPrice","bid","ask","volume","openInterest","impliedVolatility"]].copy()
            df2["impliedVolatility"] = (df2["impliedVolatility"]*100).round(1)
            df2["volume"] = df2["volume"].fillna(0).astype(int)
            df2["openInterest"] = df2["openInterest"].fillna(0).astype(int)
            st.dataframe(df2.sort_values("volume",ascending=False).head(20)
                         .style.format({"strike":"${:.2f}","lastPrice":"${:.2f}",
                                        "bid":"${:.2f}","ask":"${:.2f}","impliedVolatility":"{:.1f}%"}),
                         use_container_width=True)
    except Exception as e: st.warning(f"Chain error: {e}")

# ──────────────────────────────────────────────────────────────────────────────
# ALERT ENGINE
# ──────────────────────────────────────────────────────────────────────────────
ALERT_CONDITIONS = {
    "🚀 RSI Oversold Bounce":     lambda r: r.get("RSI",50)<32,
    "⚠️ RSI Overbought":          lambda r: r.get("RSI",50)>70,
    "📈 Bullish MACD Cross":      lambda r: r.get("MACD",0)>0 and abs(r.get("MACD",0))<0.5,
    "🔔 Volume Spike (>2x)":      lambda r: r.get("Vol Spike",1)>2.0,
    "💥 Volume Spike (>3x)":      lambda r: r.get("Vol Spike",1)>3.0,
    "🟢 Strong Buy Signal":       lambda r: r.get("Signal") in ("STRONG BUY","BUY"),
    "🔴 Strong Sell Signal":      lambda r: r.get("Signal") in ("STRONG SELL","SELL"),
    "📐 Near Bollinger Lower":    lambda r: (r.get("Price",0)-r.get("BB Lo",0))/max(r.get("Price",1),1)<0.01,
    "🎯 Near Support":            lambda r: abs(r.get("Price",0)-r.get("Support",0))/max(r.get("Price",1),1)<0.015,
    "🏔️ Near Resistance":        lambda r: abs(r.get("Resistance",0)-r.get("Price",0))/max(r.get("Price",1),1)<0.015,
    "📅 Earnings Soon":           lambda r: r.get("EarningsSoon")=="⚠️",
    "💎 High Conviction (5/5)":   lambda r: r.get("Score",0)==5,
    "📉 Full EMA Downtrend":      lambda r: r.get("EMA 9",0)<r.get("EMA 21",999)<r.get("EMA 50",999),
    "📊 High Short Interest":     lambda r: isinstance(r.get("ShortRatio"),float) and r.get("ShortRatio",0)>5,
    "⭐ Positive Analyst Upside": lambda r: isinstance(r.get("Upside%"),float) and r.get("Upside%",0)>15,
}

def scan_alerts(df: pd.DataFrame, active: list) -> pd.DataFrame:
    if df.empty or not active: return pd.DataFrame()
    fired = []
    for _, row in df.iterrows():
        rd = row.to_dict()
        hits = [c for c in active if c in ALERT_CONDITIONS and ALERT_CONDITIONS[c](rd)]
        if hits:
            fired.append({"Ticker":row.get("Ticker",""),"Company":row.get("Company",""),
                          "Price":row.get("Price",np.nan),"Signal":row.get("Signal",""),
                          "Score":row.get("Score",0),"RSI":row.get("RSI",np.nan),
                          "Vol Spike":row.get("Vol Spike",np.nan),"1W%":row.get("1W%",np.nan),
                          "Alerts":" | ".join(hits),"#Alerts":len(hits)})
    if not fired: return pd.DataFrame()
    return pd.DataFrame(fired).sort_values("#Alerts",ascending=False)

def render_alerts_page():
    section("AI Trade Alert Engine", "configurable scanner · real-time conditions · AI commentary")

    df = st.session_state.get("_cached_screener")
    if df is None or df.empty:
        st.warning("⚠️ Run the **Technical Screener** page first to load ticker data.")
        if st.button("Load Default Tickers Now", type="primary"):
            with st.spinner("Loading…"):
                df = fetch_stock_data_all(tuple(sorted(DEFAULT_TICKERS)))
        else: return

    render_auto_refresh_control()
    st.divider()

    all_conds = list(ALERT_CONDITIONS.keys())
    defaults  = [c for c in all_conds if any(k in c for k in ["RSI Oversold","Volume Spike","Strong Buy","Earnings","High Conviction","Upside"])]
    active    = st.multiselect("Active conditions:", all_conds, default=defaults)

    c1,c2 = st.columns([2,4])
    with c1: run = st.button("🔍 Run Scan",type="primary")
    with c2: st.caption(f"Scanning {len(df)} tickers · {len(active)} conditions active")

    if not run and not st.session_state.get("alerts_run"): return
    st.session_state["alerts_run"] = True
    alerts = scan_alerts(df, active)

    if alerts.empty:
        st.success("✅ No alerts triggered with current conditions."); return

    a1,a2,a3,a4 = st.columns(4)
    a1.markdown(f'<div class="metric-card"><div class="metric-label">ALERTS FIRED</div><div class="metric-value">{len(alerts)}</div></div>',unsafe_allow_html=True)
    a2.markdown(f'<div class="metric-card"><div class="metric-label">BUY-BIASED</div><div class="metric-value">{alerts[alerts["Signal"].isin(["BUY","STRONG BUY"])].shape[0]}</div></div>',unsafe_allow_html=True)
    a3.markdown(f'<div class="metric-card"><div class="metric-label">AVG CONFLUENCE</div><div class="metric-value">{alerts["Score"].mean():.1f}/5</div></div>',unsafe_allow_html=True)
    a4.markdown(f'<div class="metric-card"><div class="metric-label">MAX CONDITIONS HIT</div><div class="metric-value">{alerts["#Alerts"].max()}</div></div>',unsafe_allow_html=True)

    st.divider()

    # Render as styled alert cards
    for _, row in alerts.head(20).iterrows():
        sig = row.get("Signal","")
        card_class = "bullish" if "BUY" in sig else ("bearish" if "SELL" in sig else "warning")
        price_str = f"${row['Price']:.2f}" if not pd.isna(row.get("Price",np.nan)) else "N/A"
        rsi_str   = f"{row['RSI']:.1f}" if not pd.isna(row.get("RSI",np.nan)) else "—"
        vs_str    = f"{row['Vol Spike']:.2f}x" if not pd.isna(row.get("Vol Spike",np.nan)) else "—"
        st.markdown(f"""
        <div class="alert-card {card_class}">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span class="alert-ticker">{row['Ticker']}</span>
                <span style="color:#94a3b8;font-size:0.8rem;">{row.get('Company','')}</span>
                {signal_badge(sig)}
                <span style="font-family:'JetBrains Mono',monospace;font-size:0.85rem;color:#f1f5f9;">{price_str}</span>
                <span style="font-family:'JetBrains Mono',monospace;font-size:0.78rem;color:#64748b;">RSI {rsi_str} · Vol {vs_str} · {row.get('#Alerts',0)} alerts</span>
            </div>
            <div class="alert-conditions">{row.get('Alerts','')}</div>
        </div>""", unsafe_allow_html=True)

    st.divider()
    section("🧠 AI Alert Commentary")
    if st.button("Generate AI Trade Commentary", type="primary", key="al_ai"):
        top = alerts.head(10).to_string(index=False)
        prompt = f"""
You are an algorithmic trading desk's AI commentary system.
These stocks triggered automated technical alerts right now:

{top}

For each ticker, provide 2–3 sentences:
1. Why the alert is significant
2. Specific trade setup: exact entry trigger, stop loss level, target price
3. Risk/reward ratio and position sizing note

Format: **$TICKER** — [commentary]
Be precise with dollar levels. Flag any conflicting signals.
"""
        with st.spinner("Generating…"):
            result = call_gemini(prompt)
            result = re.sub(r'\$([A-Z]{1,5})\b',r'[\1](https://finance.yahoo.com/quote/\1)',result)
            st.markdown(result)

# ──────────────────────────────────────────────────────────────────────────────
# PORTFOLIO TRACKER
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_prices(tickers: tuple) -> dict:
    out = {}
    for t in tickers:
        try:
            h = yf.Ticker(t).history(period="2d")
            if len(h)>=2:
                out[t]={"price":float(h["Close"].iloc[-1]),"prev":float(h["Close"].iloc[-2])}
            elif len(h)==1:
                out[t]={"price":float(h["Close"].iloc[-1]),"prev":float(h["Close"].iloc[-1])}
        except Exception: pass
    return out

def render_portfolio_page():
    section("Portfolio Tracker", "live p&l · allocation analytics · ai portfolio review")

    if "portfolio" not in st.session_state: st.session_state.portfolio = []

    render_auto_refresh_control()
    st.divider()

    with st.expander("➕ Add Position", expanded=len(st.session_state.portfolio)==0):
        c1,c2,c3,c4,c5 = st.columns([2,2,2,2,1])
        with c1: nt = st.text_input("Ticker","AAPL",key="pt").strip().upper()
        with c2: ns = st.number_input("Shares",min_value=0.001,value=10.,step=1.,key="ps")
        with c3: nc = st.number_input("Cost/Share $",min_value=0.01,value=150.,step=0.01,key="pc")
        with c4: nd = st.date_input("Entry Date",key="pd")
        with c5:
            st.markdown("<br>",unsafe_allow_html=True)
            if st.button("Add",type="primary",key="padd"):
                if any(p["ticker"]==nt for p in st.session_state.portfolio):
                    st.warning(f"{nt} already added.")
                else:
                    st.session_state.portfolio.append({"ticker":nt,"shares":ns,"cost":nc,"date":str(nd)})
                    st.success(f"Added {nt}"); st.rerun()

    if not st.session_state.portfolio:
        st.info("Add your first position above."); return

    tickers = tuple(p["ticker"] for p in st.session_state.portfolio)
    with st.spinner("Fetching live prices…"):
        prices = get_prices(tickers)

    rows, tot_inv, tot_val = [], 0., 0.
    for p in st.session_state.portfolio:
        t  = p["ticker"]
        pd_ = prices.get(t,{})
        cur = pd_.get("price",np.nan)
        prv = pd_.get("prev",cur)
        inv = p["shares"]*p["cost"]
        val = p["shares"]*cur if not pd.isna(cur) else np.nan
        unr = val-inv if not pd.isna(val) else np.nan
        tot_inv += inv; tot_val += val if not pd.isna(val) else 0
        rows.append({
            "Ticker":t,"Shares":p["shares"],"Cost":p["cost"],"Price":cur,
            "Invested":inv,"Value":val,"P&L":unr,
            "Return%":(unr/inv*100) if inv>0 and not pd.isna(unr) else np.nan,
            "Day$":(cur-prv)*p["shares"] if not pd.isna(cur) else np.nan,
            "Day%":(cur/prv-1)*100 if prv and not pd.isna(cur) else np.nan,
        })

    df_p  = pd.DataFrame(rows)
    tot_pnl = tot_val - tot_inv
    tot_pct = (tot_pnl/tot_inv*100) if tot_inv>0 else 0.

    # KPIs
    k1,k2,k3,k4,k5 = st.columns(5)
    k1.markdown(f'<div class="metric-card"><div class="metric-label">INVESTED</div><div class="metric-value">${tot_inv:,.0f}</div></div>',unsafe_allow_html=True)
    pnl_c="#34d399" if tot_pnl>=0 else "#f87171"
    k2.markdown(f'<div class="metric-card"><div class="metric-label">PORTFOLIO VALUE</div><div class="metric-value">${tot_val:,.0f}</div><div class="metric-delta" style="color:{pnl_c};">${tot_pnl:+,.0f} ({tot_pct:+.2f}%)</div></div>',unsafe_allow_html=True)
    wins = int((df_p["Return%"]>0).sum())
    k3.markdown(f'<div class="metric-card"><div class="metric-label">WINNERS / LOSERS</div><div class="metric-value">{wins} / {len(df_p)-wins}</div></div>',unsafe_allow_html=True)
    if not df_p.empty and "Return%" in df_p:
        best = df_p.nlargest(1,"Return%").iloc[0]
        k4.markdown(f'<div class="metric-card"><div class="metric-label">BEST POSITION</div><div class="metric-value" style="color:#34d399;">{best["Ticker"]}</div><div class="metric-delta delta-up">{best["Return%"]:+.1f}%</div></div>',unsafe_allow_html=True)
        worst = df_p.nsmallest(1,"Return%").iloc[0]
        k5.markdown(f'<div class="metric-card"><div class="metric-label">WORST POSITION</div><div class="metric-value" style="color:#f87171;">{worst["Ticker"]}</div><div class="metric-delta delta-down">{worst["Return%"]:+.1f}%</div></div>',unsafe_allow_html=True)

    st.divider()

    def cpnl(v):
        if pd.isna(v): return ""
        return f"color:{'#34d399' if v>=0 else '#f87171'};font-weight:600"

    section("Position Details")
    styled = (df_p.style
              .map(cpnl,subset=["P&L","Return%","Day$","Day%"])
              .format({"Shares":"{:.3f}","Cost":"${:.2f}","Price":"${:.2f}",
                       "Invested":"${:,.2f}","Value":"${:,.2f}",
                       "P&L":"${:+,.2f}","Return%":"{:+.2f}%",
                       "Day$":"${:+,.2f}","Day%":"{:+.2f}%"}))
    st.dataframe(styled,use_container_width=True)

    rem = st.selectbox("Remove position:",["—"]+list(tickers))
    if st.button("🗑️ Remove") and rem!="—":
        st.session_state.portfolio=[p for p in st.session_state.portfolio if p["ticker"]!=rem]
        st.rerun()

    st.divider()

    # Charts
    cv,bv = st.columns(2)
    with cv:
        pie_d = df_p[df_p["Value"]>0][["Ticker","Value"]].dropna()
        if not pie_d.empty:
            fig = px.pie(pie_d,names="Ticker",values="Value",hole=0.45,
                         title="Allocation by Market Value",color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(**PLOTLY_DARK,height=340,margin=dict(t=40,b=10))
            st.plotly_chart(fig,use_container_width=True)
    with bv:
        ret_d = df_p[["Ticker","Return%"]].dropna().sort_values("Return%")
        if not ret_d.empty:
            fig2 = go.Figure(go.Bar(x=ret_d["Return%"],y=ret_d["Ticker"],orientation="h",
                marker_color=["#34d399" if v>=0 else "#f87171" for v in ret_d["Return%"]],
                text=[f"{v:+.1f}%" for v in ret_d["Return%"]],textposition="outside"))
            fig2.update_layout(**PLOTLY_DARK,title="Return % per Position",height=340,
                               margin=dict(t=40,b=10,l=10,r=70))
            st.plotly_chart(fig2,use_container_width=True)

    st.divider()
    section("🧠 AI Portfolio Review")
    if st.button("Analyse My Portfolio",type="primary",key="port_ai"):
        prompt = f"""
You are reviewing a client's equity portfolio.

Positions:
{df_p.to_string(index=False)}

Summary: Invested ${tot_inv:,.0f} · Value ${tot_val:,.0f} · Total Return {tot_pct:+.2f}%

Provide:
1. **Portfolio Health**: Concentration risk, sector exposure, diversification score (/10)
2. **Top Risks**: Which positions have the most downside and why?
3. **Rebalancing**: What to trim, hold, or add to?
4. **Hedging**: 2 specific hedges for current exposure (ETFs, puts, inverse ETFs)
5. **Actionable Next Step**: The single highest-priority action to take this week.

Use actual tickers and dollar amounts. Be decisive.
"""
        with st.spinner("Analysing…"): st.markdown(call_gemini(prompt))

# ──────────────────────────────────────────────────────────────────────────────
# NEWS & EARNINGS
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def fetch_news(ticker: str, n=20):
    items=[]
    url=f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    try:
        feed=feedparser.parse(url)
        for e in feed.entries[:n]:
            pub=None
            if hasattr(e,"published_parsed") and e.published_parsed:
                pub=datetime(*e.published_parsed[:6])
            src=e.get("source",{}).get("value","Yahoo Finance") if isinstance(e.get("source"),dict) else "Yahoo Finance"
            items.append({"title":e.get("title",""),"link":e.get("link",""),"published":pub,"source":src})
    except Exception as err: logger.warning("News %s: %s",ticker,err)
    return sorted(items,key=lambda x:x["published"] or datetime.min,reverse=True)

@st.cache_data(ttl=3600)
def build_earnings_calendar(tickers: tuple):
    rows=[]
    for t in tickers:
        try:
            info=yf.Ticker(t).info
            ts=info.get("earningsTimestamp") or info.get("earningsTimestampStart")
            if not ts: continue
            date=datetime.fromtimestamp(ts)
            days=(date-datetime.now()).days
            h=yf.Ticker(t).history(period="5d")
            price=float(h["Close"].iloc[-1]) if not h.empty else np.nan
            rows.append({"Ticker":t,"Company":info.get("shortName",t),
                         "Date":date.strftime("%Y-%m-%d"),"Days Away":days,"Price":price,
                         "EPS Est":info.get("epsForward","N/A"),
                         "Rating":info.get("recommendationKey","N/A").upper(),
                         "Status":("🔴 PAST" if days<0 else "⚡ THIS WEEK" if days<=7 else "📅 SOON" if days<=30 else "🗓️ LATER")})
        except Exception: pass
    return sorted(rows,key=lambda x:x["Days Away"])

def render_news_earnings_page():
    section("News Feed & Earnings Calendar","live headlines · ai sentiment · countdown calendar")

    t1,t2=st.tabs(["📰  News & Sentiment","📅  Earnings Calendar"])

    with t1:
        c1,c2=st.columns([3,1])
        with c1: nt=st.text_input("Ticker:","NVDA",key="news_t").strip().upper()
        with c2: st.markdown("<br>",unsafe_allow_html=True); st.button("📡 Refresh",key="news_ref")

        if nt:
            with st.spinner(f"Loading {nt} news…"):
                news=fetch_news(nt)
            if not news: st.warning("No news found."); return

            left,right=st.columns([2,3])
            with left:
                section("🧠 AI Sentiment")
                if st.button("Analyse Headlines",type="primary",key="news_ai"):
                    hdls="\n".join([f"- {n['title']} ({n['published'].strftime('%m/%d') if n.get('published') else 'N/A'})" for n in news[:12]])
                    prompt=f"""Analyse these ${nt} headlines for a trader:

{hdls}

Provide:
1. **Sentiment**: Bullish/Bearish/Neutral with score (-10 to +10)
2. **Key Catalysts**: Top 2-3 impactful stories
3. **Market Reaction Risk**: Could any headline move the price >3%? Direction?
4. **Narrative**: What story is building around this stock?
5. **Trader Takeaway**: One actionable insight for today.

Be concise and direct. Reference specific headlines."""
                    with st.spinner("Analysing…"): st.markdown(call_gemini(prompt))
                else:
                    st.info(f"{len(news)} headlines loaded. Click to analyse.")

            with right:
                section("Headlines")
                for item in news[:15]:
                    pub=item["published"].strftime("%b %d, %H:%M") if item.get("published") else "—"
                    st.markdown(f"""<div class="news-card">
<a class="news-title" href="{item['link']}" target="_blank">{item['title']}</a>
<div class="news-meta">{item['source']} · {pub}</div></div>""",unsafe_allow_html=True)

    with t2:
        section("Upcoming Earnings")
        port_ts=tuple(p["ticker"] for p in st.session_state.get("portfolio",[]))
        custom=st.text_input("Add tickers:",key="earn_c")
        extras=[t.strip().upper() for t in custom.split(",") if t.strip()]
        universe=tuple(sorted(set(list(DEFAULT_TICKERS)+list(port_ts)+extras)))

        with st.spinner(f"Building calendar for {len(universe)} tickers…"):
            cal=build_earnings_calendar(universe)

        if not cal: st.warning("No earnings data found."); return
        df_c=pd.DataFrame(cal)

        filt=st.radio("Show:",["All","⚡ This Week","📅 Next 30 Days","💼 Portfolio"],horizontal=True)
        if "This Week" in filt:    df_c=df_c[df_c["Days Away"].between(0,7)]
        elif "30 Days"  in filt:   df_c=df_c[df_c["Days Away"].between(0,30)]
        elif "Portfolio" in filt:  df_c=df_c[df_c["Ticker"].isin(port_ts)]

        if df_c.empty: st.info("No earnings in window."); return

        def hl_earn(row):
            if row["Status"]=="⚡ THIS WEEK": return ["background-color:#1a2744;color:white"]*len(row)
            if row["Status"]=="📅 SOON":      return ["background-color:#0a1f0a;color:white"]*len(row)
            return [""]*len(row)

        st.dataframe(df_c[["Ticker","Company","Date","Days Away","Status","Price","EPS Est","Rating"]]
                     .style.apply(hl_earn,axis=1)
                     .format({"Price":"${:.2f}","Days Away":"{:,.0f}d"}),
                     use_container_width=True)

        this_wk=df_c[df_c["Days Away"].between(0,7)]
        if not this_wk.empty:
            st.divider(); section("⚡ This Week")
            for _,row in this_wk.iterrows():
                d=int(row["Days Away"])
                urgency="earnings-chip urgent" if d<=2 else "earnings-chip soon"
                label="TODAY ⚡" if d==0 else f"in {d} day{'s' if d!=1 else ''}"
                st.markdown(f"""<div class="{urgency}">
<span style="font-family:'Syne',sans-serif;font-weight:800;color:#38bdf8;min-width:60px">{row['Ticker']}</span>
<span style="color:#e2e8f0">{row['Company']}</span>
<span style="margin-left:auto;color:#fbbf24;font-weight:600">{row['Date']} · {label}</span>
<span style="color:#64748b;font-family:'JetBrains Mono',monospace;font-size:0.78rem">EPS: {row['EPS Est']} · {row['Rating']}</span>
</div>""",unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# SCREENER PAGE
# ──────────────────────────────────────────────────────────────────────────────
def render_screener_page(show_only_buy,max_pe,min_div,custom_raw):
    section("Technical Stock Screener","ema · rsi · macd · bollinger · vwap · atr · multi-timeframe")

    scraped=extract_tickers_from_posts(st.session_state.get("ai_df")) if st.session_state.get("ai_df") is not None else []
    extra=[t.strip().upper() for t in custom_raw.split(",") if t.strip()]
    base=scraped if scraped else DEFAULT_TICKERS
    all_t=tuple(sorted(set(base+extra)))

    if scraped: st.success(f"✅ {len(scraped)} trending tickers from social scan")
    else: st.info("Using default ticker list — run AI Intelligence first to use trending tickers")

    with st.spinner(f"Computing indicators for {len(all_t)} tickers…"):
        df=fetch_stock_data_all(all_t)

    if df.empty: st.error("No data."); return

    filt=df.copy()
    pe_ok=(filt["Fwd PE"].isna())|(filt["Fwd PE"]<=0)|(filt["Fwd PE"]<=max_pe)
    filt=filt[pe_ok & (filt["DivYield%"]>=min_div)]
    if show_only_buy: filt=filt[filt["Signal"].isin(["BUY","STRONG BUY"])]

    # KPI row
    k1,k2,k3,k4,k5,k6=st.columns(6)
    k1.markdown(f'<div class="metric-card"><div class="metric-label">SCANNED</div><div class="metric-value">{len(df)}</div></div>',unsafe_allow_html=True)
    k2.markdown(f'<div class="metric-card"><div class="metric-label">STRONG BUY 🟢</div><div class="metric-value" style="color:#34d399;">{(df["Signal"]=="STRONG BUY").sum()}</div></div>',unsafe_allow_html=True)
    k3.markdown(f'<div class="metric-card"><div class="metric-label">BUY</div><div class="metric-value" style="color:#4ade80;">{(df["Signal"]=="BUY").sum()}</div></div>',unsafe_allow_html=True)
    k4.markdown(f'<div class="metric-card"><div class="metric-label">HOLD</div><div class="metric-value" style="color:#facc15;">{df["Signal"].str.startswith("HOLD").sum()}</div></div>',unsafe_allow_html=True)
    k5.markdown(f'<div class="metric-card"><div class="metric-label">SELL / STRONG SELL</div><div class="metric-value" style="color:#f87171;">{df["Signal"].str.contains("SELL").sum()}</div></div>',unsafe_allow_html=True)
    k6.markdown(f'<div class="metric-card"><div class="metric-label">EARNINGS SOON ⚠️</div><div class="metric-value" style="color:#fbbf24;">{(df["EarningsSoon"]=="⚠️").sum()}</div></div>',unsafe_allow_html=True)

    st.divider()

    tab1,tab2,tab3,tab4=st.tabs(["🎯 Signals","📐 Key Levels","📅 Momentum","🏭 Sector Heat"])

    with tab1:
        if not filt.empty:
            show=["Ticker","Company","Signal","Score","Price","RSI","MACD","Vol Spike","EarningsSoon"]
            st.dataframe(filt[show].style.map(hl_signal,subset=["Signal"])
                         .format({"Price":"${:.2f}","RSI":"{:.1f}","MACD":"{:.3f}","Vol Spike":"{:.2f}x","Score":"{:.0f}/5"}),
                         use_container_width=True)
            st.download_button("⬇️ Export CSV",filt.to_csv(index=False).encode(),
                               f"screener_{datetime.now().strftime('%Y%m%d_%H%M')}.csv","text/csv")

    with tab2:
        lv=["Ticker","Price","Support","Pivot","Resistance","BB Lo","BB Up","Target","Upside%"]
        if not filt.empty:
            st.dataframe(filt[lv].style.format({c:"${:.2f}" for c in ["Price","Support","Pivot","Resistance","BB Lo","BB Up","Target"]}
                                               |{"Upside%":"{:+.1f}%"}),use_container_width=True)

    with tab3:
        mc=["Ticker","Company","Signal","1W%","1M%","3M%","6M%","Beta"]
        if not filt.empty:
            st.dataframe(filt[mc].style.map(hl_signal,subset=["Signal"])
                         .map(hl_mom,subset=["1W%","1M%","3M%","6M%"])
                         .format({c:"{:+.2f}%" for c in ["1W%","1M%","3M%","6M%"]}|{"Beta":"{:.2f}"}),
                         use_container_width=True)

    with tab4:
        if "Sector" in df and "1M%" in df:
            sp=df.dropna(subset=["Sector","1M%"]).groupby("Sector")["1M%"].mean().reset_index()
            sp.columns=["Sector","Avg 1M%"]; sp=sp.sort_values("Avg 1M%",ascending=True)
            fig=px.bar(sp,x="Avg 1M%",y="Sector",orientation="h",
                       color="Avg 1M%",color_continuous_scale=["#7f1d1d","#1c1a03","#052e16"],
                       title="Sector 1-Month Return %")
            fig.update_layout(**PLOTLY_DARK,height=max(300,len(sp)*35+80),
                              margin=dict(l=10,r=10,t=40,b=10),coloraxis_showscale=False)
            st.plotly_chart(fig,use_container_width=True)

    st.divider()
    # Volume spike alerts
    spikes=df[df["Vol Spike"]>2.].sort_values("Vol Spike",ascending=False)
    if not spikes.empty:
        section("🔔 Volume Spike Alerts (>2x Average)")
        st.dataframe(spikes[["Ticker","Company","Signal","Price","Vol Spike","RSI"]].head(10)
                     .style.map(hl_signal,subset=["Signal"])
                     .format({"Price":"${:.2f}","Vol Spike":"{:.2f}x","RSI":"{:.1f}"}),
                     use_container_width=True)

    st.divider()
    # Deep-dive chart
    section("📉 Technical Chart")
    opts=filt["Ticker"].tolist() if not filt.empty else df["Ticker"].tolist()
    sel=st.selectbox("Select ticker:",opts)
    if sel:
        with st.spinner(f"Loading {sel}…"):
            h=yf.Ticker(sel).history(period="1y")
            if not h.empty:
                h=compute_technicals(h); render_full_chart(sel,h)
                last=h.iloc[-1]; rsi_v=float(h["RSI"].iloc[-1])
                rs=calc_support_resistance(h)
                rsi_s="⚠️ Overbought" if rsi_v>70 else ("⚠️ Oversold" if rsi_v<30 else "✅ Healthy")
                st.markdown(f"""| Indicator | Value | Status |
|-----------|-------|--------|
| **EMA Trend (9/21/50)** | {last['EMA_9']:.2f} / {last['EMA_21']:.2f} / {last['EMA_50']:.2f} | {"🟢 BULLISH" if last['EMA_9']>last['EMA_21']>last['EMA_50'] else "🔴 BEARISH"} |
| **RSI (14)** | {rsi_v:.1f} | {rsi_s} |
| **MACD vs Signal** | {last['MACD']:.3f} vs {last['MACD_Sig']:.3f} | {"🟢 Bull" if last['MACD']>last['MACD_Sig'] else "🔴 Bear"} |
| **VWAP** | ${last['VWAP']:.2f} | {"🟢 Above" if last['Close']>last['VWAP'] else "🔴 Below"} |
| **Support / Resistance** | ${rs['support']:.2f} / ${rs['resistance']:.2f} | Pivot ${rs['pivot']:.2f} |""")

def extract_tickers_from_posts(df):
    if df is None or df.empty: return []
    txt=" ".join(df["Content"].astype(str).tolist())
    ct=re.findall(r'\$([A-Z]{1,5})\b',txt)
    pw=re.findall(r'\b([A-Z]{1,5})\b',txt)
    return list(set(ct+[w for w in pw if w in DEFAULT_TICKERS]))

# ──────────────────────────────────────────────────────────────────────────────
# DEEP DIVE
# ──────────────────────────────────────────────────────────────────────────────
def render_deep_dive(ticker_in):
    ticker=ticker_in.strip().upper() if ticker_in else "NVDA"
    t_in,t_btn=st.columns([3,1])
    with t_in: ticker=st.text_input("Ticker:",value=ticker,key="dd_in").strip().upper()
    with t_btn: st.markdown("<br>",unsafe_allow_html=True); st.button("Analyse",type="primary",key="dd_run")

    with st.spinner(f"Loading {ticker}…"):
        try:
            stk=yf.Ticker(ticker); hist=stk.history(period="1y"); info=stk.info
        except Exception as e: st.error(str(e)); return

    if hist.empty: st.error(f"No data for {ticker}"); return
    hist=compute_technicals(hist)
    last=hist.iloc[-1]; sr=calc_support_resistance(hist); mom=calc_momentum(hist)
    live=fetch_live_quote(ticker)
    price=float(last["Close"]); rsi_v=float(last["RSI"])
    sig,score=generate_signal(
        price,float(last["EMA_9"]),float(last["EMA_21"]),float(last["EMA_50"]),
        rsi_v,float(last["VWAP"]),
        float(last["MACD"]) if not pd.isna(last["MACD"]) else 0,
        float(last["MACD_Sig"]) if not pd.isna(last["MACD_Sig"]) else 0,
        float(last["BB_Up"]) if not pd.isna(last["BB_Up"]) else price,
        float(last["BB_Lo"]) if not pd.isna(last["BB_Lo"]) else price,
        float(last["VolSpike"]) if not pd.isna(last["VolSpike"]) else 1.,
    )

    st.markdown(f"## {info.get('shortName',ticker)} &nbsp; <span style='color:#64748b;font-size:1rem;'>({ticker})</span>",unsafe_allow_html=True)
    st.caption(f"{info.get('sector','—')} · {info.get('industry','—')}")
    st.markdown(signal_badge(sig)+f"&nbsp; Confluence **{score}/5**",unsafe_allow_html=True)
    st.markdown("")

    k1,k2,k3,k4,k5,k6=st.columns(6)
    def dd_kpi(col,lbl,val): col.markdown(f'<div class="metric-card"><div class="metric-label">{lbl}</div><div class="metric-value">{val}</div></div>',unsafe_allow_html=True)
    dd_kpi(k1,"PRICE",f"${price:.2f}")
    dd_kpi(k2,"DAY LOW",f"${live.get('dayLow',np.nan):.2f}" if not pd.isna(live.get("dayLow",np.nan)) else "—")
    dd_kpi(k3,"DAY HIGH",f"${live.get('dayHigh',np.nan):.2f}" if not pd.isna(live.get("dayHigh",np.nan)) else "—")
    dd_kpi(k4,"52W LOW",f"${live.get('fiftyTwoWeekLow',np.nan):.2f}" if not pd.isna(live.get("fiftyTwoWeekLow",np.nan)) else "—")
    dd_kpi(k5,"52W HIGH",f"${live.get('fiftyTwoWeekHigh',np.nan):.2f}" if not pd.isna(live.get("fiftyTwoWeekHigh",np.nan)) else "—")
    mc=live.get("marketCap",np.nan)
    mc_s=f"${mc/1e12:.2f}T" if not pd.isna(mc) and mc>=1e12 else (f"${mc/1e9:.1f}B" if not pd.isna(mc) else "—")
    dd_kpi(k6,"MARKET CAP",mc_s)

    st.divider()

    cl,cr=st.columns(2)
    with cl:
        section("📐 Key Levels")
        for k,v in {"Support":f"${sr['support']:.2f}","S1":f"${sr['s1']:.2f}","Pivot":f"${sr['pivot']:.2f}",
                    "R1":f"${sr['r1']:.2f}","Resistance":f"${sr['resistance']:.2f}",
                    "BB Lower":f"${last['BB_Lo']:.2f}","BB Upper":f"${last['BB_Up']:.2f}"}.items():
            st.markdown(f"**{k}:** {v}")
        tgt=live.get("targetMeanPrice",np.nan)
        if not pd.isna(tgt): st.markdown(f"**Analyst Target:** ${tgt:.2f} ({(tgt/price-1)*100:+.1f}%)")
    with cr:
        section("📊 Indicators")
        rsi_s="⚠️ Overbought" if rsi_v>70 else ("⚠️ Oversold" if rsi_v<30 else "✅ Healthy")
        ema_t="🟢 Bullish" if last["EMA_9"]>last["EMA_21"]>last["EMA_50"] else ("🔴 Bearish" if last["EMA_9"]<last["EMA_21"] else "🟡 Mixed")
        vs=float(last["VolSpike"]) if not pd.isna(last["VolSpike"]) else 1.
        for k,v in {"EMA Trend (9/21/50)":ema_t,
                    f"RSI (14)":f"{rsi_v:.1f} — {rsi_s}",
                    "MACD vs Signal":"🟢 Bullish" if not pd.isna(last["MACD"]) and last["MACD"]>last["MACD_Sig"] else "🔴 Bearish",
                    "vs VWAP":"🟢 Above" if price>last["VWAP"] else "🔴 Below",
                    "Volume":f"🔔 {vs:.1f}x avg (Unusual)" if vs>1.5 else f"{vs:.1f}x avg",
                    "ATR":f"${last['ATR']:.2f}" if not pd.isna(last["ATR"]) else "—",
                    "Beta":f"{live.get('beta',np.nan):.2f}" if not pd.isna(live.get("beta",np.nan)) else "—",
                    "Short Ratio":f"{live.get('shortRatio',np.nan):.1f}x" if not pd.isna(live.get("shortRatio",np.nan)) else "—",
                    "Analyst Rating":live.get("recommendationKey","—").upper()}.items():
            st.markdown(f"**{k}:** {v}")

    st.divider()
    section("📈 Multi-Timeframe Momentum")
    m1,m2,m3,m4=st.columns(4)
    for col,p,v in [(m1,"1 Week",mom["1W"]),(m2,"1 Month",mom["1M"]),(m3,"3 Months",mom["3M"]),(m4,"6 Months",mom["6M"])]:
        c="#34d399" if not pd.isna(v) and v>0 else "#f87171"
        vs=f"{v:+.2f}%" if not pd.isna(v) else "—"
        col.markdown(f'<div class="metric-card"><div class="metric-label">{p.upper()}</div><div class="metric-value" style="color:{c};">{vs}</div></div>',unsafe_allow_html=True)

    st.divider()
    section(f"📉 Technical Chart — {ticker} (12 Months)")
    render_full_chart(ticker, hist)

    st.divider()
    section("🧠 AI Deep Dive")
    if st.button("Generate Full AI Analysis",type="primary",key="dd_ai"):
        prompt=f"""
You are a senior equity analyst. Analyse ${ticker} using this real-time data:

Price: ${price:.2f} | Signal: {sig} | Confluence: {score}/5
EMA 9/21/50: {last['EMA_9']:.2f} / {last['EMA_21']:.2f} / {last['EMA_50']:.2f}
RSI: {rsi_v:.1f} | MACD: {last['MACD']:.3f} vs {last['MACD_Sig']:.3f}
Bollinger: ${last['BB_Lo']:.2f} – ${last['BB_Up']:.2f}
VWAP: ${last['VWAP']:.2f} | ATR: ${last['ATR']:.2f} | Vol Spike: {vs:.2f}x
Support: ${sr['support']:.2f} | Resistance: ${sr['resistance']:.2f} | Pivot: ${sr['pivot']:.2f}
Momentum: 1W {mom['1W']:.2f}% · 1M {mom['1M']:.2f}% · 3M {mom['3M']:.2f}% · 6M {mom['6M']:.2f}%
Analyst Target: ${live.get('targetMeanPrice','N/A')} | Beta: {live.get('beta','N/A')} | Short Ratio: {live.get('shortRatio','N/A')}x

Deliver:
1. **Trend Assessment** — direction, strength, sustainability
2. **Key Price Levels** — exact $$ for entries, stops, targets
3. **Signal Confluence** — do indicators agree? Any divergences?
4. **Volume Profile** — what does volume tell us?
5. **Trade Setup** — entry, stop, T1, T2, risk/reward ratio
6. **Thesis Risks** — what invalidates this setup?
7. **Verdict** — (a) day trader playbook · (b) 3-month swing thesis · (c) long-term view

Use specific dollar amounts throughout. No vague statements.
"""
        with st.spinner("Generating analysis…"): st.markdown(call_gemini(prompt))

# ──────────────────────────────────────────────────────────────────────────────
# AI INTELLIGENCE PAGE
# ──────────────────────────────────────────────────────────────────────────────
def scrape_reddit(sub, limit=25):
    out=[]
    try:
        r=requests.get(f"https://www.reddit.com/r/{sub}/new.json?limit={limit}",
                       headers=REDDIT_HEADERS,timeout=10)
        r.raise_for_status()
        for p in r.json()["data"]["children"]:
            d=p["data"]
            out.append({"Platform":"Reddit","Source":f"r/{sub}","Content":d["title"],
                        "Created":datetime.fromtimestamp(d["created_utc"]),"URL":"https://reddit.com"+d["permalink"]})
    except Exception as e: logger.warning("Reddit r/%s: %s",sub,e)
    return out

def scrape_twitter(user, limit=10):
    for inst in NITTER_INSTANCES:
        try:
            feed=feedparser.parse(f"{inst}/{user}/rss")
            if not feed.entries: continue
            return [{"Platform":"Twitter","Source":f"@{user}","Content":e.title,
                     "Created":datetime(*e.published_parsed[:6]) if hasattr(e,"published_parsed") and e.published_parsed else None,
                     "URL":e.link} for e in feed.entries[:limit]]
        except Exception: continue
    return []

def build_html_report(summary_json, report_date):
    t="""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>APEX Market Intelligence Report</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#040810;color:#e2e8f0;font-family:'Space Grotesk',sans-serif;line-height:1.7}
.wrap{max-width:880px;margin:40px auto;padding:48px 56px;background:#07111f;border:1px solid #1e3a5f;border-radius:8px}
header{border-bottom:1px solid #1e3a5f;padding-bottom:24px;margin-bottom:36px}
.logo{font-size:1.8rem;font-weight:700;background:linear-gradient(135deg,#38bdf8,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.meta{font-family:'JetBrains Mono',monospace;font-size:.75rem;color:#475569;letter-spacing:1.5px;text-transform:uppercase;margin-top:6px}
h1{font-size:1.4rem;color:#38bdf8;margin:2rem 0 .8rem;padding-left:12px;border-left:3px solid #38bdf8}
h2{font-size:1.15rem;color:#94a3b8;margin:1.5rem 0 .6rem}
p{margin-bottom:1.2rem;color:#cbd5e1}
ul{padding-left:20px;margin-bottom:1.2rem}
li{margin-bottom:8px;color:#cbd5e1}
table{width:100%;border-collapse:collapse;margin:1.2rem 0;font-family:'JetBrains Mono',monospace;font-size:.82rem}
th{background:#0f172a;color:#38bdf8;padding:8px 12px;text-align:left;border:1px solid #1e3a5f}
td{padding:7px 12px;border:1px solid #1e3a5f;color:#cbd5e1}
tr:nth-child(even) td{background:#0a1628}
a{color:#38bdf8;text-decoration:none;border-bottom:1px solid #1e3a5f}
a:hover{color:#7dd3fc}
strong{color:#f1f5f9;font-weight:600}
footer{margin-top:48px;padding-top:20px;border-top:1px solid #1e3a5f;font-family:'JetBrains Mono',monospace;font-size:.72rem;color:#475569;text-align:center}
</style></head><body><div class="wrap">
<header><div class="logo">APEX.MI</div><div class="meta">Market Intelligence Report · __DATE__</div></header>
<main id="content"><p>Loading…</p></main>
<footer><p>Strictly Confidential · AI-generated · Not financial advice · © 2026 APEX Market Intelligence</p></footer>
</div>
<script id="d" type="application/json">__JSON__</script>
<script>try{document.getElementById('content').innerHTML=marked.parse(JSON.parse(document.getElementById('d').textContent));}catch(e){document.getElementById('content').innerHTML="<p style='color:#f87171'>Render error: "+e+"</p>";}</script>
</body></html>"""
    return t.replace("__JSON__",summary_json).replace("__DATE__",report_date)

def render_ai_intelligence(subs, users, limit, fetch_btn):
    section("AI Market Intelligence","scrape social · synthesise sentiment · generate institutional report")

    if fetch_btn:
        if not subs and not users: st.warning("Select at least one source."); return
        with st.spinner(f"Scraping {len(subs)} subreddits + {len(users)} Twitter accounts…"):
            posts=[]
            def _r(s): return scrape_reddit(s,limit)
            def _t(u): return scrape_twitter(u,limit)
            with ThreadPoolExecutor(max_workers=12) as ex:
                fs={**{ex.submit(_r,s):s for s in subs},**{ex.submit(_t,u):u for u in users}}
                for f in as_completed(fs):
                    try: posts.extend(f.result())
                    except Exception: pass
        if posts:
            df=pd.DataFrame(posts); df["Created"]=pd.to_datetime(df["Created"],errors="coerce")
            st.session_state.ai_df=df.sort_values("Created",ascending=False).reset_index(drop=True)
            st.success(f"✅ {len(df):,} posts collected")
        else:
            st.error("No data retrieved."); st.session_state.ai_df=None

    if st.session_state.ai_df is not None:
        df=st.session_state.ai_df
        with st.expander(f"🔍 Raw Data Preview ({len(df):,} posts)"):
            dd=df.copy()
            dd["URL"]=dd["URL"].apply(lambda x:f'<a href="{x}" target="_blank">↗</a>' if x else "")
            st.write(dd[["Platform","Source","Content","Created","URL"]].to_html(escape=False,index=False),unsafe_allow_html=True)
            st.download_button("⬇️ CSV",df.to_csv(index=False).encode(),
                               f"scraped_{datetime.now().strftime('%Y%m%d')}.csv","text/csv")

        st.divider()
        if st.button("🧠 Generate Premium Report",type="primary"):
            txt="\n".join(df["Content"].astype(str).tolist())[:30_000]
            prompt=f"""
You are a senior portfolio manager at a top-tier hedge fund with 20+ years of experience.
Analyse the following social media posts and deliver a comprehensive, actionable market intelligence brief.

RULE: Every stock ticker MUST be prefixed with $. Example: $AAPL, $NVDA.

# 📊 Overall Market Sentiment
Bullish/Bearish/Neutral with confidence score. Explain dominant psychological tone.

# 📋 Executive Summary
5–6 sentences on primary narrative, macro backdrop, key risk factors, regime signals.

# 🔥 Top 50 Trending Tickers
Bulleted: $TICKER — why trending + sentiment (Bullish/Bearish/Neutral)

# 📈 Tactical Trade Recommendations
Table for top 25: | Ticker | Signal | Entry Zone | Stop | T1 | T2 | Timeframe | Rationale |
Specific dollar values only — no vague ranges.

# 🏭 Sector Themes & Rotation
Inflows/outflows, rotation narrative, 3 macro catalysts.

# ⚠️ Risk Register
5 risks: | Risk | Probability | Impact | Hedge |

# 👤 Trader Playbook
Day Traders: 3 setups with entry + invalidation.
Swing Traders: 3 positions, 1–4 week horizon.
Long-Term: 3 accumulation names with thesis.

Posts:
{txt}"""
            with st.spinner("Generating report with Gemini…"):
                result=call_gemini(prompt)
            linked=re.sub(r'\$([A-Z]{1,5})\b',r'[\1](https://finance.yahoo.com/quote/\1)',result)
            st.markdown("## 📊 Intelligence Report")
            st.markdown(linked)
            rj=json.dumps(linked).replace("</","<\\/")
            html=build_html_report(rj,datetime.now().strftime("%B %d, %Y | %H:%M UTC"))
            b64=base64.b64encode(html.encode()).decode()
            fn=f"APEX_Report_{datetime.now().strftime('%Y%m%d')}.html"
            st.markdown(f'<a href="data:text/html;base64,{b64}" download="{fn}" '
                        f'style="display:inline-block;background:linear-gradient(135deg,#0369a1,#0ea5e9);'
                        f'color:white;padding:12px 28px;border-radius:6px;text-decoration:none;'
                        f'font-family:JetBrains Mono,monospace;font-weight:600;font-size:.85rem;'
                        f'letter-spacing:.5px;margin-top:20px;">📄 Download HTML Report</a>',
                        unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR + ROUTING
# ──────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown(
    '<div style="font-family:\'Syne\',sans-serif;font-size:1.1rem;font-weight:800;'
    'background:linear-gradient(135deg,#38bdf8,#818cf8);-webkit-background-clip:text;'
    '-webkit-text-fill-color:transparent;padding:8px 0 4px;">APEX.MI</div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    '<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.65rem;'
    'color:#475569;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:12px;">'
    'Market Intelligence Platform</div>',
    unsafe_allow_html=True,
)

PAGES = {
    "🌐  Intelligence":    "AI Intelligence",
    "📈  Screener":        "Screener",
    "🔬  Deep Dive":       "Deep Dive",
    "🎯  Options Flow":    "Options",
    "🚨  Alert Engine":    "Alerts",
    "💼  Portfolio":       "Portfolio",
    "📰  News & Earnings": "News",
    "⚗️  Backtester":      "Backtest",
}

page = st.sidebar.radio("", list(PAGES.keys()), label_visibility="collapsed")
mode = PAGES[page]

# ── API key widget (always visible) ─────────────────────────────
render_api_key_sidebar()

# ── Per-page sidebar controls ───────────────────────────────────
subs=[]; users=[]; limit=25; fetch_btn=False
max_pe=150; min_div=0.; show_buy=False; custom_raw=""

if mode == "AI Intelligence":
    st.sidebar.markdown(
        '<div class="section-sub" style="padding:0 4px;">⚙️ SCRAPER SETTINGS</div>',
        unsafe_allow_html=True,
    )
    subs      = st.sidebar.multiselect("Subreddits", DEFAULT_SUBREDDITS, default=DEFAULT_SUBREDDITS[:6])
    users     = st.sidebar.multiselect("Twitter",    DEFAULT_TWITTER,    default=DEFAULT_TWITTER[:4])
    limit     = st.sidebar.slider("Posts/source", 5, 100, 25)
    fetch_btn = st.sidebar.button("🔍 Fetch Data", type="primary")

elif mode == "Screener":
    st.sidebar.markdown(
        '<div class="section-sub" style="padding:0 4px;">⚙️ FILTERS</div>',
        unsafe_allow_html=True,
    )
    show_buy   = st.sidebar.checkbox("BUY signals only", False)
    max_pe     = st.sidebar.slider("Max Fwd P/E", 0, 300, 150)
    min_div    = st.sidebar.slider("Min Div Yield %", 0., 10., 0.)
    custom_raw = st.sidebar.text_area("Extra tickers", "COIN,MSTR,RKLB,IONQ")

elif mode in ("Deep Dive", "Options", "Backtest"):
    custom_raw = st.sidebar.text_input("Ticker", "NVDA")

# ── Render header + ticker strip ────────────────────────────────
render_header()
with st.spinner(""):
    ov = fetch_market_overview()
render_ticker_strip(ov)
st.markdown("")

# ── No-key banner (shown on AI-heavy pages when key is absent) ──
if mode in ("AI Intelligence", "🔬 Deep Dive", "📰 News & Earnings",
            "Alerts", "Backtest"):
    render_no_key_banner()

# ── Page dispatch ────────────────────────────────────────────────
if   mode == "AI Intelligence": render_ai_intelligence(subs, users, limit, fetch_btn)
elif mode == "Screener":        render_screener_page(show_buy, max_pe, min_div, custom_raw)
elif mode == "Deep Dive":       render_deep_dive(custom_raw)
elif mode == "Options":         render_options_page()
elif mode == "Alerts":          render_alerts_page()
elif mode == "Portfolio":       render_portfolio_page()
elif mode == "News":            render_news_earnings_page()
elif mode == "Backtest":        render_backtest_page()
