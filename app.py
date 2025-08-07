from flask import Flask, render_template, jsonify
import requests
from datetime import datetime
import pytz

app = Flask(__name__)

API_KEY = "b7ea33d435964da0b0a65b1c6a029891"
PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "EUR/JPY", "AUD/CAD"]
IST = pytz.timezone("Asia/Kolkata")

candle_cache = {}
history = {pair: {"correct": 0, "total": 0} for pair in PAIRS}

def fetch_candles(pair, count=30):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=5min&outputsize={count}&apikey={API_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()
        return data.get("values", [])[::-1]  # reverse to oldest → latest
    except Exception as e:
        print(f"Fetch error for {pair}: {e}")
        return []

def detect_trend(candles):
    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]
    if highs[-1] > highs[0] and lows[-1] > lows[0]:
        return "up"
    elif highs[-1] < highs[0] and lows[-1] < lows[0]:
        return "down"
    return "sideways"

def find_snr(candles):
    levels = []
    for i in range(2, len(candles) - 2):
        high = float(candles[i]["high"])
        low = float(candles[i]["low"])
        if high > float(candles[i-1]["high"]) and high > float(candles[i+1]["high"]):
            levels.append(high)
        if low < float(candles[i-1]["low"]) and low < float(candles[i+1]["low"]):
            levels.append(low)
    return list(set(levels))

def analyze_cwrv(candles):
    try:
        c1, c2, c3 = candles[-3], candles[-2], candles[-1]

        def parse(c):
            return {
                "open": float(c["open"]),
                "close": float(c["close"]),
                "high": float(c["high"]),
                "low": float(c["low"]),
                "volume": float(c.get("volume", 0))
            }

        C1 = parse(c1)
        C2 = parse(c2)
        C3 = parse(c3)

        def direction(c): return "CALL" if c["close"] > c["open"] else "PUT"
        dir1, dir2, dir3 = direction(C1), direction(C2), direction(C3)

        reasons = []
        take_trade = False

        if dir2 != dir1 and dir3 == dir1:
            reasons.append("CWRV 123 pattern confirmed")
            take_trade = True
        else:
            reasons.append("CWRV pattern not confirmed")

        return {
            "direction": dir3 if take_trade else "N/A",
            "reason": reasons,
            "status": "Take Trade" if take_trade else "No Trade",
            "candle": {
                "open": C3["open"], "close": C3["close"],
                "high": C3["high"], "low": C3["low"]
            }
        }

    except Exception as e:
        return {
            "direction": "N/A",
            "reason": [f"CWRV Error: {str(e)}"],
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
        try:
            # If pair not cached yet, fetch 30 candles and cache
            if pair not in candle_cache:
                candles = fetch_candles(pair, 30)
                if len(candles) < 5:
                    results[pair] = {
                        "direction": "N/A", "status": "Error", "accuracy": 0,
                        "reason": ["Not enough candles to analyze."],
                        "candle": {"open": 0, "close": 0, "high": 0, "low": 0}
                    }
                    continue
                candle_cache[pair] = candles
            else:
                # Check if new candle formed
                latest_time_str = candle_cache[pair][-1]["datetime"]
                latest_time = datetime.strptime(latest_time_str, "%Y-%m-%d %H:%M:%S")
                latest_time_ist = IST.localize(latest_time)

                # Fetch 1 candle and compare
                new_candle = fetch_candles(pair, 1)
                if new_candle:
                    new_time = datetime.strptime(new_candle[0]["datetime"], "%Y-%m-%d %H:%M:%S")
                    new_time_ist = IST.localize(new_time)

                    if new_time_ist > latest_time_ist:
                        candle_cache[pair].append(new_candle[0])
                        if len(candle_cache[pair]) > 30:
                            candle_cache[pair].pop(0)

            candles = candle_cache[pair]
            trend = detect_trend(candles)
            snr = find_snr(candles)
            result = analyze_cwrv(candles)

            result["reason"].insert(0, f"Trend: {trend}")
            result["reason"].insert(1, f"SNR Zones: {len(snr)}")

            predicted = result["direction"]
            actual = "CALL" if candles[-1]["close"] > candles[-1]["open"] else "PUT"

            history[pair]["total"] += 1
            if predicted == actual:
                history[pair]["correct"] += 1

            acc = history[pair]
            result["accuracy"] = round((acc["correct"] / acc["total"]) * 100, 2)
            results[pair] = result

        except Exception as e:
            results[pair] = {
                "direction": "N/A", "status": "Error", "accuracy": 0,
                "reason": [f"Error processing {pair}: {str(e)}"],
                "candle": {"open": 0, "close": 0, "high": 0, "low": 0}
            }

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)