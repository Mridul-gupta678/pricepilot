// ========== PRICEPILOT ULTIMATE ENGINE v12.0 ==========
const API_BASE = "http://localhost:8000";
const WATCHLIST_KEY = "pricepilot_watchlist_v12";

// System State
let priceChart = null;
let watchlist = JSON.parse(localStorage.getItem(WATCHLIST_KEY)) || [];
let currentProductData = null;
let lastMarketAvg = 0;

const ui = {
  cursor: document.getElementById("customCursor"),
  input: document.getElementById("unifiedSearch"),
  goBtn: document.getElementById("searchGoBtn"),
  hero: document.getElementById("heroSection"),
  dashboard: document.getElementById("dashboard"),
  watchlistSec: document.getElementById("watchlistSection"),
  watchlistGrid: document.getElementById("watchlistGrid"),
  totalSavings: document.getElementById("totalSavings"),
  loading: document.getElementById("loadingOverlay"),
  suggestions: document.getElementById("suggestions"),
  liveTitle: document.getElementById("liveTitle"),
  livePrice: document.getElementById("livePrice"),
  liveImage: document.getElementById("liveImage"),
  scoreValue: document.getElementById("scoreValue"),
  dealLabel: document.getElementById("dealLabel"),
  pilotScore: document.getElementById("pilotScore"),
  expertVerdict: document.getElementById("expertVerdict"),
  compareBody: document.getElementById("compareBody"),
  setAlertBtn: document.getElementById("setAlert"),
  targetPriceInput: document.getElementById("targetPriceInput"),
  specType: document.getElementById("specType"),
  specDetail: document.getElementById("specDetail"),
  terminal: document.getElementById("terminalBody"),
  ticker: document.getElementById("tickerBody"),
  chatToggle: document.getElementById("chatToggle"),
  chatBox: document.getElementById("chatBox"),
  chatInput: document.getElementById("chatInput"),
  chatSend: document.getElementById("chatSend"),
  chatHistory: document.getElementById("chatHistory")
};

const STORE_PROFILES = { amazon: { ship: 5, ret: 5, pack: 4 }, flipkart: { ship: 4, ret: 4, pack: 4 }, myntra: { ship: 4, ret: 5, pack: 5 }, ajio: { ship: 3, ret: 4, pack: 4 }, croma: { ship: 4, ret: 3, pack: 5 }, snapdeal: { ship: 2, ret: 2, pack: 3 }, default: { ship: 3, ret: 3, pack: 3 } };

// ========== INITIALIZATION ==========
document.addEventListener("DOMContentLoaded", () => {
  initPremiumInteractivity();
  renderWatchlist();
  initClock();
  initAIHandlers();
  initTicker();
  toggleLoader(false);
  logSystem("BOOT_SEQUENCE_COMPLETE", "success");
  logSystem("WAITING_FOR_RETAIL_NODE_IDENTIFICATION", "info");
});

function initPremiumInteractivity() {
  document.addEventListener("mousemove", (e) => {
    ui.cursor.style.left = `${e.clientX}px`; ui.cursor.style.top = `${e.clientY}px`;
    const isHovering = e.target.closest("button, a, input, .bento, .watchlist-card, select");
    ui.cursor.style.opacity = isHovering ? "0.95" : "0.5";
    ui.cursor.style.width = isHovering ? "180px" : "120px";
    ui.cursor.style.height = isHovering ? "180px" : "120px";
  });

  document.addEventListener("mousemove", (e) => {
    const cards = document.querySelectorAll(".bento, .search-hub");
    cards.forEach(card => {
      const rect = card.getBoundingClientRect(); const x = e.clientX - rect.left; const y = e.clientY - rect.top;
      if (x > 0 && x < rect.width && y > 0 && y < rect.height) {
        const xRot = ((y - rect.height / 2) / rect.height) * 10;
        const yRot = ((x - rect.width / 2) / rect.width) * -10;
        card.style.transform = `perspective(1200px) rotateX(${xRot}deg) rotateY(${yRot}deg) translateY(-5px)`;
      } else { card.style.transform = `perspective(1200px) rotateX(0) rotateY(0) translateY(0)`; }
    });
  });

  ui.goBtn.addEventListener("click", runAnalysis);
  ui.input.addEventListener("keydown", (e) => { if (e.key === "Enter") runAnalysis(); });
  ui.setAlertBtn.addEventListener("click", toggleAlert);
}

