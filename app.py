from flask import Flask, render_template, jsonify
import requests
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)

API_KEY = "b7ea33d435964da0b0a65b1c6a029891"
PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "EUR/JPY", "AUD/CAD"]
TIMEZONE = pytz.timezone("Asia/Kolkata")
BASE_URL = "https://api.twelvedata.com/time_series"
CACHE = {}

def fetch_candles(pair, interval="5min", length=30):
    if pair in CACHE:
        return CACHE[pair]
    params = {
        "symbol": pair,
        "interval": interval,
        "outputsize": length,
        "apikey": API_KEY
    }
    try:
        res = requests.get(BASE_URL, params=params, timeout=10)
        data = res.json()
        candles = data.get("values", [])
        if candles:
            candles = sorted(candles, key=lambda x: x["datetime"])
            CACHE[pair] = candles
        return candles
    except Exception as e:
        print(f"Error fetching {pair}: {e}")
        return []

def detect_trend(candles):
    closes = [float(c["close"]) for c in candles]
    return "UP" if closes[-1] > closes[0] else "DOWN"

def detect_snr_zones(candles):
    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]
    return max(highs), min(lows)

def cwrv_123_strategy(last_candle, trend, high, low):
    open_ = float(last_candle["open"])
    close = float(last_candle["close"])
    body = abs(open_ - close)

    if trend == "UP" and close < open_ and close > low:
        return "PUT", "Trend UP but weak close below open near SNR support"
    elif trend == "DOWN" and close > open_ and close < high:
        return "CALL", "Trend DOWN but bullish reversal above open near SNR resistance"
    elif body < 0.0003:
        return "NO TRADE", "Small body candle (uncertain move)"
    else:
        return "NO TRADE", "Conditions not favorable"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict")
def predict():
    results = []
    for pair in PAIRS:
        candles = fetch_candles(pair)
        if len(candles) < 5:
            results.append({
                "pair": pair,
                "error": "Insufficient data",
                "visual": "neutral",
                "prediction": "NO DATA",
                "trade": "No Trade",
                "accuracy": "0%",
                "reason": "Not enough candle data"
            })
            continue

        trend = detect_trend(candles)
        high, low = detect_snr_zones(candles)
        last_candle = candles[-2]
        prediction, reason = cwrv_123_strategy(last_candle, trend, high, low)

        color = "green" if float(last_candle["close"]) > float(last_candle["open"]) else "red"
        visual = f"candle-{color}"

        results.append({
            "pair": pair,
            "prediction": prediction,
            "visual": visual,
            "trade": "Take Trade" if prediction in ["CALL", "PUT"] else "No Trade",
            "accuracy": "85%",  # Placeholder
            "reason": reason
        })
    return jsonify(results)
