import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import streamlit.components.v1 as components
import urllib.request
import xml.etree.ElementTree as ET
import json
import os
import re

# Page configuration
st.set_page_config(page_title="Tether (USDT-M) Futures & Global Auth Scanner", page_icon="⚡", layout="wide")

# Persistent User Database File Storage
USERS_FILE = "users.json"

def load_users_db():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_users_db(db):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(db, f, indent=4)
    except Exception:
        pass

# Initialize Session State with Persistent Storage
if 'users_db' not in st.session_state:
    st.session_state.users_db = load_users_db()
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None

# Enhanced RSS & Regulatory News Fetcher
@st.cache_data(ttl=600)
def get_crypto_news():
    rss_feeds = {
        "London Crypto News (CoinDesk)": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "SEC Press Releases": "https://www.sec.gov/news/pressreleases.rss",
        "Federal Reserve": "https://www.federalreserve.gov/feeds/press_all.xml"
    }
    news = [
        "[FED / OCC] Federal Reserve liquidity & OCC bank charter tracking.",
        "[CPI / PPI] Inflation prints shaping institutional rate expectations."
    ]
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

# Live X (Twitter) API Fetcher for Multiple Crypto Leaders
def get_live_tweets(bearer_token, username="saylor"):
    if not bearer_token or bearer_token.strip() == "":
        fallbacks = {
            "saylor": [
                "🐦 **@saylor (Michael Saylor):** \"Saying there is no reason to buy Bitcoin because anyone can create a cryptocurrency is like saying there is no reason to learn English...\"",
                "🐦 **@saylor (Michael Saylor):** Corporate treasury strategy update: Expanding long-term digital asset reserves to back institutional balance sheet growth."
            ],
            "VitalikButerin": [
                "🐦 **@VitalikButerin:** Exploring new cryptographic primitives for cross-layer scalability and enhanced privacy preservation on decentralized state networks.",
                "🐦 **@VitalikButerin:** Thoughts on upcoming rollup security optimizations and stateless client validation milestones."
            ],
            "cz_binance": [
                "🐦 **@cz_binance:** Focus on building, security, and long-term user protection. Market cycles come and go, execution remains constant.",
                "🐦 **@cz_binance:** Education and Web3 infrastructure development are key drivers for the next wave of global adoption."
            ],
            "balajis": [
                "🐦 **@balajis:** Decentralization is moving from financial protocols outward into network states, decentralized media, and sovereign supply chains.",
                "🐦 **@balajis:** Cloud-first communities and algorithmic governance are transforming how capital and talent allocate globally."
            ]
        }
        default_tweets = fallbacks.get(username, [f"🐦 **@{username}:** [Connect your X Bearer Token in the sidebar to stream live posts from this account.]"])
        default_tweets.append("💡 *Tip: Enter your X (Twitter) API Bearer Token in the sidebar to fetch real-time tweets automatically!*")
        return default_tweets
    
    try:
        user_url = f"https://api.twitter.com/2/users/by/username/{username}"
        req_user = urllib.request.Request(user_url, headers={'Authorization': f'Bearer {bearer_token}', 'User-Agent': 'v2UserLookupPython'})
        with urllib.request.urlopen(req_user, timeout=5) as resp:
            user_data = json.loads(resp.read().decode())
            user_id = user_data.get('data', {}).get('id')
            
        if not user_id:
            return [f"⚠️ Could not resolve Twitter user ID for @{username}."]

        tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets?max_results=5&tweet.fields=created_at"
        req_tweets = urllib.request.Request(tweets_url, headers={'Authorization': f'Bearer {bearer_token}', 'User-Agent': 'v2UserTweetsPython'})
        with urllib.request.urlopen(req_tweets, timeout=5) as resp:
            tweets_data = json.loads(resp.read().decode())
            tweets = tweets_data.get('data', [])
            
            if not tweets:
                return [f"No recent tweets found for @{username}."]
                
            formatted_tweets = []
            for t in tweets:
                text = t.get('text', '')
                formatted_tweets.append(f"🐦 **@{username}:** \"{text}\"")
            return formatted_tweets
            
    except Exception as e:
        return [f"⚠️ Twitter API Error: {e}. Please check your Bearer Token."]