// ========== ADVANCED AI CHAT ==========
function initAIHandlers() {
  ui.chatToggle.onclick = () => ui.chatBox.classList.toggle("hidden");
  ui.chatSend.onclick = handleAIChat;
  ui.chatInput.onkeydown = (e) => { if (e.key === "Enter") handleAIChat(); };
}

function handleAIChat() {
  const q = ui.chatInput.value.trim(); if (!q) return;
  addChatMessage("USER", q); ui.chatInput.value = "";
  
  setTimeout(() => {
    let reply = "I am currently analyzing the market nodes. Please provide a specific product node first.";
    if (currentProductData) {
      const qLower = q.toLowerCase();
      if (qLower.includes("price") || qLower.includes("buy")) {
        const score = parseFloat(ui.pilotScore.textContent);
        reply = score > 8 ? "Market analysis indicates an ELITE buying window. The current valuation is significantly below the 30-day mean." : "My neural forecast suggests waiting. Current volatility indices are high.";
      } else if (qLower.includes("store") || qLower.includes("trust")) {
        reply = `Node ${currentProductData.source.toUpperCase()} shows stable logistics metrics with high package safety scores.`;
      } else {
        reply = `Target product: ${currentProductData.title.substring(0,30)}... Analysis complete. PILOT_SCORE: ${ui.pilotScore.textContent}.`;
      }
    }
    addChatMessage("AI", reply);
  }, 800);
}

function addChatMessage(role, msg) {
  const div = document.createElement("div");
  div.style.cssText = role === "AI" ? "background:rgba(255,255,255,0.03); padding:0.8rem; border-radius:12px; align-self:flex-start;" : "background:var(--primary); color:#000; padding:0.8rem; border-radius:12px; align-self:flex-end; font-weight:700;";
  div.textContent = msg;
  ui.chatHistory.appendChild(div);
  ui.chatHistory.scrollTop = ui.chatHistory.scrollHeight;
}

// ========== TERMINAL & TICKER ==========
function logSystem(msg, type = "info") {
  const line = document.createElement("div");
  line.className = `term-line ${type}`;
  line.innerHTML = `[${new Date().toLocaleTimeString()}] <b>${type.toUpperCase()}</b>: ${msg}`;
  ui.terminal.appendChild(line);
  ui.terminal.scrollTop = ui.terminal.scrollHeight;
}

function initTicker() {
  setInterval(() => {
    const items = ui.ticker.querySelectorAll(".ticker-item");
    const item = items[Math.floor(Math.random() * items.length)];
    const price = parseInt(item.querySelector("b").textContent.replace(/[₹,]/g, ""));
    const change = (Math.random() * 200 - 100).toFixed(0);
    const newPrice = price + parseInt(change);
    item.querySelector("b").textContent = `₹${newPrice.toLocaleString()}`;
    const icon = item.querySelector("i");
    if (change > 0) { icon.className = "fa-solid fa-caret-up"; icon.style.color = "var(--accent)"; }
    else { icon.className = "fa-solid fa-caret-down"; icon.style.color = "var(--alert)"; }
  }, 5000);
}

