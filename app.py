from flask import Flask, render_template, jsonify
import requests
import pytz
from datetime import datetime

app = Flask(__name__)

API_KEY = "b7ea33d435964da0b0a65b1c6a029891"
PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "EUR/JPY", "AUD/CAD"]
IST = pytz.timezone("Asia/Kolkata")

history = {pair: {"correct": 0, "total": 0} for pair in PAIRS}

def fetch_candles(pair):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=5min&outputsize=5&apikey={API_KEY}&dp=5"
        response = requests.get(url, timeout=10)
        data = response.json()

        if "status" in data and data["status"] == "error":
            print(f"API Error for {pair}: {data.get('message', 'Unknown')}")
            return []

        return data.get("values", [])
    except Exception as e:
        print(f"Fetch error for {pair}: {e}")
        return []

def analyze_cwrv_123(pair, candles):
    try:
        c1, c2, c3 = candles[2], candles[1], candles[0]  # oldest to newest

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

        def direction(c):
            return "CALL" if c["close"] > c["open"] else "PUT"

        reasons = []
        take_trade = False

        body1 = abs(C1["close"] - C1["open"])
        wick_top1 = C1["high"] - max(C1["open"], C1["close"])
        wick_bottom1 = min(C1["open"], C1["close"]) - C1["low"]
        vol1 = C1["volume"]

        body2 = abs(C2["close"] - C2["open"])
        vol2 = C2["volume"]

        body3 = abs(C3["close"] - C3["open"])
        vol3 = C3["volume"]

        dir1 = direction(C1)
        dir2 = direction(C2)
        dir3 = direction(C3)

        # Candle 1 checks
        if body1 < 0.0002:
            reasons.append("Candle 1 too weak")
        elif vol1 < vol2:
            reasons.append("Volume dropped after Candle 1")
        else:
            reasons.append("Candle 1 strong body and volume")

        # Candle 2 checks
        if dir2 == dir1:
            reasons.append("Candle 2 same direction (no pullback)")
        elif body2 > body1 * 0.75:
            reasons.append("Candle 2 too strong (not just pullback)")
        elif vol2 > vol1:
            reasons.append("Candle 2 volume too high")
        else:
            reasons.append("Candle 2 is a pullback with rejection")

        # Candle 3 checks
        if dir3 != dir1:
            reasons.append("Candle 3 not aligned with C1")
        elif body3 < body2:
            reasons.append("Candle 3 not stronger than C2")
        elif vol3 < vol2:
            reasons.append("Volume not rising in Candle 3")
        else:
            reasons.append("Candle 3 confirms trend")

        if (
            body1 >= 0.0002 and vol1 > vol2 and
            dir2 != dir1 and vol2 < vol1 and
            dir3 == dir1 and vol3 > vol2
        ):
            take_trade = True
            reasons.append(f"CWRV 123 strategy met → {dir3}")
        else:
            reasons.append("CWRV 123 pattern not fully formed")

        return {
            "direction": dir3 if take_trade else "N/A",
            "reason": reasons,
            "status": "Take Trade" if take_trade else "No Trade",
            "candle": {
                "open": C3["open"],
                "close": C3["close"],
                "high": C3["high"],
                "low": C3["low"]
            }
        }

    except Exception as e:
        return {
            "direction": "N/A",
            "reason": [f"Analysis error for {pair}: {str(e)}"],
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
        candles = fetch_candles(pair)
        if len(candles) >= 3:
            result = analyze_cwrv_123(pair, candles)

            # Get current candle to verify accuracy
            latest = candles[0]
            actual = "CALL" if float(latest["close"]) > float(latest["open"]) else "PUT"
            predicted = result["direction"]

            history[pair]["total"] += 1
            if predicted == actual:
                history[pair]["correct"] += 1

            acc = history[pair]
            result["accuracy"] = round((acc["correct"] / acc["total"]) * 100, 2)
            results[pair] = result
        else:
            results[pair] = {
                "direction": "N/A",
                "reason": [f"Not enough candle data for {pair}"],
                "status": "Error",
                "accuracy": 0,
                "candle": {"open": 0, "close": 0, "high": 0, "low": 0}
            }

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
