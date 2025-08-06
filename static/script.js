let interval = null;

function startPrediction() {
    fetch("/start").then(() => {
        document.getElementById("status").innerText = "Running";
        interval = setInterval(fetchStatus, 3000);
    });
}

function stopPrediction() {
    fetch("/stop").then(() => {
        document.getElementById("status").innerText = "Stopped";
        clearInterval(interval);
    });
}

function fetchStatus() {
    fetch("/status")
    .then(res => res.json())
    .then(data => {
        document.getElementById("status").innerText = data.running ? "Running" : "Stopped";
        const resDiv = document.getElementById("results");
        const acc = document.getElementById("accuracy");
        acc.innerText = data.accuracy !== null ? `${data.accuracy}% (${data.correct}/${data.total})` : "--";

        resDiv.innerHTML = "";
        for (const pair in data.results) {
            const dir = data.results[pair];
            resDiv.innerHTML += `<p><strong>${pair}:</strong> ${dir}</p>`;
        }

        if (Object.keys(data.results).length > 0) {
            document.getElementById("alertSound").play();
        }
    });
}