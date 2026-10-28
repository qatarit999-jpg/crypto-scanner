import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import urllib.request
import xml.etree.ElementTree as ET

st.set_page_config(
    page_title="Institutional Crypto & Asset Scanner",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #0b0f19; }
    .stMetric { background-color: #111827; border: 1px solid #1f2937; padding: 15px; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

def fetch_macro_news():
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
selected_tf_label = st.sidebar.selectbox("Select Timeframe", list(timeframe_map.keys()), index=2)
selected_tf = timeframe_map[selected_tf_label]

run_scan = st.sidebar.button("🚀 Run Live Market Scan", type="primary")

st.title("⚡ Binance & Global Asset RSI Scanner")
st.markdown("Institutional-grade liquidity screening, UT Bot indicators, and automated risk management advisor.")

with st.expander("📰 Live Macro, FED, OCC, CPI, PPI & London Crypto Intel", expanded=False):
    headlines = fetch_macro_news()
    for h in headlines[:5]:
        st.markdown(f"• {h}")
    st.markdown("---")
    st.markdown("🎯 **News Spotlight:** **RENDER/USDT** & **TAO/USDT** (AI Infrastructure Capital Flow)")

if run_scan:
    total_position_size = investment * leverage
    symbols = [
        'XAU/USDT', 'XAG/USDT', 'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 
        'ADA/USDT', 'DOGE/USDT', 'AVAX/USDT', 'LINK/USDT', 'DOT/USDT', 'NEAR/USDT', 'UNI/USDT', 
        'APT/USDT', 'AR/USDT', 'SUI/USDT', 'RENDER/USDT', 'PEPE/USDT', 'SHIB/USDT', 'FET/USDT', 
        'ATOM/USDT', 'ICP/USDT', 'INJ/USDT', 'TIA/USDT', 'OP/USDT', 'ARB/USDT', 'POL/USDT', 
        'IMX/USDT', 'FIL/USDT', 'GRT/USDT', 'RUNE/USDT', 'SEI/USDT', 'KAS/USDT', 'STX/USDT', 
        'FLOKI/USDT', 'WIF/USDT', 'BONK/USDT', 'JUP/USDT', 'PYTH/USDT', 'ENA/USDT', 'ONDO/USDT', 
        'TAO/USDT', 'WLD/USDT', 'ARKM/USDT', 'STRK/USDT', 'MANTA/USDT', 'ALT/USDT', 'CHZ/USDT', 
        'CRV/USDT', 'LDO/USDT', 'ETC/USDT'
    ]

    progress_bar = st.progress(0, text="Initializing Binance connection & scanning assets...")
    exchange = ccxt.binance({'enableRateLimit': True})
    matches = []
    total_symbols = len(symbols)
    
    for idx, symbol in enumerate(symbols):
        progress_bar.progress((idx + 1) / total_symbols, text=f"Scanning contract {idx+1}/{total_symbols}: {symbol}")
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, selected_tf, limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            df['rsi'] = 100 - (100 / (1 + (gain / loss)))
            
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
            r_high = df['high'].tail(20).max()
            r_low = df['low'].tail(20).min()
            
            if rsi > 70 or rsi < 30:
                is_short = rsi > 70
                signal = "SHORT 🔴" if is_short else "LONG 🟢"
                sl = r_high * 1.02 if is_short else r_low * 0.98
                risk_pct = abs(sl - price) / price
                dollar_risk = total_position_size * risk_pct
                
                tp1 = price - (abs(sl - price) * 1.5) if is_short else price + (abs(price - sl) * 1.5)
                tp2 = price - (abs(sl - price) * 2.5) if is_short else price + (abs(price - sl) * 2.5)
                tp3 = price - (abs(sl - price) * 4.0) if is_short else price + (abs(price - sl) * 4.0)
                
                advice = "✅ Safe" if dollar_risk <= investment else "🚨 High Risk"

                matches.append({
                    "Symbol": symbol, "Direction": signal, "Price": f"${price:,.2f}",
                    "Stop Loss": f"${sl:,.2f}", "TP1 (1.5R)": f"${tp1:,.2f}", "TP2 (2.5R)": f"${tp2:,.2f}",
                    "TP3 (4.0R)": f"${tp3:,.2f}", "RSI": f"{rsi:.1f}", "UT Bot": ut_style if 'ut_style' in locals() else ut_status,
                    "Risk ($)": f"-${dollar_risk:,.2f}", "Status": advice
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
        st.success(f"Successfully identified {len(matches)} active institutional trade setups!")
        st.dataframe(pd.DataFrame(matches), use_container_width=True)
    else:
        st.warning("No assets currently match extreme RSI criteria on this timeframe.")
else:
    st.info("👈 Set your investment margin and leverage in the sidebar, choose a timeframe, and click **'Run Live Market Scan'** to start.")
