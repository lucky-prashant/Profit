document.getElementById("analyzeBtn").addEventListener("click", () => {
    const btn = document.getElementById("analyzeBtn");
    btn.disabled = true;
    btn.textContent = "In Progress...";

    fetch("/predict")
        .then(res => res.json())
        .then(data => {
            const resultDiv = document.getElementById("results");
            resultDiv.innerHTML = "";

            for (const pair in data) {
                const item = data[pair];
                const box = document.createElement("div");
                box.className = "result-box";

                const candleColor = item.candle.close > item.candle.open ? "green" : "red";

                box.innerHTML = `
                    <h3>${pair}</h3>
                    <div class="candle ${candleColor}"></div>
                    <p><strong>Prediction:</strong> ${item.direction}</p>
                    <p><strong>Status:</strong> ${item.status}</p>
                    <p><strong>Accuracy:</strong> ${item.accuracy}%</p>
                    <p><strong>Reasons:</strong><br> ${item.reason.join("<br>")}</p>
                `;

                resultDiv.appendChild(box);
            }

            btn.disabled = false;
            btn.textContent = "Analyze";
        })
        .catch(err => {
            alert("Failed to fetch prediction.");
            btn.disabled = false;
            btn.textContent = "Analyze";
        });
});
