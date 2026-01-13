// ================== CONFIG ==================
const API_BASE = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") 
  ? "http://localhost:8000" 
  : "https://pricepilot-4.onrender.com";

// ================== STATE ==================
let priceChart = null;
const RECENT_KEY = "pricepilot_recent";

// ================== DOM ELEMENTS ==================
const elements = {
  input: document.getElementById("productUrl"),
  btn: document.getElementById("compareBtn"),
  loading: document.getElementById("loadingState"),
  resultSection: document.getElementById("resultSection"),
  liveTitle: document.getElementById("liveTitle"),
  livePrice: document.getElementById("livePrice"),
  liveImage: document.getElementById("liveImage"),
  sourceBadge: document.getElementById("sourceBadge"),
  dealBadge: document.getElementById("dealBadge"),
  savingsBlock: document.getElementById("savingsBlock"),
  savingsPct: document.getElementById("savingsPct"),
  avgPrice: document.getElementById("avgPrice"),
  buyLink: document.getElementById("buyLink"),
  chartCanvas: document.getElementById("priceChart"),
  noDataMsg: document.getElementById("noDataMessage"),
  themeToggle: document.getElementById("themeToggle"),
  recentGrid: document.getElementById("recentGrid"),
  clearHistory: document.getElementById("clearHistory"),
  demoMode: document.getElementById("demoMode"),
};

// ================== INIT ==================
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  loadRecentSearches();

  elements.btn.addEventListener("click", handleSearch);
  elements.input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleSearch();
  });
  
  elements.clearHistory.addEventListener("click", () => {
    localStorage.removeItem(RECENT_KEY);
    loadRecentSearches();
    showToast("History cleared", "success");
  });
});

// ================== THEME LOGIC ==================
function initTheme() {
  const savedTheme = localStorage.getItem("theme");
  const isLight = savedTheme === "light";
  
  if (isLight) {
    document.body.classList.add("light");
    elements.themeToggle.innerHTML = '<i class="fa-solid fa-sun"></i>';
  }

  elements.themeToggle.addEventListener("click", () => {
    document.body.classList.toggle("light");
    const isNowLight = document.body.classList.contains("light");
    elements.themeToggle.innerHTML = isNowLight ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
    localStorage.setItem("theme", isNowLight ? "light" : "dark");
  });
}

// ================== SEARCH LOGIC ==================
async function handleSearch() {
  const url = elements.input.value.trim();
  if (!url) {
    showToast("Please enter a valid product URL", "error");
    return;
  }

  // Reset UI
  elements.loading.classList.remove("hidden");
  elements.resultSection.classList.add("hidden");
  
  // Determine source for badge (optimistic)
  updateSourceBadge(url);

  const isDemo = elements.demoMode.checked;
  const endpoint = `${API_BASE}/compare-advanced${isDemo ? "?mock_mode=true" : ""}`;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    if (!response.ok) throw new Error("Failed to fetch data");

    const data = await response.json();
    
    // Update UI with data
    renderProductData(data, url);
    
    // Save to history
    saveToHistory(data, url);
    
    // Fetch History for Chart
    // Pass the history data directly if available from the advanced endpoint
    if (data.history) {
        renderChart(data.history);
    } else {
        fetchPriceHistory(url);
    }

    elements.loading.classList.add("hidden");
    elements.resultSection.classList.remove("hidden");
    
    // Scroll to results
    elements.resultSection.scrollIntoView({ behavior: "smooth", block: "start" });

  } catch (error) {
    console.error(error);
    elements.loading.classList.add("hidden");
    showToast("Error fetching product data. Please try again.", "error");
  }
}

function updateSourceBadge(url) {
  let source = "Unknown";
  if (url.includes("amazon")) source = "Amazon";
  else if (url.includes("flipkart")) source = "Flipkart";
  else if (url.includes("ajio")) source = "Ajio";
  else if (url.includes("snapdeal")) source = "Snapdeal";
  
  elements.sourceBadge.textContent = source;
}

function renderProductData(data, url) {
  elements.liveTitle.textContent = data.title || "Product Title Unavailable";
  elements.livePrice.textContent = data.price || "Unavailable";
  elements.liveImage.src = data.image || "https://placehold.co/400x400?text=No+Image";
  elements.buyLink.href = url;
  
  if (data.source) {
      elements.sourceBadge.textContent = data.source.replace(" Scraper", "");
  }

  // Render Deal Analysis
  if (data.deal_analysis && data.deal_analysis.score > 0) {
    const analysis = data.deal_analysis;
    
    // Badge
    elements.dealBadge.textContent = analysis.label;
    elements.dealBadge.className = "badge deal-badge"; // reset
    if (analysis.score >= 8) elements.dealBadge.classList.add("good");
    else if (analysis.score >= 5) elements.dealBadge.classList.add("fair");
    else elements.dealBadge.classList.add("bad");
    elements.dealBadge.classList.remove("hidden");

    // Savings
    if (analysis.savings && analysis.savings !== 0) {
      elements.savingsBlock.classList.remove("hidden");
      elements.savingsPct.textContent = Math.round(analysis.savings);
      elements.avgPrice.textContent = analysis.average_price;
    } else {
      elements.savingsBlock.classList.add("hidden");
    }
  } else {
    elements.dealBadge.classList.add("hidden");
    elements.savingsBlock.classList.add("hidden");
  }
}

