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
        
        if st.sidebar.button("Register Account
