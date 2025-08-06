function getResults() {
    fetch("/predict").then(res => res.json()).then(data => {
        const container = document.getElementById("results");
        container.innerHTML = "";
        for (const pair in data) {
            const info = data[pair];
            const html = `
                <div class="card">
                    <h3>${pair}</h3>
                    <div class="candle">
                        <div class="wick" style="height: ${(info.candle.high - info.candle.low) * 10000}px;"></div>
                        <div class="body ${info.direction.toLowerCase()}" style="height: ${Math.abs(info.candle.close - info.candle.open) * 10000}px;"></div>
                    </div>
                    <p><strong>Prediction:</strong> ${info.direction}</p>
                    <p><strong>Status:</strong> ${info.status}</p>
                    <p><strong>Reason:</strong> ${info.reason.join(", ")}</p>
                    <p><strong>Accuracy:</strong> ${info.accuracy}%</p>
                </div>`;
            container.innerHTML += html;
        }
    });
}
