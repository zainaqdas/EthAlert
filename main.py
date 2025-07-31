import ccxt
import pandas as pd
import requests
import time
from ta.momentum import RSIIndicator
from flask import Flask

app = Flask(__name__)  # Minimal web server for Render to keep service alive

TELEGRAM_TOKEN = '8404669597:AAFc3Uf-01CQjR6ApIdRhM3mdGev0PWbL0I'
CHAT_ID = '1315514463'

def send_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

def fetch_data():
    binance = ccxt.binance()
    ohlcv = binance.fetch_ohlcv('ETH/USDT', timeframe='1m', limit=100)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
    return df

# --- Flask Web Route (Required for Render Free Tier) ---
@app.route('/')
def home():
    return "ETH breakout bot is running!"

# --- Start Monitoring Logic in Background ---
import threading
def monitor():
    last_signal = None
    while True:
        try:
            df = fetch_data()
            latest = df.iloc[-1]
            avg_vol = df['volume'].rolling(20).mean().iloc[-1]

            if latest['volume'] > 2 * avg_vol:
                if latest['rsi'] > 70 and last_signal != 'overbought':
                    send_alert(f"🚨 ETH Overbought + Volume Surge!\nRSI: {latest['rsi']:.2f}, Volume: {latest['volume']:.2f}")
                    last_signal = 'overbought'
                elif latest['rsi'] < 30 and last_signal != 'oversold':
                    send_alert(f"📉 ETH Oversold + Volume Surge!\nRSI: {latest['rsi']:.2f}, Volume: {latest['volume']:.2f}")
                    last_signal = 'oversold'
            else:
                last_signal = None

        except Exception as e:
            print("Error:", e)

        time.sleep(60)

# Start the monitor loop in a separate thread
threading.Thread(target=monitor, daemon=True).start()

# Start the Flask app (required by Render)
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
