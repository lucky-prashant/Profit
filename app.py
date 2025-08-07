from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
import pytz
import requests
import os
import matplotlib.pyplot as plt

app = Flask(__name__)

API_KEY = 'b7ea33d435964da0b0a65b1c6a029891'
PAIRS = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'EUR/JPY', 'AUD/CAD']
SYMBOLS = {
    'EUR/USD': 'EUR/USD',
    'GBP/USD': 'GBP/USD',
    'USD/JPY': 'USD/JPY',
    'EUR/JPY': 'EUR/JPY',
    'AUD/CAD': 'AUD/CAD',
}
CANDLE_DATA = {}
RESULTS = {}
IST = pytz.timezone('Asia/Kolkata')

def fetch_candles(symbol):
    url = f'https://api.twelvedata.com/time_series?symbol={symbol}&interval=5min&outputsize=30&apikey={API_KEY}'
    response = requests.get(url)
    data = response.json()
    candles = []
    for item in data['values'][::-1]:
        candles.append({
            'time': item['datetime'],
            'open': float(item['open']),
            'high': float(item['high']),
            'low': float(item['low']),
            'close': float(item['close']),
        })
    return candles

def draw_candle(candle, pair):
    fig, ax = plt.subplots(figsize=(1.5, 4))
    color = 'green' if candle['close'] > candle['open'] else 'red'
    ax.plot([0, 0], [candle['low'], candle['high']], color='black', linewidth=1)
    bottom = min(candle['open'], candle['close'])
    height = abs(candle['close'] - candle['open'])
    ax.add_patch(plt.Rectangle((-0.2, bottom), 0.4, height, color=color))
    ax.set_xlim(-0.5, 0.5)
    ax.set_ylim(candle['low'] - 0.001, candle['high'] + 0.001)
    ax.axis('off')
    path = f'static/{pair.replace("/", "")}_candle.png'
    plt.savefig(path, bbox_inches='tight', pad_inches=0.05, dpi=100)
    plt.close()
    return path

def detect_trend(candles):
    if candles[-1]['close'] > candles[-5]['close']:
        return 'up'
    elif candles[-1]['close'] < candles[-5]['close']:
        return 'down'
    return 'sideways'

def detect_snr(candles):
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    return max(highs), min(lows)

def apply_cwrv123(candles, trend):
    c1, c2, c3 = candles[-3], candles[-2], candles[-1]
    if trend == 'up' and c2['close'] > c1['close'] and c3['close'] > c2['close']:
        return 'CALL'
    elif trend == 'down' and c2['close'] < c1['close'] and c3['close'] < c2['close']:
        return 'PUT'
    return 'HOLD'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze')
def analyze():
    ist_now = datetime.now(IST)
    for pair in PAIRS:
        symbol = SYMBOLS[pair]
        if pair not in CANDLE_DATA:
            CANDLE_DATA[pair] = fetch_candles(symbol)
        else:
            latest = CANDLE_DATA[pair][-1]['time']
            new_data = fetch_candles(symbol)
            if new_data[-1]['time'] != latest:
                CANDLE_DATA[pair].append(new_data[-1])
                if len(CANDLE_DATA[pair]) > 30:
                    CANDLE_DATA[pair] = CANDLE_DATA[pair][-30:]

        candles = CANDLE_DATA[pair]
        trend = detect_trend(candles)
        snr_high, snr_low = detect_snr(candles)
        decision = apply_cwrv123(candles, trend)
        last_candle = candles[-1]
        img_path = draw_candle(last_candle, pair)

        result = {
            'pair': pair,
            'trend': trend,
            'snr': f'Resistance: {snr_high:.3f}, Support: {snr_low:.3f}',
            'direction': decision,
            'trade': 'Take Trade' if decision in ['CALL', 'PUT'] else 'No Trade',
            'reason': f"Trend: {trend}, SNR: {snr_high:.3f}/{snr_low:.3f}, Pattern: CWRV123",
            'image': '/' + img_path
        }
        RESULTS[pair] = result

    return jsonify(list(RESULTS.values()))

if __name__ == '__main__':
    app.run(debug=True)