// ================== HISTORY & RECENT ==================
function saveToHistory(data, url) {
  if (!data.title || data.title === "Unavailable") return;
  
  let history = JSON.parse(localStorage.getItem(RECENT_KEY) || "[]");
  
  // Remove duplicate if exists
  history = history.filter(item => item.url !== url);
  
  // Add new item to start
  history.unshift({
    title: data.title,
    price: data.price,
    image: data.image,
    url: url,
    date: new Date().toISOString()
  });
  
  // Limit to 4 items
  if (history.length > 4) history.pop();
  
  localStorage.setItem(RECENT_KEY, JSON.stringify(history));
  loadRecentSearches();
}

function loadRecentSearches() {
  const history = JSON.parse(localStorage.getItem(RECENT_KEY) || "[]");
  elements.recentGrid.innerHTML = "";
  
  if (history.length === 0) {
    elements.recentGrid.innerHTML = '<p style="color:var(--text-secondary); grid-column: 1/-1;">No recent searches.</p>';
    return;
  }

  history.forEach(item => {
    const div = document.createElement("div");
    div.className = "recent-item";
    div.innerHTML = `
      <img src="${item.image || 'https://placehold.co/100'}" class="recent-img" alt="Product">
      <div class="recent-info">
        <div class="recent-title" title="${item.title}">${item.title}</div>
        <div class="recent-price">₹ ${item.price}</div>
      </div>
    `;
    div.addEventListener("click", () => {
      elements.input.value = item.url;
      handleSearch();
    });
    elements.recentGrid.appendChild(div);
  });
}

// ================== CHART LOGIC ==================
async function fetchPriceHistory(url) {
  try {
    const res = await fetch(`${API_BASE}/price-history?product_url=${encodeURIComponent(url)}`);
    if (!res.ok) return;
    
    const history = await res.json();
    renderChart(history);
  } catch (e) {
    console.error("Chart error", e);
  }
}

function renderChart(historyData) {
  // Destroy existing chart
  if (priceChart) {
    priceChart.destroy();
    priceChart = null;
  }

  if (!historyData || historyData.length === 0) {
    elements.noDataMsg.classList.remove("hidden");
    elements.chartCanvas.classList.add("hidden");
    return;
  }

  elements.noDataMsg.classList.add("hidden");
  elements.chartCanvas.classList.remove("hidden");

  const ctx = elements.chartCanvas.getContext("2d");
  
  // Create Gradient
  const gradient = ctx.createLinearGradient(0, 0, 0, 400);
  gradient.addColorStop(0, 'rgba(59, 130, 246, 0.5)'); // Brand color high opacity
  gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)'); // Fade out

  // Format Data
  // Assuming historyData is [{price: 100, date: "2023-01-01"}, ...]
  // If the backend returns simplified list, adjust accordingly. 
  // Based on previous code, it seemed to return objects with 'price' and 'date' (implied from DB schema)
  
  const labels = historyData.map(d => new Date(d.date).toLocaleDateString());
  const prices = historyData.map(d => parseFloat(d.price.replace(/,/g, '')));

  priceChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Price History (₹)",
          data: prices,
          borderColor: "#3b82f6",
          backgroundColor: gradient,
          borderWidth: 3,
          pointBackgroundColor: "#fff",
          pointBorderColor: "#3b82f6",
          pointRadius: 4,
          pointHoverRadius: 6,
          fill: true,
          tension: 0.4, // Smooth curve
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1e293b',
          titleColor: '#f8fafc',
          bodyColor: '#f8fafc',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          padding: 10,
          displayColors: false,
          callbacks: {
            label: (context) => `₹ ${context.parsed.y}`
          }
        }
      },
      scales: {
        x: {
          grid: { display: false, drawBorder: false },
          ticks: { color: '#94a3b8' }
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false },
          ticks: { color: '#94a3b8', callback: (val) => '₹' + val }
        }
      }
    },
  });
}

// ================== UTILS ==================
function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <i class="fa-solid ${type === 'success' ? 'fa-circle-check' : 'fa-circle-exclamation'}"></i>
    <span>${message}</span>
  `;
  
  container.appendChild(toast);
  
  // Remove after 3 seconds
  setTimeout(() => {
    toast.style.animation = "slideIn 0.3s reverse forwards";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}
