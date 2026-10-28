import streamlit as st
import pandas as pd
import numpy as np
import requests

# --- MODERN STYLING FOR METRIC BOXES ---
st.markdown("""
<style>
    /* Custom styling for sleek, high-contrast metric containers */
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

# --- STRICT USDT-MARGINED PERPETUAL FUTURES ASSET LIST ---
# Guaranteed futures symbols (Binance USDⓈ-M perpetual contracts & tokenized futures mappings)
FUTURES_ASSETS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT", 
    "ZECUSDT", "TAOUSDT", "HYPEUSDT", "TAIUSDT", 
    "XAUUSDT", "XAGUSDT", "ADAUSDT", "AVAXUSDT", "DOGEUSDT"
]
2. Replacing the Plain Metric Boxes with Clean HTML Cards
Locate where your metric cards are rendered in app.py and replace them with this layout using st.columns:

Python
# --- RENDER CLEAN METRIC CARDS ---
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Opportunities</div>
            <div class="metric-value">{len(filtered_df) if 'filtered_df' in locals() else 0}</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Contracts Scanned</div>
            <div class="metric-value">{len(FUTURES_ASSETS)}</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Timeframe</div>
            <div class="metric-value">{timeframe if 'timeframe' in locals() else '15m'}</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Margin Used</div>
            <div class="metric-value">${investment if 'investment' in locals() else 20}</div>
        </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Leverage</div>
            <div class="metric-value">{leverage if 'leverage' in locals() else 10}x</div>
        </div>
    """, unsafe_allow_html=True)
3. Enforcing Strict Futures-Only API Endpoints
To guarantee that your data is pulled strictly from perpetual futures markets (USDⓈ-M Futures API) and never from spot markets, update your data fetching function to target Binance Futures (fapi.binance.com):

Python
@st.cache_data(ttl=60)
def fetch_futures_ohlcv(symbol, interval="15m", limit=100):
    """
    Fetches candlestick data STRICTLY from Binance USDⓈ-M Perpetual Futures API.
    Endpoint: https://fapi.binance.com (Never uses spot endpoint api.binance.com)
    """
    url = f"https://fapi.binance.com/fapi/v1/klines"
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
                # Convert price/volume columns to float strictly for futures calculations
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                return df
    except Exception as e:
        print(f"Futures API Error for {symbol}: {e}")
    return None