// ========== CORE ENGINE ==========
async function runAnalysis() {
  const query = ui.input.value.trim(); if (!query) return;
  toggleLoader(true); logSystem(`IDENTIFYING_NODE: ${query.substring(0,20)}...`, "info");
  try {
    const isLink = /^https?:\/\//i.test(query); let results = [];
    if (isLink) {
      logSystem("SCANNING_REMOTE_RETAIL_NODE", "info");
      const res = await fetch(`${API_BASE}/compare-advanced`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url: query }), });
      const data = await res.json(); currentProductData = data.product || data; renderPrimary(currentProductData, query); if (data.history) renderChart(data.history);
      const sRes = await fetch(`${API_BASE}/search-compare`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: currentProductData.title }), });
      results = (await sRes.json()).results || [];
    } else {
      logSystem("SEARCHING_GLOBAL_MARKET_INDEX", "info");
      const res = await fetch(`${API_BASE}/search-compare`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: query }), });
      results = (await res.json()).results || [];
      if (results.length > 0) { currentProductData = results[0]; renderPrimary(currentProductData, currentProductData.url); fetchHistory(currentProductData.url); }
    }
    if (results.length > 0) { renderTable(results); processMetrics(results); logSystem("MARKET_SCAN_COMPLETE", "success"); }
    
    ui.hero.style.opacity = "0"; ui.hero.style.transform = "translateY(-40px)";
    setTimeout(() => { ui.hero.classList.add("hidden"); ui.dashboard.classList.remove("hidden"); ui.watchlistSec.classList.remove("hidden"); ui.dashboard.style.opacity = "1"; window.scrollTo({ top: 0, behavior: "smooth" }); }, 500);
  } catch (err) { logSystem(`NODE_FAULT: ${err.message}`, "alert"); toggleLoader(false); } finally { toggleLoader(false); }
}

// ========== ADAPTIVE THEMING ==========
function applyTheme(score) {
  let primary = "#cbb26a"; let glow = "rgba(203, 178, 106, 0.2)";
  if (score >= 8.5) { primary = "#10b981"; glow = "rgba(16, 185, 129, 0.2)"; logSystem("ELITE_NODE_DETECTED: OPTIMIZING_FOR_ACQUISITION", "success"); }
  else if (score < 4.5) { primary = "#f87171"; glow = "rgba(248, 113, 113, 0.2)"; logSystem("RISK_PROTOCOL_ACTIVE: VALUATION_VOLATILE", "info"); }
  
  document.documentElement.style.setProperty('--primary', primary);
  document.documentElement.style.setProperty('--theme-glow', glow);
}

// ========== LOGIC ==========
function renderPrimary(product, url) {
  document.querySelector(".b-product").classList.add("data-veins");
  ui.liveTitle.textContent = product.title || "UNKNOWN_ID"; ui.livePrice.textContent = (product.price || "0").toLocaleString("en-IN"); ui.liveImage.src = product.image || "https://placehold.co/400x400?text=NO_IMAGE";
  document.getElementById("sourceTag").textContent = `NODE: ${(product.source || "EXT").toUpperCase()}`;
  const da = product.deal_analysis || { score: 7, label: "STABLE" }; ui.scoreValue.textContent = da.score;
}

function processMetrics(results) {
  const prices = results.map(i => parseFloat(String(i.price).replace(/,/g, "")) || 0).filter(p => p > 0); if (!prices.length) return;
  const low = Math.min(...prices); const avg = prices.reduce((a,b)=>a+b,0)/prices.length; lastMarketAvg = avg;
  const spread = ((avg - low) / avg) * 100; const sentiment = Math.min(Math.max(spread * 2.5, 10), 100);
  const profile = STORE_PROFILES[currentProductData.source.toLowerCase()] || STORE_PROFILES.default;
  const storeScore = (profile.ship + profile.ret + profile.pack) / 1.5;
  const final = (parseInt(ui.scoreValue.textContent) * 0.4) + ((sentiment / 10) * 0.3) + (storeScore * 0.3);
  ui.pilotScore.textContent = final.toFixed(1); ui.expertVerdict.textContent = final > 8.5 ? "ELITE_DEAL" : (final > 7 ? "OPTIMAL" : "RISKY");
  applyTheme(final);
}

function renderTable(items) {
  ui.compareBody.innerHTML = items.map(it => `<tr><td><div class="store-id" style="color:var(--primary);">${it.source.toUpperCase()}</div></td><td><div class="price-id">₹${it.price}</div></td><td style="color:var(--text-dim); font-size:0.8rem; font-family:monospace;">STABILITY_A</td><td><a href="${it.url}" target="_blank" class="search-btn" style="padding:0.6rem 1.4rem; font-size:0.7rem; text-decoration:none; display:inline-block;">VISIT_NODE</a></td></tr>`).join("");
}

