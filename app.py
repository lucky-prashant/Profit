from flask import Flask, render_template, jsonify
import requests
import pytz
from datetime import datetime

app = Flask(__name__)

API_KEY = "b7ea33d435964da0b0a65b1c6a029891"
PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "EUR/JPY", "AUD/CAD"]
IST = pytz.timezone("Asia/Kolkata")

history = {pair: {"correct": 0, "total": 0} for pair in PAIRS}

def fetch_candle(pair):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=5min&outputsize=2&apikey={API_KEY}"
        res = requests.get(url, timeout=10)
        data = res.json()
        return data.get("values", [])
    except Exception as e:
        print(f"Error fetching data for {pair}: {e}")
        return []

def analyze(pair, candle):
    try:
        open_p = float(candle["open"])
        close_p = float(candle["close"])
        high = float(candle["high"])
        low = float(candle["low"])

        direction = "CALL" if close_p > open_p else "PUT"
        body = abs(close_p - open_p)
        wick_top = high - max(open_p, close_p)
        wick_bottom = min(open_p, close_p) - low

        reasons = []
        take_trade = False

        # Logic 1: Body size filter
        if body > 0.0002:
            reasons.append("Body is strong")
        else:
            reasons.append("Body is weak")

        # Logic 2: Wick pattern
        if wick_top > wick_bottom:
            reasons.append("Top wick long → Bearish rejection")
        elif wick_bottom > wick_top:
            reasons.append("Bottom wick long → Bullish rejection")
        else:
            reasons.append("Neutral wick")

        # Logic 3: Momentum direction
        if direction == "CALL" and wick_bottom > wick_top and body > 0.0002:
            take_trade = True
            reasons.append("Bullish momentum → Call")
        elif direction == "PUT" and wick_top > wick_bottom and body > 0.0002:
            take_trade = True
            reasons.append("Bearish momentum → Put")
        else:
            reasons.append("Unclear momentum")

        return {
            "direction": direction,
            "reason": reasons,
            "status": "Take Trade" if take_trade else "No Trade",
            "candle": {
                "open": open_p, "close": close_p,
                "high": high, "low": low
            }
        }
    except Exception as e:
        print(f"Analysis error for {pair}: {e}")
        return {
            "direction": "N/A",
            "reason": [f"Error analyzing candle: {str(e)}"],
            "status": "Error",
            "candle": {"open": 0, "close": 0, "high": 0, "low": 0}
        }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict")
def predict():
    results = {}
    for pair in PAIRS:
        data = fetch_candle(pair)
        if len(data) >= 2:
            latest, previous = data[0], data[1]
            result = analyze(pair, previous)

            # Accuracy tracking
            predicted = result["direction"]
            actual = "CALL" if float(latest["close"]) > float(latest["open"]) else "PUT"

            history[pair]["total"] += 1
            if predicted == actual:
                history[pair]["correct"] += 1

            acc = history[pair]
            result["accuracy"] = round((acc["correct"] / acc["total"]) * 100, 2)
            results[pair] = result
        else:
            results[pair] = {
                "direction": "N/A",
                "reason": [f"Data error. Could not fetch candles for {pair}"],
                "status": "Error",
                "accuracy": 0,
                "candle": {"open": 0, "close": 0, "high": 0, "low": 0}
            }
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
