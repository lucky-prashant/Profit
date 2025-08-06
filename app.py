from flask import Flask, render_template, jsonify, session
import requests
import threading
import time
import os
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = "secret_key"
API_KEY = "b7ea33d435964da0b0a65b1c6a029891"
IST = pytz.timezone("Asia/Kolkata")
PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "EUR/JPY"]

auto_mode = {"running": False, "results": {}, "last_predictions": {}}

def fetch_candles(pair):
    url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=5min&outputsize=10&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data["values"] if "values" in data else []

def analyze_candle(candle):
    open_price = float(candle["open"])
    close_price = float(candle["close"])
    return "CALL (Green)" if close_price > open_price else "PUT (Red)"

def prediction_loop():
    while auto_mode["running"]:
        now = datetime.now(IST)
        if now.minute % 5 == 0 and now.second < 10:
            correct = session.get("correct", 0)
            total = session.get("total", 0)
            results = {}
            for pair in PAIRS:
                candles = fetch_candles(pair)
                if candles:
                    prediction = analyze_candle(candles[0])
                    results[pair] = prediction

                    actual_open = float(candles[0]["open"])
                    actual_close = float(candles[0]["close"])
                    actual = "CALL (Green)" if actual_close > actual_open else "PUT (Red)"

                    if prediction == actual:
                        correct += 1
                    total += 1

            auto_mode["results"] = results
            session["correct"] = correct
            session["total"] = total
            time.sleep(60)
        time.sleep(2)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start")
def start():
    if not auto_mode["running"]:
        auto_mode["running"] = True
        thread = threading.Thread(target=prediction_loop)
        thread.start()
    return jsonify({"status": "started"})

@app.route("/stop")
def stop():
    auto_mode["running"] = False
    return jsonify({"status": "stopped"})

@app.route("/status")
def status():
    correct = session.get("correct", 0)
    total = session.get("total", 0)
    accuracy = round((correct / total) * 100, 2) if total > 0 else None
    return jsonify({
        "running": auto_mode["running"],
        "results": auto_mode["results"],
        "correct": correct,
        "total": total,
        "accuracy": accuracy
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)