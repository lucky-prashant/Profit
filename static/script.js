async function analyze() {
    const btn = document.getElementById("analyzeBtn");
    btn.innerText = "In Progress...";
    btn.disabled = true;

    try {
        const res = await fetch("/predict");
        const data = await res.json();
        const container = document.getElementById("result-container");
        container.innerHTML = "";

        for (const pair in data) {
            const item = data[pair];
            const box = document.createElement("div");
            box.className = "result-box";

            const candle = item.candle;
            const candleColor = candle.close > candle.open ? "green" : "red";
            const wickTop = candle.high - Math.max(candle.open, candle.close);
            const wickBottom = Math.min(candle.open, candle.close) - candle.low;
            const bodyHeight = Math.abs(candle.close - candle.open);

            box.innerHTML = `
                <h2>${pair}</h2>
                <div class="candle-frame">
                    <div class="wick-top" style="height: ${wickTop * 1000}px;"></div>
                    <div class="body ${candleColor}" style="height: ${bodyHeight * 1000}px;"></div>
                    <div class="wick-bottom" style="height: ${wickBottom * 1000}px;"></div>
                </div>
                <p><strong>Prediction:</strong> ${item.direction}</p>
                <p><strong>Status:</strong> ${item.status}</p>
                <p><strong>Accuracy:</strong> ${item.accuracy}%</p>
                <p><strong>Reasoning:</strong></p>
                <ul>${item.reason.map(r => `<li>${r}</li>`).join("")}</ul>
            `;
            container.appendChild(box);
        }
    } catch (e) {
        alert("Error fetching prediction");
    } finally {
        btn.innerText = "Analyze";
        btn.disabled = false;
    }
}
