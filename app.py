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
