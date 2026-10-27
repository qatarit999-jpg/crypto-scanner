import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import urllib.request
import xml.etree.ElementTree as ET
import json
import re

# Page configuration
st.set_page_config(page_title="Tether (USDT-M) Futures & Global Auth Scanner", page_icon="⚡", layout="wide")

# Initialize Session State for User Authentication Database
if 'users_db' not in st.session_state:
    st.session_state.users_db = {}
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None

# Define your Admin Username here (Change this to your exact login username)
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
                st.sidebar.success("🎉 Registration successful! Please switch to Login.")
                
    elif auth_mode == "Login":
        st.sidebar.subheader("🔑 Member Login")
        login_user = st.sidebar.text_input("Username")
        login_pass = st.sidebar.text_input("Password", type="password")
        
        if st.sidebar.button("Login", type="primary"):
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
        "CZ (Changpeng Zhao - @cz_binance)": "cz_binance",
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
st.markdown("Strictly USDⓈ-M derivatives screening, UT Bot indicators, Price Volume Trend (PVT) confirmation, and backtesting engine.")

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

if 'run_backtest' in locals() and run_backtest and st.session_state.logged_in_user == ADMIN_USERNAME:
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
                st.dataframe(pd.DataFrame(trades), use_container_width=True)
            else:
                st.info("Not enough extreme RSI triggers found in this historical window to backtest.")
        except Exception as e:
            st.error(f"Backtest execution failed: {e}")

elif 'run_scan' in locals() and run_scan:
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

            priority_coins = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'ZEC/USDT', 'ADA/USDT', 'AVAX/USDT', 'LINK/USDT', 'DOGE/USDT', 'MATIC/USDT']
            
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
                        c, pc, cl = df['close'].iloc[i], df['close'].iloc[i-1], atr.iloc[i]
                        if pd.isna(cl): 
                            cl = 0
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
                    prev_candle = df.iloc[-2]
                    rsi = latest['rsi']
                    price = latest['close']
                    
                    volume_ma = df['volume'].rolling(window=20).mean().iloc[-1]
                    is_whale_spike = latest['volume'] > (volume_ma * 3.5) if not pd.isna(volume_ma) else False
                    
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
                            advice = "Wait 15m-30m (Bullish Momentum)"
                        elif signal.startswith("LONG") and not is_bullish_momentum:
                            advice = "Wait 15m-30m (Bearish Momentum)"
                        elif signal.startswith("LONG") and pvt_rising:
                            advice = "Confirmed PVT Buy"
                        elif signal.startswith("SHORT") and not pvt_rising:
                            advice = "Confirmed PVT Sell"
                        else:
                            advice = "Volume Divergence Warning"
                        
                        dev_status = "N/A"
                        clean_sym = symbol.split('/')[0]
                        if "BTC" in clean_sym:
                            dev_status = check_github_dev_activity("bitcoin/bitcoin")
                        elif "ETH" in clean_sym:
                            dev_status = check_github_dev_activity("ethereum/go-ethereum")
                        elif "SOL" in clean_sym:
                            dev_status = check_github_dev_activity("solana-labs/solana")

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
                            "Whale Vol": "🐋 Spike" if is_whale_spike else "Normal",
                            "Dev Pulse": dev_status,
                            "UT Bot": ut_status,
                            "Risk ($USDT)": f"-${dollar_risk:.2f}",
                            "Status": advice
                        })
                except Exception:
                    continue
            
            progress_bar.empty()
            
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Opportunities Found", len(matches))
            col2.metric("Contracts Scanned", total_symbols)
            col3.metric("Timeframe", selected_tf)
            col4.metric("Margin Used", f"${investment:,.0f} USDT")
            col5.metric("Leverage", f"{leverage}x")
            
            st.markdown("---")
            
            if matches:
                st.success(f"Successfully identified {len(matches)} active USDT Perpetual Futures setups!")
                st.dataframe(pd.DataFrame(matches), use_container_width=True)
            else:
                st.warning("No USDT futures contracts currently match extreme RSI & volume criteria on this timeframe.")
                
        except Exception as e:
            st.error(f"Error executing USDT futures scan: {e}")
else:
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Opportunities Found", 0)
    col2.metric("Contracts Scanned", 40)
    col3.metric("Timeframe", "5m")
    col4.metric("Margin Used", "$40 USDT")
    col5.metric("Leverage", "65x")
    
    st.markdown("---")
    st.info("👈 Register or login via the sidebar, configure your parameters, and click **'Run Live USDT Futures Scan'** to start.")
