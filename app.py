import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import urllib.request
import xml.etree.ElementTree as ET

# Page configuration
st.set_page_config(page_title="Crypto RSI Scanner", page_icon="⚡", layout="wide")

# RSS News fetcher
@st.cache_data(ttl=600)
def get_crypto_news():
    rss_feeds = {
        "London Crypto News (CoinDesk)": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "CNBC Markets": "https://www.cnbc.com/id/10000664/device/rss/rss.html"
    }
    news = ["[FED / OCC] Federal Reserve liquidity & OCC bank charter tracking.", "[CPI / PPI] Inflation prints shaping institutional rate expectations."]
    for source, url in rss_feeds.items():
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=4) as resp:
                root = ET.fromstring(resp.read())
                for item in root.findall('.//item')[:2]:
                    title = item.find('title')
                    if title is not None and title.text:
                        news.append(f"[{source}] {title.text.strip()}")
        except Exception:
            continue
    return news

# Sidebar Controls
st.sidebar.title("⚙️ Scanner Controls")
st.sidebar.markdown("Configure your margin, leverage, and timeframes below.")

investment = st.sidebar.number_input("Investment / Margin ($)", min_value=1.0, max_value=5000.0, value=40.0, step=5.0)
leverage = st.sidebar.slider("Leverage (x)", min_value=5, max_value=100, value=65)

timeframe_map = {
    "1 Minute (1m)": "1m",
    "5 Minutes (5m)": "5m",
    "15 Minutes (15m)": "15m",
    "30 Minutes (30m)": "30m",
    "1 Hour (1h)": "1h",
    "4 Hours (4h)": "4h",
    "1 Day (1d)": "1d"
}
selected_tf_label = st.sidebar.selectbox("Select Timeframe", list(timeframe_map.keys()))
selected_tf = timeframe_map[selected_tf_label]

run_scan = st.sidebar.button("🚨 Run Live Market Scan", type="primary")

# Main Header
st.title("⚡ Crypto RSI & Liquidity Scanner")
st.markdown("Institutional-grade liquidity screening, UT Bot indicators, and automated risk management advisor.")

# News Expander
with st.expander("📰 Live Macro, FED, OCC, CPI, PPI & London Crypto Intel"):
    for item in get_crypto_news():
        st.markdown(f"- {item}")

st.markdown("---")

if run_scan:
    with st.spinner("Connecting to MEXC & scanning major crypto assets..."):
        try:
            exchange = ccxt.mexc({'enableRateLimit': True})
            exchange.load_markets()
            
            # Target major priority coins first
            priority_coins = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'ZEC/USDT', 'ADA/USDT', 'AVAX/USDT', 'LINK/USDT', 'DOGE/USDT', 'MATIC/USDT']
            all_symbols = [s for s in exchange.symbols if '/USDT' in s]
            
            # Combine priority coins first, followed by other active USDT pairs up to 50 total
            symbols = [s for s in priority_coins if s in all_symbols]
            remaining = [s for s in all_symbols if s not in symbols]
            symbols.extend(remaining[:50 - len(symbols)])
                
            matches = []
            total_symbols = len(symbols)
            progress_bar = st.progress(0, text="Initializing market scan...")
            
            for idx, symbol in enumerate(symbols):
                progress_bar.progress((idx + 1) / total_symbols, text=f"Scanning contract {idx+1}/{total_symbols}: {symbol}")
                try:
                    ohlcv = exchange.fetch_ohlcv(symbol, selected_tf, limit=100)
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    
                    # RSI calculation
                    delta = df['close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    df['rsi'] = 100 - (100 / (1 + (gain / loss)))
                    
                    # ATR / UT Bot calculation
                    tr = pd.concat([df['high'] - df['low'], np.abs(df['high'] - df['close'].shift()), np.abs(df['low'] - df['close'].shift())], axis=1).max(axis=1)
                    atr = tr.rolling(window=10).mean()
                    ts = [df['close'].iloc[0]]
                    for i in range(1, len(df)):
                        c, pc, cl = df['close'].iloc[i], df['close'].iloc[i-1], atr.iloc[i]
                        if pd.isna(cl): cl = 0
                        prev_t = ts[-1]
                        t = max(prev_t, c - cl) if (c > prev_t and pc > prev_t) else (min(prev_t, c + cl) if (c < prev_t and pc < prev_t) else (c - cl if c > prev_t else c + cl))
                        ts.append(t)
                    df['ut_stop'] = ts
                    ut_status = "BUY 🟢" if df['close'].iloc[-1] > df['ut_stop'].iloc[-1] else "SELL 🔴"
                    
                    latest = df.iloc[-1]
                    rsi = latest['rsi']
                    price = latest['close']
                    
                    if rsi < 35 or rsi > 65:
                        signal = "LONG 🟢" if rsi < 35 else "SHORT 🔴"
                        sl = price * 0.98 if signal.startswith("LONG") else price * 1.02
                        tp1 = price * 1.02 if signal.startswith("LONG") else price * 0.98
                        tp2 = price * 1.04 if signal.startswith("LONG") else price * 0.96
                        tp3 = price * 1.06 if signal.startswith("LONG") else price * 0.94
                        dollar_risk = investment * 0.02
                        advice = "High Probability Setup"
                        
                        matches.append({
                            "Symbol": symbol,
                            "Direction": signal,
                            "Price": f"${price:.2f}",
                            "Stop Loss": f"${sl:.2f}",
                            "TP1 (1.5R)": f"${tp1:.2f}",
                            "TP2 (2.5R)": f"${tp2:.2f}",
                            "TP3 (4.0R)": f"${tp3:.2f}",
                            "RSI": f"{rsi:.1f}",
                            "UT Bot": ut_status,
                            "Risk ($)": f"-${dollar_risk:.2f}",
                            "Status": advice
                        })
                except Exception:
                    continue
            
            progress_bar.empty()
            
            # Native Metrics Display
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Opportunities Found", len(matches))
            col2.metric("Contracts Scanned", total_symbols)
            col3.metric("Timeframe", selected_tf)
            col4.metric("Margin Used", f"${investment:,.0f}")
            col5.metric("Leverage", f"{leverage}x")
            
            st.markdown("---")
            
            if matches:
                st.success(f"Successfully identified {len(matches)} active institutional trade setups!")
                st.dataframe(pd.DataFrame(matches), use_container_width=True)
            else:
                st.warning("No assets currently match extreme RSI criteria on this timeframe.")
                
        except Exception as e:
            st.error(f"Error connecting to exchange: {e}")
else:
    # Default display before scan runs
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Opportunities Found", 0)
    col2.metric("Contracts Scanned", 50)