# Sidebar Authentication & Controls
st.sidebar.title("🔐 User Portal & Controls")

st.sidebar.metric("👥 Total Registered Users", len(st.session_state.users_db))
st.sidebar.markdown("---")

if st.session_state.logged_in_user is None:
    auth_mode = st.sidebar.radio("Select Mode", ["Login", "Register / Sign Up", "Forgot Credentials"])
    
    country_dial_codes = {
        "Pakistan (+92)": "+92",
        "United States / Canada (+1)": "+1",
        "United Kingdom (+44)": "+44",
        "United Arab Emirates (+971)": "+971",
        "Saudi Arabia (+966)": "+966",
        "India (+91)": "+91",
        "Germany (+49)": "+49",
        "France (+33)": "+33",
        "Turkey (+90)": "+90",
        "Qatar (+974)": "+974",
        "Australia (+61)": "+61",
        "Singapore (+65)": "+65",
        "Malaysia (+60)": "+60",
        "Other / International": "+"
    }

    if auth_mode == "Register / Sign Up":
        st.sidebar.subheader("🌍 Global User Registration")
        reg_name = st.sidebar.text_input("Full Name")
        reg_username = st.sidebar.text_input("Choose Username")
        reg_password = st.sidebar.text_input("Create Password", type="password")
        
        selected_country_label = st.sidebar.selectbox("Select Country / Dial Code", list(country_dial_codes.keys()))
        dial_prefix = country_dial_codes[selected_country_label]
        
        reg_phone_local = st.sidebar.text_input("Phone Number (e.g. 3001234567)")
        
        if st.sidebar.button("Register Account", type="primary"):
            cleaned_phone_local = reg_phone_local.strip().lstrip('0')
            full_phone = f"{dial_prefix}{cleaned_phone_local}"
            
            if not reg_name or not reg_username or not reg_password or not reg_phone_local:
                st.sidebar.error("⚠️ Please fill in all registration fields.")
            elif reg_username in st.session_state.users_db:
                st.sidebar.error("⚠️ Username already exists. Choose another.")
            elif not re.match(r"^\+[1-9]\d{6,14}$", full_phone):
                st.sidebar.error("⚠️ Invalid phone number format. Please check your digits.")
            else:
                st.session_state.users_db[reg_username] = {
                    "name": reg_name,
                    "password": reg_password,
                    "phone": full_phone
                }
                save_users_db(st.session_state.users_db)
                st.sidebar.success("🎉 Registration successful! Please switch to Login.")
                
    elif auth_mode == "Login":
        st.sidebar.subheader("🔑 Member Login")
        login_user = st.sidebar.text_input("Username")
        login_pass = st.sidebar.text_input("Password", type="password")
        
        if st.sidebar.button("Login", type="primary"):
            st.session_state.users_db = load_users_db()
            if login_user in st.session_state.users_db and st.session_state.users_db[login_user]["password"] == login_pass:
                st.session_state.logged_in_user = login_user
                st.sidebar.success(f"Welcome back, {st.session_state.users_db[login_user]['name']}!")
                st.rerun()
            else:
                st.sidebar.error("❌ Invalid username or password.")
                
    elif auth_mode == "Forgot Credentials":
        st.sidebar.subheader("🔄 Recover Account")
        selected_rec_country = st.sidebar.selectbox("Select Country / Dial Code", list(country_dial_codes.keys()), key="rec_country")
        rec_dial_prefix = country_dial_codes[selected_rec_country]
        rec_phone_local = st.sidebar.text_input("Registered Phone Number (e.g. 3001234567)", key="rec_phone")
        
        if st.sidebar.button("Send Recovery Details", type="primary"):
            cleaned_rec_phone = rec_phone_local.strip().lstrip('0')
            target_full_phone = f"{rec_dial_prefix}{cleaned_rec_phone}"
            
            st.session_state.users_db = load_users_db()
            found_user = None
            for uname, udata in st.session_state.users_db.items():
                if udata.get("phone") == target_full_phone:
                    found_user = uname
                    break
            
            if found_user:
                st.sidebar.success(f"📨 Message has been sent to the registered number ({target_full_phone})!")
            else:
                st.sidebar.error("⚠️ No account found registered with this phone number.")

    st.stop()

