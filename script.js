// ================== CONFIG ==================
const API_BASE = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") 
  ? "http://localhost:8000" 
  : "https://pricepilot-4.onrender.com";

// ================== STATE ==================
let priceChart = null;
const RECENT_KEY = "pricepilot_recent";

// ================== DOM ELEMENTS ==================
const elements = {
  unified: document.getElementById("unifiedSearch"),
  goBtn: document.getElementById("searchGoBtn"),
  modeContainer: document.getElementById("searchMode"),
  modeButtons: () => Array.from(document.querySelectorAll("#searchMode .seg-btn")),
  modeBadge: document.getElementById("modeBadge"),
  inputIcon: document.getElementById("inputIcon"),
  suggestions: document.getElementById("suggestions"),
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
  initSuggestions();
  elements.goBtn.addEventListener("click", unifiedSearchGo);
  elements.unified.addEventListener("input", updateSuggestions);
  elements.unified.addEventListener("keydown", (e) => {
    if (e.key === "Enter") unifiedSearchGo();
  });
  elements.modeButtons().forEach(btn => {
    btn.addEventListener("click", () => setMode(btn.dataset.mode));
  });
  setMode("product");
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

// ================== SEARCH LOGIC (URL) ==================
async function handleSearch() {
  const url = elements.unified.value.trim();
  if (!url) {
    showToast("Please enter a valid product URL", "error");
    return;
  }

  elements.loading.classList.remove("hidden");
  elements.resultSection.classList.add("hidden");
  
  updateSourceBadge(url);

  const isDemo = elements.demoMode.checked;
  const endpoint = `${API_BASE}/compare-advanced${isDemo ? "?mock_mode=true" : ""}`;

  try {
    const handleResponse = async (response, isMock) => {
      if (!response.ok) {
        throw new Error("Failed to fetch data");
      }
      const data = await response.json();
      const product = data.product || data;
      const viewModel = { ...product, deal_analysis: data.deal_analysis };
      renderProductData(viewModel, url);
      saveToHistory(product, url);
      if (data.history) {
        renderChart(data.history);
      } else {
        fetchPriceHistory(url);
      }
      elements.loading.classList.add("hidden");
      elements.resultSection.classList.remove("hidden");
      elements.resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
      if (isMock) {
        showToast("Showing demo data because live scraping failed", "success");
      }
    };

    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    await handleResponse(response, isDemo);
  } catch (error) {
    console.error(error);
    if (!elements.demoMode.checked) {
      try {
        const fallbackResponse = await fetch(`${API_BASE}/compare-advanced?mock_mode=true`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url }),
        });
        await handleResponse(fallbackResponse, true);
        return;
      } catch (fallbackError) {
        console.error(fallbackError);
      }
    }
    elements.loading.classList.add("hidden");
    showToast("Error fetching product data. Please try again.", "error");
  }
}

// ================== SEARCH BY NAME ==================
const popularProducts = [
  "iPhone 14", "AirPods Pro", "Samsung Galaxy S23", "OnePlus 11R",
  "Sony WH-1000XM5", "Boat Airdopes 141", "Dell Inspiron 15",
  "HP Victus 16", "Nike Running Shoes", "Casio G-Shock"
];

function initSuggestions() {
  elements.suggestions.classList.add("hidden");
}

function updateSuggestions() {
  const q = elements.unified.value.trim();
  if (!q) { elements.suggestions.classList.add("hidden"); return; }
  const recents = JSON.parse(localStorage.getItem(RECENT_KEY) || "[]").map(r => r.title);
  const pool = [...popularProducts, ...recents];
  const matches = pool
    .filter(p => similarity(p, q) >= 0.5 || p.toLowerCase().includes(q.toLowerCase()))
    .slice(0, 6);
  renderSuggestions(matches);
}

function renderSuggestions(list) {
  if (list.length === 0) { elements.suggestions.classList.add("hidden"); return; }
  elements.suggestions.innerHTML = list.map(item => `<div class="suggestion-item">${item}</div>`).join("");
  elements.suggestions.classList.remove("hidden");
  Array.from(elements.suggestions.children).forEach((el) => {
    el.addEventListener("click", () => { elements.unified.value = el.textContent; elements.suggestions.classList.add("hidden"); handleSearchCompare(); });
  });
}

function similarity(a, b) {
  const ed = editDistance(a.toLowerCase(), b.toLowerCase());
  const maxLen = Math.max(a.length, b.length);
  return maxLen ? 1 - (ed / maxLen) : 0;
}

