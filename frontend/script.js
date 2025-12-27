// ================== API BASE (PHASE 1.2 CHANGE) ==================

// 🔁 During local development:
const API_BASE = "http://127.0.0.1:8000";

// 🔁 After deployment, this will become:
// const API_BASE = "https://pricepilot-backend.onrender.com";


// ================== GLOBAL STATE ==================

let priceChart = null;


// 🔒 HARD BLOCK ENTER KEY (NO PAGE RELOAD)
window.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
        e.preventDefault();
    }
});


// ================== EVENT BINDING ==================

document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("compareBtn");
    if (btn) {
        btn.addEventListener("click", compareAdvanced);
    }
});


// ================== MAIN FUNCTION ==================

async function compareAdvanced() {
    const input = document.getElementById("productUrl");
    const url = input.value.trim();

    if (!url) {
        alert("Paste a product link");
        return;
    }

    // UI loading
    document.getElementById("liveTitle").innerText = "Loading...";
    document.getElementById("livePrice").innerText = "";
    document.getElementById("liveImage").src = "";

    try {
        const response = await fetch(
            `${API_BASE}/compare-advanced`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url })
            }
        );

        if (!response.ok) {
            throw new Error("Backend error");
        }

        const data = await response.json();

        document.getElementById("liveImage").src = data.image || "";
        document.getElementById("liveTitle").innerText = data.title || "";
        document.getElementById("livePrice").innerText =
            data.price ? "₹ " + data.price : "";

        loadPriceHistory(url);

    } catch (err) {
        console.error(err);
        document.getElementById("liveTitle").innerText = "Error loading data";
    }
}


// ================== PRICE HISTORY ==================

async function loadPriceHistory(url) {
    try {
        const response = await fetch(
            `${API_BASE}/price-history?product_url=${encodeURIComponent(url)}`
        );

        if (!response.ok) return;

        const history = await response.json();
        if (!history.length) return;

        const labels = history.map(i =>
            new Date(i.date).toLocaleDateString()
        );
        const prices = history.map(i => i.price);

        const canvas = document.getElementById("priceChart");
        if (!canvas) return;

        const ctx = canvas.getContext("2d");

        if (priceChart) priceChart.destroy();

        priceChart = new Chart(ctx, {
            type: "line",
            data: {
                labels,
                datasets: [{
                    label: "Price History (₹)",
                    data: prices,
                    borderWidth: 3,
                    tension: 0.3
                }]
            }
        });

    } catch (err) {
        console.error("Graph error:", err);
    }
}
