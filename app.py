import pandas as pd
import numpy as np

def analyze_whale_and_patterns(df):
    """
    Analyzes true per-asset whale volume spikes and detects multiple 
    bullish and bearish candlestick patterns.
    Expects df to have columns: ['open', 'high', 'low', 'close', 'volume']
    """
    if df is None or len(df) < 30:
        return "Normal", "No Pattern"

    try:
        # 1. Ensure numeric data types to prevent calculation crashes
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna()
        if len(df) < 30:
            return "Normal", "No Pattern"

        # --- WHALE VOLUME DETECTION (Per-Asset Rolling Calculation) ---
        # Calculate 20-period moving average of volume for this specific coin
        df['vol_ma20'] = df['volume'].rolling(window=20).mean()
        
        latest_vol = df['volume'].iloc[-1]
        latest_ma = df['vol_ma20'].iloc[-1]
        
        # Whale condition: Current volume is >= 3.0x the 20-period volume MA
        if latest_ma > 0 and latest_vol >= (latest_ma * 3.0):
            whale_status = "🐋 Whale Spike"
        else:
            whale_status = "Normal"

        # --- EXTENSIVE CANDLESTICK PATTERN RECOGNITION ---
        # Extract candle data (Index -3, -2, -1 for multi-candle patterns like Morning/Evening Star)
        o3, h3, l3, c3 = df['open'].iloc[-3], df['high'].iloc[-3], df['low'].iloc[-3], df['close'].iloc[-3]
        o2, h2, l2, c2 = df['open'].iloc[-2], df['high'].iloc[-2], df['low'].iloc[-2], df['close'].iloc[-2]
        o1, h1, l1, c1 = df['open'].iloc[-1], df['high'].iloc[-1], df['low'].iloc[-1], df['close'].iloc[-1]
        
        pattern = "None"
        
        # --- BULLISH PATTERNS ---
        # 1. Morning Star (3-candle bullish reversal)
        if (c3 < o3) and (abs(c2 - o2) < (h2 - l2) * 0.3) and (c1 > o1) and (c1 > (o3 + c3) / 2):
            pattern = "Bullish Morning Star"
            
        # 2. Bullish Engulfing (2-candle bullish reversal)
        elif c2 < o2 and c1 > o1 and c1 >= o2 and (c1 - o1) > (o2 - c2):
            pattern = "Bullish Engulfing"
            
        # 3. Piercing Line (2-candle bullish reversal)
        elif c2 < o2 and c1 > o1 and o1 < l2 and c1 > (o2 + c2) / 2:
            pattern = "Bullish Piercing Line"
            
        # 4. Hammer (1-candle bullish reversal)
        elif (h1 - l1) > 3 * (abs(c1 - o1)) and (min(c1, o1) - l1) > 2 * (abs(c1 - o1)) and (h1 - max(c1, o1)) < (abs(c1 - o1)):
            pattern = "Bullish Hammer"

        # --- BEARISH PATTERNS ---
        # 5. Evening Star (3-candle bearish reversal)
        elif (c3 > o3) and (abs(c2 - o2) < (h2 - l2) * 0.3) and (c1 < o1) and (c1 < (o3 + c3) / 2):
            pattern = "Bearish Evening Star"
            
        # 6. Bearish Engulfing (2-candle bearish reversal)
        elif c2 > o2 and c1 < o1 and c1 <= o2 and (o1 - c1) > (c2 - o2):
            pattern = "Bearish Engulfing"
            
        # 7. Dark Cloud Cover (2-candle bearish reversal)
        elif c2 > o2 and c1 < o1 and o1 > h2 and c1 < (o2 + c2) / 2:
            pattern = "Bearish Dark Cloud Cover"
            
        # 8. Shooting Star (1-candle bearish reversal)
        elif (h1 - l1) > 3 * (abs(c1 - o1)) and (h1 - max(c1, o1)) > 2 * (abs(c1 - o1)) and (min(c1, o1) - l1) < (abs(c1 - o1)):
            pattern = "Bearish Shooting Star"

        return whale_status, pattern

    except Exception as e:
        return "Normal", f"Error: {str(e)}"
