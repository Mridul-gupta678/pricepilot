// ================== API BASE (PRODUCTION READY) ==================

// ✅ LIVE BACKEND (Render)
const API_BASE = "https://pricepilot-4.onrender.com";

// ❌ LOCAL (use only if backend running locally)
// const API_BASE = "http://127.0.0.1:8000";


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
        const response = await fetch(`${API_BASE}/compare-advanced`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ url })
        });

        if (!response.ok) {
            throw new Error("Backend error");
        }

        const data = await response.json();

        document.getElementById("liveImage").src = data.image || "";
        document.getElementById("liveTitle").innerText = data.title || "No title found";
        document.getElementById("livePrice").innerText =
            data.price ? "₹ " + data.price : "Price not available";

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
        if (!history || history.length === 0) return;

        // ✅ SAFETY: Chart.js must be loaded
        if (typeof Chart === "undefined") {
            console.warn("Chart.js not loaded");
            return;
        }

        const labels = history.map(item =>
            new Date(item.date).toLocaleDateString()
        );
        const prices = history.map(item => item.price);

        const canvas = document.getElementById("priceChart");
        if (!canvas) return;

        const ctx = canvas.getContext("2d");

        if (priceChart) priceChart.destroy();

        priceChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
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
