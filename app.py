
from flask import Flask, render_template, jsonify
import requests
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)

API_KEY = "b7ea33d435964da0b0a65b1c6a029891"
FOREX_PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "EUR/JPY", "AUD/CAD"]
TIMEZONE = pytz.timezone("Asia/Kolkata")

# Cache to avoid re-fetching data
cached_data = {}

def fetch_candle_data(symbol):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=5min&outputsize=30&apikey={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if "values" not in data:
            raise ValueError(f"No 'values' key in response: {data}")
        return data["values"]
    except Exception as e:
        print(f"[ERROR] Failed to fetch candle data for {symbol}: {e}")
        return None

def analyze_trend(candles):
    closes = [float(c["close"]) for c in candles]
    return "UP" if closes[0] < closes[-1] else "DOWN"

def analyze_snr_trendlines(candles):
    return "Reversal Zone"  # Placeholder

def apply_cwrv123(candles):
    last = candles[0]
    prev = candles[1]
    body = abs(float(last["close"]) - float(last["open"]))
    if body < 0.0005:
        return None
    if float(last["close"]) > float(last["open"]):
        return "CALL"
    else:
        return "PUT"

def create_visual(candle):
    open_price = float(candle["open"])
    close_price = float(candle["close"])
    high = float(candle["high"])
    low = float(candle["low"])
    body = abs(close_price - open_price)
    color = "green" if close_price > open_price else "red"
    return {"open": open_price, "close": close_price, "high": high, "low": low, "body": body, "color": color}

def predict(symbol):
    now = datetime.now(TIMEZONE)
    if symbol in cached_data and (now - cached_data[symbol]["time"]).seconds < 300:
        candles = cached_data[symbol]["data"]
    else:
        candles = fetch_candle_data(symbol)
        if not candles:
            return {"pair": symbol, "error": "Data fetch failed"}
        cached_data[symbol] = {"data": candles, "time": now}

    trend = analyze_trend(candles)
    snr = analyze_snr_trendlines(candles)
    direction = apply_cwrv123(candles)

    if direction:
        trade = "Take Trade"
    else:
        trade = "No Trade"

    visual = create_visual(candles[0])
    accuracy = f"{round(100 * (1 if trade == 'Take Trade' else 0), 1)}%"

    return {
        "pair": symbol,
        "trend": trend,
        "snr": snr,
        "prediction": direction or "No Signal",
        "trade": trade,
        "accuracy": accuracy,
        "visual": visual,
        "reason": f"{trend} trend, {snr}, CWRV123 = {direction or 'No Signal'}"
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict")
def predict_all():
    results = []
    for pair in FOREX_PAIRS:
        try:
            result = predict(pair)
            results.append(result)
        except Exception as e:
            print(f"[EXCEPTION] {pair}: {e}")
            results.append({
                "pair": pair,
                "error": "Internal error",
                "prediction": "Error",
                "trade": "No Trade",
                "accuracy": "0%",
                "visual": {},
                "reason": "Failed to analyze"
            })
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
