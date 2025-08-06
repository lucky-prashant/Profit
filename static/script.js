function getResults() {
    fetch("/predict").then(res => res.json()).then(data => {
        const container = document.getElementById("results");
        container.innerHTML = "";
        for (const pair in data) {
            const info = data[pair];
            const high = info.candle.high;
            const low = info.candle.low;
            const open = info.candle.open;
            const close = info.candle.close;

            // Prevent div errors when candle data is missing
            if (high === 0 && low === 0) {
                container.innerHTML += `
                    <div class="card">
                        <h3>${pair}</h3>
                        <p style="color:red;">No candle data available</p>
                    </div>`;
                continue;
            }

            // Calculate percentage for wick and body positions
            const range = high - low || 1; // avoid divide by zero
            const bodyHeight = Math.abs(close - open) / range * 100;
            const wickBottom = (Math.min(open, close) - low) / range * 100;

            const candleHTML = `
                <div class="candle">
                    <div class="wick"></div>
                    <div class="body ${info.direction.toLowerCase()}"
                         style="height:${bodyHeight}%; bottom:${wickBottom}%;">
                    </div>
                </div>`;

            const html = `
                <div class="card">
                    <h3>${pair}</h3>
                    ${candleHTML}
                    <p><strong>Prediction:</strong> ${info.direction}</p>
                    <p><strong>Status:</strong> ${info.status}</p>
                    <p><strong>Reason:</strong> ${info.reason.join(", ")}</p>
                    <p><strong>Accuracy:</strong> ${info.accuracy}%</p>
                </div>`;
            container.innerHTML += html;
        }
    });
}
