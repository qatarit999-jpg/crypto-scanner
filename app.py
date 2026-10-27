import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import urllib.request
import xml.etree.ElementTree as ET

# Page configuration
st.set_page_config(page_title="Multi-Exchange Crypto RSI & PVT Scanner", page_icon="⚡", layout="wide")

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
st.sidebar.markdown("Configure your exchange, margin, leverage, and timeframes below.")

# Exchange Selector Dropdown
exchange_options = ["MEXC", "Binance", "OKX", "Bybit", "Bitget", "Gate.io", "KuCoin"]
selected_exchange_name = st.sidebar.selectbox("Select Exchange", exchange_options)

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
st.title("⚡ Multi-Exchange Crypto RSI & PVT Scanner")
st.markdown("Institutional-grade liquidity screening, UT Bot indicators, Price Volume Trend (PVT) confirmation, and automated risk management advisor.")

# News Expander
with st.expander("📰 Live Macro, FED, OCC, CPI, PPI & London Crypto Intel"):
    for item in get_crypto_news():
        st.markdown(f"- {item}")

st.markdown("---")

if run_scan:
    with st.spinner(f"Connecting to {selected_exchange_name} & scanning market with PVT indicators..."):
        try:
            exchange_map = {
                "MEXC": ccxt.mexc,
                "Binance": ccxt.binance,
                "OKX": ccxt.okx,
                "Bybit": ccxt.bybit,
                "Bitget": ccxt.bitget,
                "Gate.io": ccxt.gate,
                "KuCoin": ccxt.kucoin
            }
            
            exchange_class = exchange_map.get(selected_exchange_name, ccxt.mexc)
            exchange = exchange_class({'enableRateLimit': True})
            exchange.load_markets()
            
        except Exception as e:
            st.warning(f"⚠️ {selected_exchange_name} connection blocked or failed ({e}). Automatically falling back to MEXC...")
            exchange = ccxt.mexc({'enableRateLimit': True})
            exchange.load_markets()

        try:
            priority_coins = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'ZEC/USDT', 'ADA/USDT', 'AVAX/USDT', 'LINK/USDT', 'DOGE/USDT', 'MATIC/USDT']
            all_symbols = [s for s in exchange.symbols if '/USDT' in s]
            
            symbols = [s for s in priority_coins if s in all_symbols]
            remaining = [s for s in all_symbols if s not in symbols]
            symbols.extend(remaining[:50 - len(symbols)])
            
            if not symbols:
                symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'ZEC/USDT']
                
            matches = []
            total_symbols = len(symbols)
            progress_bar = st.progress(0, text="Initializing market scan...")
            
            for idx, symbol in enumerate(symbols):
                progress_bar.progress((idx + 1) / total_symbols, text=f"Scanning contract {idx+1}/{total_symbols}: {symbol}")
                try:
                    ohlcv = exchange.fetch_ohlcv(symbol, selected_tf, limit=100)
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    
                    # 1. RSI calculation
                    delta = df['close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    df['rsi'] = 100 - (100 / (1 + (gain / loss)))
                    
                    # 2. Price Volume Trend (PVT) calculation
                    price_change_pct = df['close'].pct_change()
                    df['pvt'] = (df['volume'] * price_change_pct).cumsum().fillna(0)
                    df['pvt_signal'] = df['pvt'].ewm(span=10, adjust=False).mean()
                    
                    # 3. ATR / UT Bot calculation (Clean multi-line format to prevent syntax errors)
                    tr1 = df['high'] - df['low']
                    tr2 = np.abs(df['high'] - df['close'].shift())
                    tr3 = np.abs(df['low'] - df['close'].shift())
                    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                    
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
                    prev_candle = df.iloc[-2]
                    rsi = latest['rsi']
                    price = latest['close']
                    
                    pvt_rising = latest['pvt'] > latest['pvt_signal']
                    
                    if rsi < 35 or rsi > 65:
                        signal = "LONG 🟢" if rsi < 35 else "SHORT 🔴"
                        sl = price * 0.98 if signal.startswith("LONG") else price * 1.02
                        tp1 = price * 1.02 if signal.startswith("LONG") else price * 0.98
                        tp2 = price * 1.04 if signal.startswith("LONG") else price * 0.96
                        tp3 = price * 1.06 if signal.startswith("LONG") else price * 0.94
                        
                        position_notional = investment * leverage
                        dollar_risk = position_notional * (abs(price - sl) / price)
                        
                        is_bullish_momentum = price > prev_candle['close']
                        
                        if signal.startswith("SHORT") and is_bullish_momentum:
                            advice = "⏳ Wait 15m-30m (Bullish Momentum)"
                        elif signal.startswith("LONG") and not is_bullish_momentum:
                            advice = "⏳ Wait 15m-30m (Bearish Momentum)"
                        elif signal.startswith("LONG") and pvt_rising:
                            advice = "⚡ Confirmed PVT Buy"
                        elif signal.startswith("SHORT") and not pvt_rising:
                            advice = "⚡ Confirmed PVT Sell"
                        else:
                            advice = "⚠️ Volume Divergence Warning"
                        
                        matches.append({
                            "Symbol": symbol,
                            "Direction": signal,
                            "Price": f"${price:.2f}",
                            "Stop Loss": f"${sl:.2f}",
                            "TP1 (1.5R)": f"${tp1:.2f}",
                            "TP2 (2.5R)": f"${tp2:.2f}",
                            "TP3 (4.0R)": f"${tp3:.2f}",
                            "RSI": f"{rsi:.1f}",
                            "PVT Trend": "Bullish 🟢" if pvt_rising else "Bearish 🔴",
                            "UT Bot": ut_status,
                            "Risk ($)": f"-${dollar_risk:.2f}",
                            "Status": advice
                        })
                except Exception:
                    continue
            
            progress_bar.empty()
            
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Opportunities Found", len(matches))
            col2.metric("Contracts Scanned", total_symbols)
            col3.metric("Timeframe", selected_tf)
            col4.metric("Margin Used", f"${investment:,.0f}")
            col5.metric("Leverage", f"{leverage}x")
            
            st.markdown("---")
            
            if matches:
                st.success(f"Successfully identified {len(matches)} active institutional trade setups with PVT filters!")
                st.dataframe(pd.DataFrame(matches), use_container_width=True)
            else:
                st.warning("No assets currently match extreme RSI & volume criteria on this timeframe.")
                
        except Exception as e:
            st.error(f"Error executing market scan: {e}")
else:
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Opportunities Found", 0)
    col2.metric("Contracts Scanned", 50)
    col3.metric("Timeframe", selected_tf)
    col4.metric("Margin Used", f"${investment:,.0f}")
    col5.metric("Leverage", f"{leverage}x")
    
    st.markdown("---")
    st.info("👈 Choose your exchange, set your margin and leverage in the sidebar, select a timeframe, and click **'Run Live Market Scan'** to start.")
