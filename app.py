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
    url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=5min&outputsize=2&apikey={API_KEY}"
    res = requests.get(url).json()
    return res.get("values", [])

def analyze(pair, candle):
    open_p = float(candle["open"])
    close_p = float(candle["close"])
    high = float(candle["high"])
    low = float(candle["low"])
    direction = "CALL" if close_p > open_p else "PUT"
    body = abs(close_p - open_p)
    wick_top = high - max(open_p, close_p)
    wick_bottom = min(open_p, close_p) - low

    logic_passed = []
    take_trade = False

    if body > 0.0002:
        logic_passed.append("Body not small")
    else:
        logic_passed.append("Body too small")

    if wick_top > wick_bottom:
        logic_passed.append("Wick confirms reversal")
    else:
        logic_passed.append("Wick does not confirm")

    if "Body not small" in logic_passed and "Wick confirms reversal" in logic_passed:
        take_trade = True

    return {
        "direction": direction,
        "reason": logic_passed,
        "status": "Take Trade" if take_trade else "No Trade",
        "candle": {"open": open_p, "close": close_p, "high": high, "low": low}
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
            predicted = result["direction"]
            actual = "CALL" if float(latest["close"]) > float(latest["open"]) else "PUT"

            history[pair]["total"] += 1
            if predicted == actual:
                history[pair]["correct"] += 1

            acc = history[pair]
            result["accuracy"] = round((acc["correct"] / acc["total"]) * 100, 2) if acc["total"] > 0 else 0
            results[pair] = result
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
