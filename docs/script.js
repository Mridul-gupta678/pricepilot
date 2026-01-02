// ================== API BASE ==================
const API_BASE = "https://pricepilot-4.onrender.com";

// ================== GLOBAL STATE ==================
let priceChart = null;

// ================== PREVENT ENTER KEY RELOAD ==================
window.addEventListener("keydown", (e) => {
  if (e.key === "Enter") e.preventDefault();
});

// ================== DOM READY ==================
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("compareBtn")?.addEventListener("click", compareAdvanced);

  // 🌙 Theme toggle
  const toggleBtn = document.getElementById("themeToggle");
  if (!toggleBtn) return;

  const savedTheme = localStorage.getItem("theme");
  if (savedTheme === "light") {
    document.body.classList.add("light");
    toggleBtn.innerText = "☀️";
  } else {
    toggleBtn.innerText = "🌙";
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
  const input = document.getElementById("productUrl");
  const url = input.value.trim();

  if (!url) {
    alert("Please paste a product link");
    return;
  }

  // UI loading state
  document.getElementById("liveTitle").innerText = "Fetching product details...";
  document.getElementById("livePrice").innerText = "";
  document.getElementById("liveImage").src = "";

  try {
    const response = await fetch(`${API_BASE}/compare-advanced`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url }),
    });

    if (!response.ok) {
      throw new Error("Backend error");
    }

    const data = await response.json();

    // ✅ Update UI safely
    document.getElementById("liveTitle").innerText =
      data.title && data.title !== "Unavailable"
        ? data.title
        : "Product data not available";

    document.getElementById("livePrice").innerText =
      data.price && data.price !== "Unavailable"
        ? `₹ ${data.price}`
        : "Price not available";

    document.getElementById("liveImage").src =
      data.image && data.image !== "" ? data.image : "";

    // Load price history if available
    loadPriceHistory(url);

  } catch (err) {
    console.error(err);
    document.getElementById("liveTitle").innerText =
      "Unable to fetch product (blocked by website)";
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
    if (!Array.isArray(history) || history.length === 0) return;

    if (typeof Chart === "undefined") return;

    const labels = history.map((h) =>
      new Date(h.date).toLocaleDateString()
    );
    const prices = history.map((h) => h.price);

    const canvas = document.getElementById("priceChart");
    if (!canvas) return;

    if (priceChart) priceChart.destroy();

    priceChart = new Chart(canvas.getContext("2d"), {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Price History (₹)",
            data: prices,
            borderWidth: 3,
            tension: 0.3,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            display: true,
          },
        },
      },
    });

  } catch (err) {
    console.warn("Price history not available");
  }
}