function editDistance(a, b) {
  const dp = Array.from({ length: a.length + 1 }, () => Array(b.length + 1).fill(0));
  for (let i = 0; i <= a.length; i++) dp[i][0] = i;
  for (let j = 0; j <= b.length; j++) dp[0][j] = j;
  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      dp[i][j] = Math.min(
        dp[i - 1][j] + 1,
        dp[i][j - 1] + 1,
        dp[i - 1][j - 1] + cost
      );
    }
  }
  return dp[a.length][b.length];
}

async function handleSearchCompare() {
  const name = elements.unified.value.trim();
  if (!name) { showToast("Please enter a product name", "error"); return; }
  elements.loading.classList.remove("hidden");
  try {
    const res = await fetch(`${API_BASE}/search-compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name })
    });
    if (!res.ok) throw new Error("Search failed");
    const json = await res.json();
    renderComparison(json.results);
    elements.loading.classList.add("hidden");
    showToast(`Compared across ${json.results.length} sources`);
  } catch (e) {
    console.error(e);
    elements.loading.classList.add("hidden");
    showToast("Error during comparison", "error");
  }
}

function renderComparison(items) {
  const containerId = "compareTable";
  let container = document.getElementById(containerId);
  if (!container) {
    container = document.createElement("section");
    container.id = containerId;
    container.className = "compare-section";
    container.innerHTML = `
      <div class="section-header">
        <h3><i class="fa-solid fa-table-columns"></i> Comparison</h3>
        <div class="view-sort-row">
          <select id="sortSelect" class="select">
            <option value="price">Sort: Price</option>
            <option value="rating">Sort: Rating</option>
          </select>
          <div class="view-toggle">
            <button id="viewTable" class="view-btn active" data-view="table">Table</button>
            <button id="viewGrid" class="view-btn" data-view="grid">Grid</button>
          </div>
        </div>
      </div>
      <div id="filterBar" class="filter-bar"></div>
      <div class="table-wrapper">
        <table class="compare-table">
          <thead>
            <tr>
              <th>Store</th><th>Title</th><th>Price (₹)</th><th>Rating</th><th>Availability</th><th>Seller</th><th></th>
            </tr>
          </thead>
          <tbody id="compareBody"></tbody>
        </table>
      </div>
      <div id="compareGrid" class="grid-wrapper hidden"></div>
    `;
    document.querySelector("main.container").prepend(container);
  }
  const tableWrapper = container.querySelector(".table-wrapper");
  const body = document.getElementById("compareBody");
  const sortSelect = document.getElementById("sortSelect");
  const grid = document.getElementById("compareGrid");
  const filterBar = document.getElementById("filterBar");
  const viewTableBtn = document.getElementById("viewTable");
  const viewGridBtn = document.getElementById("viewGrid");
  const sources = Array.from(new Set(items.map(it => it.source).filter(Boolean)));
  filterBar.innerHTML = `
    <div class="filter-bar-inner">
      <div class="filter-group">
        <label for="originFilter">Source</label>
        <select id="originFilter" class="select small-select">
          <option value="all">All</option>
          <option value="feed">Feed</option>
          <option value="live">Live</option>
        </select>
      </div>
      <div class="filter-group">
        <label for="storeFilter">Store</label>
        <select id="storeFilter" class="select small-select">
          <option value="">All stores</option>
          ${sources.map(s => `<option value="${s}">${s}</option>`).join("")}
        </select>
      </div>
      <div class="filter-group">
        <label>Price</label>
        <div class="price-inputs">
          <input id="minPriceFilter" type="number" placeholder="Min" />
          <input id="maxPriceFilter" type="number" placeholder="Max" />
        </div>
      </div>
    </div>
  `;
  const originFilter = document.getElementById("originFilter");
  const storeFilter = document.getElementById("storeFilter");
  const minPriceFilter = document.getElementById("minPriceFilter");
  const maxPriceFilter = document.getElementById("maxPriceFilter");
  let currentView = "table";
  const parsePrice = (p) => {
    if (!p || p === "Unavailable" || p === "Sold Out") return Infinity;
    return parseFloat(String(p).replace(/[^\d.]/g, "")) || Infinity;
  };
  sortSelect.onchange = () => {
    applyFiltersAndSort();
  };
  originFilter.onchange = () => applyFiltersAndSort();
  storeFilter.onchange = () => applyFiltersAndSort();
  minPriceFilter.oninput = () => applyFiltersAndSort();
  maxPriceFilter.oninput = () => applyFiltersAndSort();
  viewTableBtn.onclick = () => {
    currentView = "table";
    viewTableBtn.classList.add("active");
    viewGridBtn.classList.remove("active");
    tableWrapper.classList.remove("hidden");
    grid.classList.add("hidden");
  };
  viewGridBtn.onclick = () => {
    currentView = "grid";
    viewGridBtn.classList.add("active");
    viewTableBtn.classList.remove("active");
    tableWrapper.classList.add("hidden");
    grid.classList.remove("hidden");
  };
  function drawRows(list) {
    const bestIdx = list.length ? list.reduce((best, cur, i, arr) => parsePrice(cur.price) < parsePrice(arr[best].price) ? i : best, 0) : -1;
    body.innerHTML = list.map((it, idx) => `
      <tr class="${idx===bestIdx ? 'best' : ''} ${it.origin === 'feed' ? 'feed-row' : 'live-row'}">
        <td>
          <div class="store-cell">
            <span class="store-name">${it.source||'-'}</span>
            ${it.origin === 'feed' ? "<span class='origin-badge origin-feed'>Feed</span>" : "<span class='origin-badge origin-live'>Live</span>"}
          </div>
        </td>
        <td>${it.title||'-'}</td>
        <td>${it.price||'-'}</td>
        <td>${it.rating||'-'}</td>
        <td>${it.availability||'-'}</td>
        <td>${it.seller||'-'}</td>
        <td>${it.url ? `<a class='btn-buy' target='_blank' href='${it.url}'>Buy Now</a>` : ''}</td>
      </tr>
    `).join("");
  }
  function drawCards(list) {
    grid.innerHTML = list.map(it => `
      <div class="product-card-mini ${it.origin === 'feed' ? 'feed-row' : 'live-row'}">
        <div class="mini-img-wrapper">
          <img src="${it.image || "https://placehold.co/200x200?text=No+Image"}" alt="${it.title || ""}" />
        </div>
        <div class="mini-body">
          <div class="mini-title">${it.title || "-"}</div>
          <div class="mini-meta">
            <span class="mini-price">${it.price || "-"}</span>
            <span class="mini-store">${it.source || "-"}</span>
            <span class="origin-badge ${it.origin === 'feed' ? 'origin-feed' : 'origin-live'}">${it.origin === 'feed' ? "Feed" : "Live"}</span>
          </div>
          <div class="mini-footer">
            <span class="mini-rating">${it.rating || "-"}</span>
            ${it.url ? `<a class="btn-buy mini-buy" target="_blank" href="${it.url}">Visit store</a>` : ""}
          </div>
        </div>
      </div>
    `).join("");
  }
  function applyFiltersAndSort() {
    let list = items.slice();
    const originVal = originFilter.value;
    const storeVal = storeFilter.value;
    const minVal = parseFloat(minPriceFilter.value || "0") || 0;
    const maxValRaw = maxPriceFilter.value;
    const maxVal = maxValRaw ? parseFloat(maxValRaw) || Infinity : Infinity;
    list = list.filter(it => {
      if (originVal !== "all" && it.origin !== originVal) return false;
      if (storeVal && it.source !== storeVal) return false;
      const p = parsePrice(it.price);
      if (p < minVal) return false;
      if (p > maxVal) return false;
      return true;
    });
    const crit = sortSelect.value;
    const sorted = list.sort((a, b) =>
      crit === "rating"
        ? (Number(b.rating || 0) - Number(a.rating || 0))
        : (parsePrice(a.price) - parsePrice(b.price))
    );
    drawRows(sorted);
    drawCards(sorted);
  }
  applyFiltersAndSort();
}
function currentMode() {
  const active = elements.modeButtons().find(b => b.classList.contains("active"));
  return active ? active.dataset.mode : "product";
}
function setMode(mode) {
  elements.modeButtons().forEach(b => b.classList.toggle("active", b.dataset.mode === mode));
  elements.modeBadge.textContent = mode === "product" ? "Product" : "Link";
  elements.inputIcon.className = `fa-solid ${mode === "product" ? "fa-magnifying-glass" : "fa-link"} input-icon`;
  elements.suggestions.classList.toggle("hidden", mode !== "product");
  if (mode === "product") {
    elements.unified.placeholder = "Search products (e.g., iPhone 14, AirPods)";
  } else {
    elements.unified.placeholder = "Paste product link (Amazon, Flipkart, Ajio...)";
  }
}
function unifiedSearchGo() {
  const val = elements.unified.value.trim();
  if (!val) { showToast("Please enter a query", "error"); return; }
  const looksLink = /^https?:\/\//i.test(val);
  elements.suggestions.classList.add("hidden");
  if (looksLink) {
    handleSearch();
  } else {
    handleSearchCompare();
  }
}
function updateSourceBadge(url) {
  let source = "Unknown";
  if (url.includes("amazon")) source = "Amazon";
  else if (url.includes("flipkart")) source = "Flipkart";
  else if (url.includes("ajio")) source = "Ajio";
  else if (url.includes("snapdeal")) source = "Snapdeal";
  else if (url.includes("croma")) source = "Croma";
  else if (url.includes("myntra")) source = "Myntra";
  
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
      setMode("link");
      elements.unified.value = item.url;
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