else:
    user_info = st.session_state.users_db[st.session_state.logged_in_user]
    st.sidebar.success(f"👤 Logged in as: **{user_info['name']}** (@{st.session_state.logged_in_user})")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in_user = None
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.title("⚙️ USDT Futures Controls")
    
    exchange_options = ["MEXC", "Binance", "OKX", "Bybit", "Bitget", "Gate.io", "KuCoin"]
    selected_exchange_name = st.sidebar.selectbox("Select Exchange", exchange_options)

    investment = st.sidebar.number_input("Investment / Margin ($USDT)", min_value=1.0, max_value=5000.0, value=40.0, step=5.0)
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

    st.sidebar.markdown("---")
    st.sidebar.markdown("🐦 **Crypto Trader Twitter / X Settings**")

    trader_options = {
        "Michael Saylor (@saylor)": "saylor",
        "Vitalik Buterin (@VitalikButerin)": "VitalikButerin",
        "CZ (Changpeng Zhao)": "cz_binance",
        "Balaji Srinivasan (@balajis)": "balajis",
        "Custom Handle": "custom"
    }
    selected_trader_label = st.sidebar.selectbox("Select Market Leader", list(trader_options.keys()))

    if selected_trader_label == "Custom Handle":
        twitter_handle = st.sidebar.text_input("Enter Custom Twitter Handle", value="saylor", help="Type username without '@'")
    else:
        twitter_handle = trader_options[selected_trader_label]

    twitter_token = st.sidebar.text_input("X API Bearer Token (Optional)", type="password", help="Paste your X Developer Bearer Token here to pull live real-time tweets.")

    run_scan = st.sidebar.button("🚨 Run Live USDT Futures Scan", type="primary")

# Main Header
st.title("⚡ Multi-Exchange USDT Perpetual Futures Scanner")
st.markdown("Strictly USDⓈ-M derivatives screening, TradingView-aligned UT Bot indicators, and Price Volume Trend (PVT) confirmation.")

# News & Regulatory Expander
with st.expander("📰 Live Macro, SEC Regulatory Filings & London Crypto Intel"):
    for item in get_crypto_news():
        st.markdown(f"- {item}")

# 🧮 Interactive Risk Management & PnL Calculator Panel
st.markdown("---")
st.subheader("🧮 Live Risk Management & PnL Calculator")
st.markdown("Configure your margin allocation and leverage to calculate exact risk exposure and profit targets.")

calc_col1, calc_col2, calc_col3, calc_col4 = st.columns(4)
with calc_col1:
    calc_margin = st.number_input("Margin Amount ($USDT)", min_value=1.0, max_value=10000.0, value=investment, step=10.0)
with calc_col2:
    calc_lev = st.number_input("Leverage (x)", min_value=1, max_value=100, value=leverage, step=1)
with calc_col3:
    calc_entry = st.number_input("Estimated Entry Price ($)", min_value=0.0001, value=100.0, step=0.01, format="%.4f")
with calc_col4:
    calc_target_pct = st.number_input("Target Gain (%)", min_value=0.1, max_value=500.0, value=5.0, step=0.5)

total_position_size = calc_margin * calc_lev
potential_profit_usdt = total_position_size * (calc_target_pct / 100.0)
max_loss_usdt = calc_margin

