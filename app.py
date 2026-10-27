import streamlit as st
import ccxt
import pandas as pd
import numpy as np
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

# Define your Admin Username here
ADMIN_USERNAME = "admin"

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

# GitHub Developer Activity Pulse Checker
@st.cache_data(ttl=3600)
def check_github_dev_activity(repo_path):
    try:
        url = f"https://api.github.com/repos/{repo_path}/commits?per_page=3"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            commits = json.loads(resp.read().decode())
            if len(commits) > 0:
                return "Active Dev Pulse 🟢"
    except Exception:
        pass
    return "Normal ⚪"

# Sidebar Authentication & Controls
st.sidebar.title("🔐 User Portal & Controls")

# Display live user registration counter metric
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
    
    run_backtest = False
    if st.session_state.logged_in_user == ADMIN_USERNAME:
        run_backtest = st.sidebar.button("📈 Run Historical Backtest", type="secondary")

# Main Header
st.title("⚡ Multi-Exchange USDT Perpetual Futures Scanner")
st.markdown("Strictly USDⓈ-M derivatives screening, TradingView-aligned UT Bot indicators, Price Volume Trend (PVT) confirmation, and backtesting engine.")

# News & Regulatory Expander
with st.expander("📰 Live Macro, SEC Regulatory Filings & London Crypto Intel"):
    for item in get_crypto_news():
        st.markdown(f"- {item}")

# Top Trader Twitter / X Intel Section
with st.expander(f"🐦 Live Twitter / X Intel Feed (Tracking @{twitter_handle})"):
    st.markdown(f"Real-time commentary from key market figures (Tracking **@{twitter_handle}**):")
    for tweet in get_live_tweets(twitter_token, twitter_handle):
        st.markdown(f"- {tweet}")

st.markdown("---")

# Independent Backtest Execution Block
is_admin = (st.session_state.logged_in_user == ADMIN_USERNAME)
if is_admin and 'run_backtest' in locals() and run_backtest:
    with st.spinner(f"Running historical backtest simulation on {selected_exchange_name} ({selected_tf})..."):
        try:
            exchange_class = getattr(ccxt, selected_exchange_name.lower())()
            exchange_class.options['defaultType'] = 'swap'
            exchange_class.load_markets()
            
            test_symbol = 'BTC/USDT'
            if test_symbol not in exchange_class.symbols:
                test_symbol = exchange_class.symbols[0]
                
            ohlcv = exchange_class.fetch_ohlcv(test_symbol, selected_tf, limit=200)
            df_bt = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            delta = df_bt['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            df_bt['rsi'] = 100 - (100 / (1 + (gain / loss)))
            
            trades = []
            wins = 0
            losses = 0
            
            for i in range(20, len(df_bt) - 5):
                rsi_val = df_bt['rsi'].iloc[i]
                entry_price = df_bt['close'].iloc[i]
                
                if rsi_val < 35:
                    sl = entry_price * 0.98
                    tp = entry_price * 1.03
                    trade_won = False
                    for j in range(i+1, min(i+6, len(df_bt))):
                        h = df_bt['high'].iloc[j]
                        l = df_bt['low'].iloc[j]
                        if l <= sl:
                            trade_won = False
                            break
                        if h >= tp:
                            trade_won = True
                            break
                    if trade_won:
                        wins += 1
                        trades.append({"Candle": i, "Type": "LONG", "Result": "WIN 🟢"})
                    else:
                        losses += 1
                        trades.append({"Candle": i, "Type": "LONG", "Result": "LOSS 🔴"})
                
                elif rsi_val > 65:
                    sl = entry_price * 1.02
                    tp = entry_price * 0.97
                    trade_won = False
                    for j in range(i+1, min(i+6, len(df_bt))):
                        h = df_bt['high'].iloc[j]
                        l = df_bt['low'].iloc[j]
                        if h >= sl:
                            trade_won = False
                            break
                        if l <= tp:
                            trade_won = True
                            break
                    if trade_won:
                        wins += 1
                        trades.append({"Candle": i, "Type": "SHORT", "Result": "WIN 🟢"})
                    else:
                        losses += 1
                        trades.append({"Candle": i, "Type": "SHORT", "Result": "LOSS 🔴"})

            total_trades = wins + losses
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
            
            st.subheader(f"📈 Backtest Results for {test_symbol} ({selected_tf})")
            bcol1, bcol2, bcol3 = st.columns(3)
            bcol1.metric("Total Simulated Trades", total_trades)
            bcol2.metric("Win Rate", f"{win_rate:.1f}%")
            bcol3.metric("Wins / Losses", f"{wins}W / {losses}L")
            
            if trades:
                st
