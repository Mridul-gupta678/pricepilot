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
  // 🔁 CHANGE: use multi-site comparison
  document.getElementById("compareBtn")?.addEventListener("click", compareAllSites);

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

// ================== MULTI-WEBSITE COMPARISON ==================
async function compareAllSites() {
  const input = document.getElementById("productUrl");
  const query = input.value.trim();

  if (!query) {
    alert("Please enter a product name");
    return;
  }

  // UI loading state
  document.getElementById("liveTitle").innerText = "Comparing prices...";
  document.getElementById("livePrice").innerText = "";
  document.getElementById("liveImage").src = "";

  try {
    const response = await fetch(
      `${API_BASE}/compare-all?query=${encodeURIComponent(query)}`
    );

    if (!response.ok) {
      throw new Error("Backend error");
    }

    const data = await response.json();

    // Filter valid prices
    const validProducts = data.filter(
      (p) => p.price && p.price !== "Unavailable"
    );

    if (validProducts.length === 0) {
      document.getElementById("liveTitle").innerText =
        "No prices found for this product";
      return;
    }

    // Find cheapest product
    const cheapest = validProducts.reduce((a, b) =>
      parseInt(a.price) < parseInt(b.price) ? a : b
    );

    // Update UI
    document.getElementById("liveTitle").innerText =
      `${cheapest.title} (${cheapest.source})`;

    document.getElementById("livePrice").innerText =
      `₹ ${cheapest.price}`;

    document.getElementById("liveImage").src =
      cheapest.image && cheapest.image !== "" ? cheapest.image : "";

  } catch (err) {
    console.error(err);
    document.getElementById("liveTitle").innerText =
      "Unable to compare prices (backend issue)";
  }
}