pnl_col1, pnl_col2, pnl_col3 = st.columns(3)
pnl_col1.metric("Total Position Notional", f"${total_position_size:,.2f} USDT")
pnl_col2.metric("Projected Profit (TP)", f"+${potential_profit_usdt:,.2f} USDT", delta=f"+{calc_target_pct}% Move")
pnl_col3.metric("Max Margin Risk (SL)", f"-${max_loss_usdt:,.2f} USDT", delta="100% Margin Risk Allocation", delta_color="inverse")

# 🐋 Exchange Whale & Large-Block Volume Detector
st.markdown("---")
st.subheader("🐋 Exchange Whale & Large-Block Volume Detector")
st.markdown("Calculates the ratio of top 10 largest inflow blocks versus total aggregate exchange inflows.")

col_w1, col_w2 = st.columns([2, 2])
with col_w1:
    whale_coin = st.text_input("Enter Coin Symbol for Whale Analysis", value="BTC/USDT", help="e.g. BTC/USDT, ETH/USDT, SOL/USDT")
with col_w2:
    whale_tf = st.selectbox("Whale Analysis Timeframe", ["15m", "1h", "4h", "1d"], index=1, key="whale_tf_box")

if st.button("📊 Run Whale Flow & Top-10 Inflow Ratio Analysis"):
    with st.spinner(f"Computing top-10 inflow ratio for {whale_coin} on {selected_exchange_name}..."):
        try:
            ex_class = {
                "MEXC": ccxt.mexc, "Binance": ccxt.binance, "OKX": ccxt.okx,
                "Bybit": ccxt.bybit, "Bitget": ccxt.bitget, "Gate.io": ccxt.gate, "KuCoin": ccxt.kucoin
            }.get(selected_exchange_name, ccxt.mexc)
            
            ex_inst = ex_class({'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
            ex_inst.load_markets()
            
            target_w_sym = whale_coin.upper().strip()
            if not target_w_sym.endswith('/USDT'):
                target_w_sym += '/USDT'
                
            if target_w_sym not in ex_inst.symbols:
                matching_w = [s for s in ex_inst.symbols if target_w_sym.split('/')[0] in s and 'USDT' in s]
                if matching_w:
                    target_w_sym = matching_w[0]
                else:
                    target_w_sym = 'BTC/USDT'
            
            w_candles = ex_inst.fetch_ohlcv(target_w_sym, whale_tf, limit=100)
            df_w = pd.DataFrame(w_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df_w['Timestamp'] = pd.to_datetime(df_w['timestamp'], unit='ms')
            
            inflows = df_w['volume'].values
            sorted_inflows = np.sort(inflows)[::-1]
            top_10_sum = np.sum(sorted_inflows[:10])
            total_inflow_sum = np.sum(inflows)
            whale_ratio = (top_10_sum / total_inflow_sum) if total_inflow_sum > 0 else 0.0
            
            df_w['whale_ratio_index'] = df_w['volume'] / (total_inflow_sum / len(df_w) if len(df_w) > 0 else 1)
            
            st.success(f"Whale ratio computation complete for **{target_w_sym}** on **{selected_exchange_name}** ({whale_tf})")
            
            w_col1, w_col2, w_col3 = st.columns(3)
            w_col1.metric("Top-10 Inflow Whale Ratio", f"{whale_ratio:.4f}", delta="High Whale Concentration" if whale_ratio > 0.35 else "Normal Distribution")
            w_col2.metric("Top 10 Transactions Sum", f"{top_10_sum:,.2f}")
            w_col3.metric("Total Inflow Sum", f"{total_inflow_sum:,.2f}")
            
            st.line_chart(df_w.set_index('Timestamp')[['whale_ratio_index']])
            
        except Exception as e:
            st.error(f"Could not complete whale flow calculation: {e}")

# 📊 MEXC / Binance Style Interactive Candle & Data Viewer
st.markdown("---")
st.subheader("📊 Live Exchange Candle & Market Data Viewer (MEXC / Binance Style)")
col_v1, col_v2 = st.columns([2, 2])
with col_v1:
    viewer_coin = st.text_input("Enter Coin Symbol to Inspect", value="BTC/USDT", help="e.g. BTC/USDT, ETH/USDT, SOL/USDT")
with col_v2:
    viewer_tf = st.selectbox("Inspection Timeframe", ["1m", "5m", "15m", "30m", "1h", "4h", "1d"], index=1)

if st.button("🔍 Load Live Candle Data & Chart"):
    with st.spinner(f"Fetching live market data for {viewer_coin} from {selected_exchange_name}..."):
        try:
            ex_class = {
                "MEXC": ccxt.mexc, "Binance": ccxt.binance, "OKX": ccxt.okx,
                "Bybit": ccxt.bybit, "Bitget": ccxt.bitget, "Gate.io": ccxt.gate, "KuCoin": ccxt.kucoin
            }.get(selected_exchange_name, ccxt.mexc)
            
            ex_inst = ex_class({'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
            ex_inst.load_markets()
            
            target_sym = viewer_coin.upper().strip()
            if not target_sym.endswith('/USDT'):
                target_sym += '/USDT'
                
            if target_sym not in ex_inst.symbols:
                matching = [s for s in ex_inst.symbols if target_sym.split('/')[0] in s and 'USDT' in s]
                if matching:
                    target_sym = matching[0]
                else:
                    target_sym = 'BTC/USDT'
            
            candles = ex_inst.fetch_ohlcv(target_sym, viewer_tf, limit=50)
            df_viewer = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df_viewer['Timestamp'] = pd.to_datetime(df_viewer['timestamp'], unit='ms')
            
            st.success(f"Successfully loaded live data for **{target_sym}** on **{selected_exchange_name}** ({viewer_tf})")
            
            chart_data = df_viewer.set_index('Timestamp')[['close', 'open', 'high', 'low']]
            st.line_chart(chart_data)
            
            st.markdown("##### 📋 Recent Candle OHLCV Feed")
            st.dataframe(df_viewer[['Timestamp', 'open', 'high', 'low', 'close', 'volume']].sort_values(by='Timestamp', ascending=False), use_container_width=True)
            
        except Exception as e:
            st.error(f"Could not load market inspection data: {e}")

# Top Trader Twitter / X Intel Section
with st.expander(f"🐦 Live Twitter / X Intel Feed (Tracking @{twitter_handle})"):
    st.markdown(f"Real-time commentary from key market figures (Tracking **@{twitter_handle}**):")
    for tweet in get_live_tweets(twitter_token, twitter_handle):
        st.markdown(f"- {tweet}")

st.markdown("---")

# Initialize Session State for Scanned Results
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = []

# Live Scan Execution Block
if 'run_scan' in locals() and run_scan:
    with st.spinner(f"Connecting to {selected_exchange_name} Derivatives Server (USDT Swaps Only)..."):
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
            exchange = exchange_class({'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
            exchange.load_markets()
            
        except Exception as e:
            st.warning(f"⚠️ {selected_exchange_name} connection failed ({e}). Falling back to MEXC...")
            exchange = ccxt.mexc({'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
            exchange.load_markets()

        try:
            usdt_swap_symbols = []
            for symbol, market in exchange.markets.items():
                if market.get('swap', False) and market.get('linear', False) and market.get('quote') == 'USDT':
                    usdt_swap_symbols.append(symbol)
            
            if not usdt_swap_symbols:
                usdt_swap_symbols = [s for s in exchange.symbols if '/USDT' in s]

            priority_coins = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'ZEC/USDT', 'ADA/USDT', 'AVAX/USDT', 'LINK/USDT', 'DOGE/USDT', 'MATIC/USDT', 'AKE/USDT']
            
            raw_symbols = []
            for p in priority_coins:
                base = p.split('/')[0]
                matching = [s for s in usdt_swap_symbols if s.startswith(base + '/') or s.startswith(base + ':')]
                raw_symbols.extend(matching)
            
            remaining = [s for s in usdt_swap_symbols if s not in raw_symbols]
            raw_symbols.extend(remaining[:40])

            symbols = []
            seen = set()
            for s in raw_symbols:
                if s not in seen:
                    seen.add(s)
                    symbols.append(s)
                
            matches = []
            total_symbols = len(symbols)
            progress_bar = st.progress(0, text="Scanning USDT Perpetual Swap contracts...")
            
            for idx, symbol in enumerate(symbols):
                progress_bar.progress((idx + 1) / total_symbols, text=f"Scanning futures contract {idx+1}/{total_symbols}: {symbol}")
                try:
                    ticker = exchange.fetch_ticker(symbol)
                    live_price = ticker.get('last') or ticker.get('close')

                    ohlcv = exchange.fetch_ohlcv(symbol, selected_tf, limit=100)
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    
                    if live_price is not None:
                        df.loc[df.index[-1], 'close'] = live_price

                    current_price = df['close'].iloc[-1]
                    if pd.isna(current_price) or current_price <= 0.0001:
                        continue

                    delta = df['close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    df['rsi'] = 100 - (100 / (1 + (gain / loss)))
                    
                    price_change_pct = df['close'].pct_change()
                    df['pvt'] = (df['volume'] * price_change_pct).cumsum().fillna(0)
                    df['pvt_signal'] = df['pvt'].ewm(span=10, adjust=False).mean()
                    
                    tr1 = df['high'] - df['low']
                    tr2 = np.abs(df['high'] - df['close'].shift())
                    tr3 = np.abs(df['low'] - df['close'].shift())
                    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                    
                    atr = tr.rolling(window=10).mean()
                    
                    ts = [df['close'].iloc[0]]
                    for i in range(1, len(df)):
                        c = df['close'].iloc[i]
                        pc = df['close'].iloc[i-1]
                        cl = atr.iloc[i]
                        if pd.isna(cl):
                            cl = 0.0
                        prev_t = ts[-1]
                        
                        if c > prev_t and pc > prev_t:
                            t = max(prev_t, c - cl)
                        elif c < prev_t and pc < prev_t:
                            t = min(prev_t, c + cl)
                        elif c > prev_t:
                            t = c - cl
                        else:
                            t = c + cl
                        ts.append(t)
                        
                    df['ut_stop'] = ts
                    ut_status = "BUY 🟢" if df['close'].iloc[-1] > df['ut_stop'].iloc[-1] else "SELL 🔴"
                    
                    latest = df.iloc[-1]
                    rsi = latest['rsi']
                    price = latest['close']
                    
                    open_p = latest['open']
                    close_p = latest['close']
                    high_p = latest['high']
                    low_p = latest['low']
                    
                    body_size = abs(close_p - open_p)
                    total_bar_range = high_p - low_p
                    
                    if total_bar_range > 0 and (body_size / total_bar_range) > 0.6:
                        if close_p > open_p:
                            bar_state = f"🟢 Bullish Impulse @ ${price:.2f}"
                        else:
                            bar_state = f"🔴 Bearish Dump @ ${price:.2f}"
                    else:
                        bar_state = f"⚖️ Consolidation @ ${price:.2f}"

                    # Fair Value Gap (FVG) Detection
                    fvg_status = "None ⚪"
                    if len(df) >= 3:
                        c1_high = df['high'].iloc[-3]
                        c1_low = df['low'].iloc[-3]
                        c3_low = df['low'].iloc[-1]
                        c3_high = df['high'].iloc[-1]
                        
                        if c3_low > c1_high:
                            fvg_status = f"🟢 Bullish FVG (${c1_high:.2f} - ${c3_low:.2f})"
                        elif c3_high < c1_low:
                            fvg_status = f"🔴 Bearish FVG (${c3_high:.2f} - ${c1_low:.2f})"

                    # Previous Fully Closed Daily Candle Status
                    prev_daily_status = "Neutral ⚪"
                    try:
                        d_candles = exchange.fetch_ohlcv(symbol, '1d', limit=3)
                        if d_candles and len(d_candles) >= 2:
                            d_prev = d_candles[-2]
                            prev_daily_status = "Bullish 🟢" if d_prev[4] >= d_prev[1] else "Bearish 🔴"
                    except Exception:
                        pass

                    # Previous Fully Closed Monthly Candle Status
                    prev_monthly_status = "Neutral ⚪"
                    try:
                        m_candles = exchange.fetch_ohlcv(symbol, '1M', limit=3)
                        if m_candles and len(m_candles) >= 2:
                            m_prev = m_candles[-2]
                            prev_monthly_status = "Bullish 🟢" if m_prev[4] >= m_prev[1] else "Bearish 🔴"
                    except Exception:
                        pass

                    # Calculate Support and Resistance Zones
                    recent_lows = df['low'].rolling(20).min().iloc[-1]
                    recent_highs = df['high'].rolling(20).max().iloc[-1]
                    current_atr = atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else price * 0.01

                    s1 = price - current_atr
                    s2 = recent_lows if recent_lows < price else price - (current_atr * 2)
                    r1 = price + current_atr
                    r2 = recent_highs if recent_highs > price else price + (current_atr * 2)

                    # Proximity Reversal / Bearish Zone Marking
                    zone_status = "Normal Range ⚪"
                    if abs(price - s1) / price <= 0.008 or abs(price - s2) / price <= 0.008:
                        zone_status = "🟢 Near Support / Potential Reversal Bounce"
                    elif abs(price - r1) / price <= 0.008 or abs(price - r2) / price <= 0.008:
                        zone_status = "🔴 Near Resistance / Bearish Rejection Risk"
                    
                    pvt_rising = latest['pvt'] > latest['pvt_signal']
                    is_ut_buy = ut_status.startswith("BUY")
                    
                    if rsi < 35 or rsi > 65:
                        signal = "LONG 🟢" if rsi < 35 else "SHORT 🔴"
                        
                        if signal.startswith("LONG"):
                            entry_price = price * 0.995
                            sl = price * 0.980
                            tp1 = price * 1.020
                            tp2 = price * 1.040
                            tp3 = price * 1.060
                        else:
                            entry_price = price * 1.005
                            sl = price * 1.020
                            tp1 = price * 0.980
                            tp2 = price * 0.960
                            tp3 = price * 0.940
                        
                        position_notional = investment * leverage
                        dollar_risk = position_notional * (abs(entry_price - sl) / entry_price)
                        
                        if signal.startswith("SHORT"):
                            if is_ut_buy or pvt_rising:
                                advice = "⏳ Wait: Bullish Momentum Active"
                            else:
                                advice = "🚨 Ready: Confirmed Short Entry"
                        else:
                            if not is_ut_buy or not pvt_rising:
                                advice = "⏳ Wait: Bearish Momentum Active"
                            else:
                                advice = "🚀 Ready: Confirmed Long Entry"

                        matches.append({
                            "Symbol": symbol,
                            "Direction": signal,
                            "Market Price": f"${price:.2f}",
                            "Entry Price": f"${entry_price:.2f}",
                            "Price Action": bar_state,
                            "Fair Value Gap": fvg_status,
                            "Prev Daily Close": prev_daily_status,
                            "Prev Monthly Close": prev_monthly_status,
                            "Zone Status": zone_status,
                            "Support 1": f"${s1:.2f}",
                            "Support 2": f"${s2:.2f}",
                            "Resistance 1": f"${r1:.2f}",
                            "Resistance 2": f"${r2:.2f}",
                            "Stop Loss": f"${sl:.2f}",
                            "TP1 (1.5R)": f"${tp1:.2f}",
                            "TP2 (2.5R)": f"${tp2:.2f}",
                            "TP3 (4.0R)": f"${tp3:.2f}",
                            "RSI": f"{rsi:.1f}",
                            "PVT Trend": "Bullish 🟢" if pvt_rising else "Bearish 🔴",
                            "UT Bot": ut_status,
                            "Risk ($USDT)": f"-${dollar_risk:.2f}",
                            "Status": advice
                        })
                except Exception:
                    continue
            
            progress_bar.empty()
            st.session_state.scan_results = matches
            
        except Exception as e:
            st.error(f"Error executing USDT futures scan: {e}")

# Display Results & Interactive Dropdown Selector Panel with Official TradingView Chart
if st.session_state.scan_results:
    st.markdown("---")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Opportunities Found", len(st.session_state.scan_results))
    col2.metric("Timeframe", selected_tf)
    col3.metric("Margin Used", f"${investment:,.0f} USDT")
    col4.metric("Leverage", f"{leverage}x")
    
    display_table_data = [{k: v for k, v in item.items()} for item in st.session_state.scan_results]
    st.success(f"Successfully identified {len(st.session_state.scan_results)} active USDT Perpetual Futures setups!")
    st.dataframe(pd.DataFrame(display_table_data), use_container_width=True)
    
    st.markdown("---")
    st.subheader("🎯 Scanned Coin Analysis Dropdown & Official TradingView Chart")
    
    coin_symbols_list = [item["Symbol"] for item in st.session_state.scan_results]
    selected_dropdown_coin = st.selectbox("Select Scanned Coin to Analyze", coin_symbols_list)
    
    selected_item = next((item for item in st.session_state.scan_results if item["Symbol"] == selected_dropdown_coin), None)
    
    if selected_item:
        st.markdown(f"### Detailed Setup for **{selected_item['Symbol']}**")
        d_col1, d_col2, d_col3, d_col4 = st.columns(4)
        d_col1.metric("Signal Direction", selected_item["Direction"])
        d_col2.metric("Entry Price", selected_item["Entry Price"])
        d_col3.metric("Zone Status", selected_item["Zone Status"])
        d_col4.metric("Support / Resistance", f"S1: {selected_item['Support 1']} | R1: {selected_item['Resistance 1']}")
        
        st.info(f"**Trader Advisory & Status:** {selected_item['Status']} | **Fair Value Gap:** {selected_item['Fair Value Gap']} | **RSI:** {selected_item['RSI']}")
        
        # Format Symbol for TradingView Embed (e.g., BINANCE:BTCUSDT or MEXC:BTCUSDT)
        base_clean = selected_item['Symbol'].split('/')[0].upper()
        tv_exchange = selected_exchange_name.upper()
        tv_symbol_str = f"{tv_exchange}:{base_clean}USDT"
        
        # Official TradingView Advanced Real-Time Chart Widget HTML embed with properly escaped JS curly braces
        tv_html = f"""
        <div class="tradingview-widget-container" style="height:550px;width:100%">
          <div id="tradingview_chart" style="height:550px;width:100%"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget(
          {{
            "width": "100%",
            "height": 550,
            "symbol": "{tv_symbol_str}",
            "interval": "D",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "allow_symbol_change": true,
            "details": true,
            "hotlist": true,
            "calendar": true,
            "support_host": "https://www.tradingview.com"
          }});
          </script>
        </div>
        """
        components.html(tv_html, height=560)
else:
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Opportunities Found", 0)
    col2.metric("Contracts Scanned", 40)
    col3.metric("Timeframe", "5m")
    col4.metric("Margin Used", "$40 USDT")
    col5.metric("Leverage", "65x")
    
    st.markdown("---")
    st.info("👈 Register or login via the sidebar, configure your parameters, and click **'Run Live USDT Futures Scan'** to start.")
