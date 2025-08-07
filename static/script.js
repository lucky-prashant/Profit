document.getElementById("analyzeBtn").addEventListener("click", () => {
    const btn = document.getElementById("analyzeBtn");
    btn.textContent = "In Progress...";
    btn.disabled = true;

    fetch("/analyze")
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById("results");
            container.innerHTML = "";

            data.forEach(result => {
                const box = document.createElement("div");
                box.className = "result-box";

                const img = document.createElement("img");
                img.src = result.image;
                img.alt = "candle";

                const title = document.createElement("h3");
                title.textContent = result.pair;

                const dir = document.createElement("p");
                dir.textContent = "Direction: " + result.direction;
                dir.className = result.direction === "CALL" ? "call" : "put";

                const trade = document.createElement("p");
                trade.textContent = "Trade: " + result.trade;

                const reason = document.createElement("p");
                reason.textContent = "Reason: " + result.reason;

                box.appendChild(title);
                box.appendChild(img);
                box.appendChild(dir);
                box.appendChild(trade);
                box.appendChild(reason);

                container.appendChild(box);
            });

            btn.textContent = "Analyze";
            btn.disabled = false;
        })
        .catch(err => {
            alert("Error fetching prediction.");
            btn.textContent = "Analyze";
            btn.disabled = false;
        });
});