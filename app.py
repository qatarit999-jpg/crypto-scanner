import streamlit as st
import pandas as pd
import numpy as np
import requests

# --- PAGE CONFIG ---
st.set_page_config(page_title="Crypto Futures Scanner", layout="wide")

# --- MODERN STYLING FOR METRIC BOXES ---
st.markdown("""
<style>
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 16px;
        border-radius: 10px;
        text-align: center;
        color: #f8fafc;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-title {
        font-size: 14px;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 24px;
        color: #38bdf8;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# --- STRICT USDT-MARGINED PERPETUAL FUTURES ASSETS ---
FUTURES_ASSETS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT", 
    "ZECUSDT", "TAOUSDT", "HYPEUSDT", "TAIUSDT", 
    "XAUUSDT", "XAGUSDT", "ADAUSDT", "AVAXUSDT", "DOGEUSDT"
]

@st.cache_data(ttl=60)
def fetch_futures_ohlcv(symbol, interval="15m", limit=100):
    """
    Fetches candlestick data STRICTLY from Binance USD-M Perpetual Futures API.
    Endpoint: https://fapi.binance.com (Never uses spot endpoints)
    """
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": limit
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'number_of_trades',
                    'taker_buy_base', 'taker_buy_quote', 'ignore'
                ])
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                return df
    except Exception as e:
        print(f"Futures API Error for {symbol}: {e}")
    return None

def analyze_whale_and_patterns(df):
    """
    Analyzes per-asset whale volume spikes and detects candlestick patterns.
    """
    default_whale = "Normal"
    default_pattern = "None"

    if df is None or len(df) == 0:
        return default_whale, default_pattern

    try:
        df.columns = [str(col).lower() for col in df.columns]
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                return default_whale, default_pattern

        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna(subset=required_cols)
        if len(df) < 5:
            return default_whale, default_pattern

        # Whale Volume Calculation
        window_size = min(20, len(df))
        df['vol_ma'] = df['volume'].rolling(window=window_size).mean()
        
        latest_vol = df['volume'].iloc[-1]
        latest_ma = df['vol_ma'].iloc[-1]
        
        if pd.notna(latest_ma) and latest_ma > 0 and latest_vol >= (latest_ma * 3.0):
            whale_status = "🐋 Whale Spike"
        else:
            whale_status = "Normal"

        # Candlestick Patterns
        pattern = "None"
        if len(df) >= 3:
            o3, h3, l3, c3 = df['open'].iloc[-3], df['high'].iloc[-3], df['low'].iloc[-3], df['close'].iloc[-3]
            o2, h2, l2, c2 = df['open'].iloc[-2], df['high'].iloc[-2], df['low'].iloc[-2], df['close'].iloc[-2]
            o1, h1, l1, c1 = df['open'].iloc[-1], df['high'].iloc[-1], df['low'].iloc[-1], df['close'].iloc[-1]
            
            if (c3 < o3) and (abs(c2 - o2) < (h2 - l2 + 1e-9) * 0.3) and (c1 > o1) and (c1 > (o3 + c3) / 2):
                pattern = "Bullish Morning Star"
            elif c2 < o2 and c1 > o1 and c1 >= o2 and (c1 - o1) > (o2 - c2):
                pattern = "Bullish Engulfing"
            elif (h1 - l1) > 3 * (abs(c1 - o1)) and (min(c1, o1) - l1) > 2 * (abs(c1 - o1)):
                pattern = "Bullish Hammer"
            elif (c3 > o3) and (abs(c2 - o2) < (h2 - l2 + 1e-9) * 0.3) and (c1 < o1) and (c1 < (o3 + c3) / 2):
                pattern = "Bearish Evening Star"
            elif c2 > o2 and c1 < o1 and c1 <= o2 and (o1 - c1) > (c2 - o2):
                pattern = "Bearish Engulfing"
            elif (h1 - l1) > 3 * (abs(c1 - o1)) and (h1 - max(c1, o1)) > 2 * (abs(c1 - o1)):
                pattern = "Bearish Shooting Star"

        return whale_status, pattern

    except Exception:
        return default_whale, default_pattern

# --- SIDEBAR CONTROLS ---
st.sidebar.markdown("## ⚙️ Scanner Controls")
investment = st.sidebar.number_input("Investment / Margin ($)", value=20.0, step=5.0)
leverage = st.sidebar.slider("Leverage (x)", min_value=1, max_value=50, value=10)
timeframe = st.sidebar.selectbox("Select Timeframe", ["5m", "15m", "1h", "4h"], index=1)
scan_button = st.sidebar.button("🚀 Run Live Market Scan")

# --- MAIN UI LAYOUT ---
st.markdown("# ⚡ Binance Futures & Global Asset Scanner")
st.markdown("Institutional-grade perpetual futures liquidity screening and risk management.")

# Render Clean Metric Cards
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Opportunities</div><div class="metric-value">0</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Contracts Scanned</div><div class="metric-value">{len(FUTURES_ASSETS)}</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Timeframe</div><div class="metric-value">{timeframe}</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Margin Used</div><div class="metric-value">${investment}</div></div>', unsafe_allow_html=True)
with col5:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Leverage</div><div class="metric-value">{leverage}x</div></div>', unsafe_allow_html=True)

if scan_button:
    results = []
    with st.spinner("Scanning Binance Perpetual Futures markets..."):
        for symbol in FUTURES_ASSETS:
            df = fetch_futures_ohlcv(symbol, interval=timeframe)
            if df is not None and not df.empty:
                whale, pattern = analyze_whale_and_patterns(df)
                latest_price = df['close'].iloc[-1]
                results.append({
                    "Symbol": symbol,
                    "Futures Price ($)": latest_price,
                    "Whale Vol": whale,
                    "Candle Pattern": pattern
                })
        
        if results:
            res_df = pd.DataFrame(results)
            st.success(f"Successfully scanned {len(res_df)} futures contracts!")
            st.dataframe(res_df, width='stretch')
        else:
            st.warning("No futures data returned from the exchange endpoints.")
