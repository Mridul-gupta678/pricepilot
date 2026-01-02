// ================== API BASE ==================
const API_BASE = "https://pricepilot-4.onrender.com";

// ================== GLOBAL STATE ==================
let priceChart = null;

// Prevent Enter key reload
window.addEventListener("keydown", e => {
  if (e.key === "Enter") e.preventDefault();
});

// ================== EVENT BINDING ==================
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("compareBtn")?.addEventListener("click", compareAdvanced);

  // Load theme
  const toggleBtn = document.getElementById("themeToggle");
  if (localStorage.getItem("theme") === "light") {
    document.body.classList.add("light");
    toggleBtn.innerText = "☀️";
  }

  toggleBtn.addEventListener("click", () => {
    document.body.classList.toggle("light");
    const isLight = document.body.classList.contains("light");
    toggleBtn.innerText = isLight ? "☀️" : "🌙";
    localStorage.setItem("theme", isLight ? "light" : "dark");
  });
});

// ================== MAIN FUNCTION ==================
async function compareAdvanced() {
  const url = document.getElementById("productUrl").value.trim();
  if (!url) return alert("Paste a product link");

  document.getElementById("liveTitle").innerText = "Loading...";
  document.getElementById("livePrice").innerText = "";
  document.getElementById("liveImage").src = "";

  try {
    const res = await fetch(`${API_BASE}/compare-advanced`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });

    const data = await res.json();

    document.getElementById("liveImage").src = data.image || "";
    document.getElementById("liveTitle").innerText = data.title || "No title";
    document.getElementById("livePrice").innerText = data.price ? `₹ ${data.price}` : "";

    loadPriceHistory(url);
  } catch {
    document.getElementById("liveTitle").innerText = "Error loading data";
  }
}

// ================== PRICE HISTORY ==================
async function loadPriceHistory(url) {
  const res = await fetch(`${API_BASE}/price-history?product_url=${encodeURIComponent(url)}`);
  const history = await res.json();
  if (!history.length) return;

  if (priceChart) priceChart.destroy();

  priceChart = new Chart(document.getElementById("priceChart"), {
    type: "line",
    data: {
      labels: history.map(h => new Date(h.date).toLocaleDateString()),
      datasets: [{
        label: "Price History (₹)",
        data: history.map(h => h.price),
        borderWidth: 3,
        tension: 0.3
      }]
    }
  });
}
