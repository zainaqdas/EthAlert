import ccxt
import pandas as pd
import requests
import time
from ta.momentum import RSIIndicator

# --- Your Telegram bot info ---
TELEGRAM_TOKEN = 'YOUR_BOT_TOKEN'
CHAT_ID = 'YOUR_CHAT_ID'

def send_alert(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def fetch_eth_data():
    binance = ccxt.binance()
    ohlcv = binance.fetch_ohlcv('ETH/USDT', timeframe='1m', limit=100)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
    return df

last_signal = None

while True:
    try:
        df = fetch_eth_data()
        last = df.iloc[-1]
        avg_vol = df['volume'].rolling(20).mean().iloc[-1]

        if last['volume'] > 2 * avg_vol:
            if last['rsi'] > 70 and last_signal != 'overbought':
                send_alert(f"🚨 ETH Overbought + Volume Surge!\nRSI: {last['rsi']:.2f}, Volume: {last['volume']:.2f}")
                last_signal = 'overbought'
            elif last['rsi'] < 30 and last_signal != 'oversold':
                send_alert(f"📉 ETH Oversold + Volume Surge!\nRSI: {last['rsi']:.2f}, Volume: {last['volume']:.2f}")
                last_signal = 'oversold'
        else:
            last_signal = None

    except Exception as e:
        print("Error:", e)

    time.sleep(60)
