import pandas as pd
import numpy as np

def analyze_whale_and_patterns(df):
    """
    Bulletproof analyzer that handles column name casing, short dataframes, 
    and prevents blank white screen crashes.
    """
    # Default return values if anything goes wrong
    default_whale = "Normal"
    default_pattern = "None"

    if df is None or len(df) == 0:
        return default_whale, default_pattern

    try:
        # 1. Normalize column names to lowercase to prevent KeyErrors (e.g. 'Close' -> 'close')
        df.columns = [str(col).lower() for col in df.columns]
        
        # Check if mandatory columns exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                return default_whale, default_pattern

        # 2. Force numeric conversion
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna(subset=required_cols)
        
        # If we have very few candles, still try to calculate what we can without crashing
        if len(df) < 5:
            return default_whale, default_pattern

        # --- WHALE VOLUME DETECTION (Safe Rolling Check) ---
        window_size = min(20, len(df))
        df['vol_ma'] = df['volume'].rolling(window=window_size).mean()
        
        latest_vol = df['volume'].iloc[-1]
        latest_ma = df['vol_ma'].iloc[-1]
        
        if pd.notna(latest_ma) and latest_ma > 0 and latest_vol >= (latest_ma * 3.0):
            whale_status = "🐋 Whale Spike"
        else:
            whale_status = "Normal"

        # --- CANDLESTICK PATTERN RECOGNITION ---
        pattern = "None"
        
        if len(df) >= 3:
            o3, h3, l3, c3 = df['open'].iloc[-3], df['high'].iloc[-3], df['low'].iloc[-3], df['close'].iloc[-3]
            o2, h2, l2, c2 = df['open'].iloc[-2], df['high'].iloc[-2], df['low'].iloc[-2], df['close'].iloc[-2]
            o1, h1, l1, c1 = df['open'].iloc[-1], df['high'].iloc[-1], df['low'].iloc[-1], df['close'].iloc[-1]
            
            # Bullish Morning Star
            if (c3 < o3) and (abs(c2 - o2) < (h2 - l2 + 1e-9) * 0.3) and (c1 > o1) and (c1 > (o3 + c3) / 2):
                pattern = "Bullish Morning Star"
            # Bullish Engulfing
            elif c2 < o2 and c1 > o1 and c1 >= o2 and (c1 - o1) > (o2 - c2):
                pattern = "Bullish Engulfing"
            # Hammer
            elif (h1 - l1) > 3 * (abs(c1 - o1)) and (min(c1, o1) - l1) > 2 * (abs(c1 - o1)):
                pattern = "Bullish Hammer"
            # Evening Star
            elif (c3 > o3) and (abs(c2 - o2) < (h2 - l2 + 1e-9) * 0.3) and (c1 < o1) and (c1 < (o3 + c3) / 2):
                pattern = "Bearish Evening Star"
            # Bearish Engulfing
            elif c2 > o2 and c1 < o1 and c1 <= o2 and (o1 - c1) > (c2 - o2):
                pattern = "Bearish Engulfing"
            # Shooting Star
            elif (h1 - l1) > 3 * (abs(c1 - o1)) and (h1 - max(c1, o1)) > 2 * (abs(c1 - o1)):
                pattern = "Bearish Shooting Star"

        return whale_status, pattern

    except Exception:
        # Failsafe so the app never goes blank white
        return default_whale, default_pattern