function renderChart(data) {
  const ctx = document.getElementById("priceChart").getContext("2d"); if (priceChart) priceChart.destroy();
  const grad = ctx.createLinearGradient(0, 0, 0, 300); grad.addColorStop(0, 'rgba(203, 178, 106, 0.1)'); grad.addColorStop(1, 'rgba(203, 178, 106, 0)');
  priceChart = new Chart(ctx, { type: 'line', data: { labels: data.map(d => new Date(d.date).toLocaleDateString("en-IN", {day:'numeric', month:'short'})), datasets: [{ data: data.map(d => d.price), borderColor: getComputedStyle(document.documentElement).getPropertyValue('--primary').trim(), backgroundColor: grad, borderWidth: 3, pointRadius: 0, tension: 0.4, fill: true }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false }, ticks: { color: '#64748b', font: { size: 10 } } }, y: { grid: { color: 'rgba(255,255,255,0.02)' }, ticks: { color: '#64748b', font: { size: 10 } } } } } });
}

function toggleAlert() {
  const url = ui.setAlertBtn.getAttribute("data-url"); if (!url) return;
  const target = parseFloat(ui.targetPriceInput.value); const product = { title: ui.liveTitle.textContent, price: ui.livePrice.textContent, image: ui.liveImage.src, url, targetPrice: isNaN(target) ? null : target, avgAtTrack: lastMarketAvg };
  const idx = watchlist.findIndex(i => i.url === url);
  if (idx === -1) { watchlist.push(product); logSystem("NODE_ADDED_TO_WATCHLIST", "success"); } else { watchlist.splice(idx, 1); logSystem("NODE_REMOVED", "info"); }
  localStorage.setItem(WATCHLIST_KEY, JSON.stringify(watchlist)); renderWatchlist();
}

function renderWatchlist() {
  if (watchlist.length === 0) { ui.watchlistGrid.innerHTML = '<p style="color:var(--text-dim);">No monitored nodes.</p>'; ui.totalSavings.textContent = "₹0"; return; }
  ui.watchlistGrid.innerHTML = watchlist.map(item => `<div class="bento watchlist-card" style="display:flex; align-items:center; gap:1.5rem; padding:1.5rem; cursor:pointer;" onclick="window.open('${item.url}', '_blank')"><img src="${item.image}" style="width:60px; height:60px; object-fit:contain; background:#fff; border-radius:10px; padding:6px;" /><div style="flex:1; overflow:hidden;"><div style="font-weight:800; font-size:0.9rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${item.title}</div><div style="color:var(--accent); font-weight:800; margin-top:4px;">₹${item.price}</div>${item.targetPrice ? `<div style="font-size:0.6rem; color:var(--primary); font-weight:700; margin-top:2px;">STRIKE: ₹${item.targetPrice}</div>` : ''}</div></div>`).join("");
  let total = 0; watchlist.forEach(i => { if (i.avgAtTrack) total += (i.avgAtTrack - parseFloat(String(i.price).replace(/,/g, ""))); });
  ui.totalSavings.textContent = `₹${Math.max(0, Math.round(total)).toLocaleString()}`;
}

function toggleLoader(on) { ui.loading.classList.toggle("hidden", !on); }
function initClock() { setInterval(() => { const now = new Date(); document.getElementById("systemClock").textContent = `NODE_SYNC: ${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}:${now.getSeconds().toString().padStart(2,'0')} | STATUS: OPTIMAL`; }, 1000); }
function checkStrike(title, price) { const p = parseFloat(String(price).replace(/,/g, "")); watchlist.forEach(i => { if (i.title === title && i.targetPrice && p <= i.targetPrice) alert(`TARGET_STRIKE: ${title} is now ₹${price}!`); }); }
async function fetchHistory(url) { try { const res = await fetch(`${API_BASE}/price-history?product_url=${encodeURIComponent(url)}`); if (res.ok) { const h = await res.json(); if (h.length > 0) renderChart(h); } } catch (e) {} }
