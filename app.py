from flask import Flask, render_template, request, session
import requests
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key_here"
API_KEY = "b7ea33d435964da0b0a65b1c6a029891"

PAIRS = {
    "EUR/USD": "EUR/USD",
    "GBP/USD": "GBP/USD",
    "USD/JPY": "USD/JPY",
    "EUR/JPY": "EUR/JPY"
}

def fetch_candles(pair):
    url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=5min&outputsize=50&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if "values" not in data:
        return None
    return data["values"]

def is_strong_snr(candles, level, threshold=0.0005, min_touches=3):
    touches = 0
    for c in candles:
        close = float(c['close'])
        if abs(close - level) < threshold:
            touches += 1
    return touches >= min_touches

def is_trend_up(candles, period=20):
    closes = [float(c['close']) for c in candles[:period]]
    return closes[0] > sum(closes)/len(closes)

def is_trend_down(candles, period=20):
    closes = [float(c['close']) for c in candles[:period]]
    return closes[0] < sum(closes)/len(closes)

def is_small_body(candle):
    open_price = float(candle['open'])
    close_price = float(candle['close'])
    high = float(candle['high'])
    low = float(candle['low'])
    body = abs(open_price - close_price)
    total_range = high - low
    return body < 0.2 * total_range

def is_good_time():
    current_utc = datetime.utcnow()
    hour = current_utc.hour
    return 3 <= hour <= 22  # Active market hours in UTC

def analyze_advanced(candles):
    if not is_good_time():
        return "SKIP (Low Volatility Hour)"

    latest = candles[0]
    second_last = candles[1]
    third_last = candles[2]

    # Skip if current candle is too small (doji)
    if is_small_body(second_last):
        return "SKIP (Doji/Small Body)"

    open_price = float(second_last['open'])
    close_price = float(second_last['close'])
    high = float(second_last['high'])
    low = float(second_last['low'])

    body = abs(open_price - close_price)
    wick_top = high - max(open_price, close_price)
    wick_bottom = min(open_price, close_price) - low

    direction = "PUT" if close_price < open_price else "CALL"

    if wick_top > body * 1.5 and close_price < open_price:
        direction = "PUT"
    elif wick_bottom > body * 1.5 and close_price > open_price:
        direction = "CALL"

    # Multi candle confirmation
    prev_dir = "CALL" if float(third_last['close']) > float(third_last['open']) else "PUT"
    if prev_dir != direction:
        return "SKIP (No Multi-Candle Confirmation)"

    # Trend filter
    if direction == "CALL" and not is_trend_up(candles):
        return "SKIP (Against Trend)"
    if direction == "PUT" and not is_trend_down(candles):
        return "SKIP (Against Trend)"

    # SNR Filter
    snr_level = float(second_last['close'])
    if not is_strong_snr(candles, snr_level):
        return "SKIP (Weak SNR Zone)"

    return direction

def update_accuracy(prediction, actual_close, actual_open):
    if prediction.startswith("SKIP"):
        return
    correct = session.get("correct", 0)
    total = session.get("total", 0)
    actual_direction = "CALL" if actual_close > actual_open else "PUT"
    if prediction == actual_direction:
        correct += 1
    total += 1
    session["correct"] = correct
    session["total"] = total

@app.route("/", methods=["GET", "POST"])
def index():
    prediction = None
    selected_pair = "EUR/USD"
    candles = []
    accuracy = None

    if request.method == "POST":
        selected_pair = request.form["pair"]
        candles = fetch_candles(selected_pair)
        if candles:
            prediction = analyze_advanced(candles)
            actual_open = float(candles[0]["open"])
            actual_close = float(candles[0]["close"])
            update_accuracy(prediction, actual_close, actual_open)

    correct = session.get("correct", 0)
    total = session.get("total", 0)
    if total > 0:
        accuracy = round((correct / total) * 100, 2)

    return render_template("index.html", pairs=PAIRS.keys(), prediction=prediction,
                           candles=candles, selected_pair=selected_pair, accuracy=accuracy,
                           total=total, correct=correct)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)