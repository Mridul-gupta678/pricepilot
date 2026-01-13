🛒 PricePilot
Intelligent Price Comparison & Tracking Platform

PricePilot is a modern web application designed to help users make smarter online shopping decisions by tracking product prices and visualizing their historical trends.
The project focuses on real-world system design, scalability, and practical engineering constraints rather than unsafe scraping shortcuts.

🌟 Problem Statement

Online shoppers often face uncertainty while purchasing products:

Is the current price the lowest?

Has the price dropped recently?

Should I buy now or wait?

PricePilot aims to answer these questions by providing:

Price tracking

Historical price visualization

A clean and responsive user interface

A production-aware backend architecture

✨ Features

🔍 Product Price Tracking – Submit a product link to track its price

📉 Price History Storage – Saves historical price data for analysis

📊 Interactive Charts – Visualizes price changes using graphs

🌗 Dark / Light Mode – Premium UI with theme toggle

🌐 RESTful Backend API – Built with FastAPI

🛡️ Graceful Error Handling – Handles blocked or unavailable data safely

🧠 System Architecture

PricePilot follows a decoupled frontend–backend architecture, similar to real industry systems.

Frontend (Static Web App)
        ↓
REST API (FastAPI Backend)
        ↓
Database (Price History)

🖥️ Frontend

Built using HTML, CSS, and JavaScript

Hosted on GitHub Pages

Responsible for:

User interface

User input handling

Data visualization using charts

⚙️ Backend

Built using FastAPI

Hosted on Render

Responsible for:

API endpoints

Data validation

Price history storage

Business logic

🔌 API Endpoints
POST /compare-advanced
Stores product price data (if available).

json
Copy code
{
  "url": "https://example.com/product-link"
}
GET /price-history
Returns historical price data for a given product.

bash
Copy code
/price-history?product_url=...
🛠️ Technology Stack
Layer	Technologies
Frontend	HTML, CSS, JavaScript
Backend	Python, FastAPI
Database	SQLite
Charts	Chart.js
Hosting	GitHub Pages, Render

🚀 Deployment
Frontend → GitHub Pages
Backend → Render (Auto-deployed from GitHub)

This setup allows independent deployment, easy maintenance, and clean separation of concerns.

📦 Deployment Steps
1) Prepare the deployment package
- Build production-ready frontend assets (minify CSS/JS if desired)
- Ensure backend entrypoint: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- Pin dependencies in `requirements.txt` and verify local installs
- Confirm configuration: API base URL in `script.js` auto-detects localhost vs production

2) Set up the target environment
- Provision backend service (Render) with Python runtime
- Configure environment: `PORT` (default 8000), persistent disk for SQLite if needed
- Enable CORS for the frontend origin (GitHub Pages domain)
- Install runtime dependencies using `requirements.txt`

3) Execute the deployment
- Connect Render service to this GitHub repo and select auto-deploy
- Set start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- For frontend, push to `main` with `index.html` at repo root (GitHub Pages)
- Initialize database by hitting `/compare-advanced?mock_mode=true` once (creates tables if not present)

4) Verify the deployment
- Run smoke tests:
  - `GET /health` should return `{"status":"healthy"}`
  - `POST /compare-advanced?mock_mode=true` with `{"url":"https://amazon.in/demo"}` should return product + deal_analysis
- Check service logs and CPU/memory usage in Render dashboard
- Validate frontend → backend integration from browser

5) Finalize the deployment
- Update DNS or Pages custom domain (optional)
- Enable monitoring and alerts (Render health checks + uptime monitors)
- Record deployment details and version in this README

🛑 Rollback Procedures
- Render: use “Rollback” to previous successful build, or redeploy a known-good commit
- Frontend: restore previous commit on GitHub Pages (revert merge or force-push)
- Database: keep regular backups of SQLite file if persistence is enabled
- If API outage occurs, enable `mock_mode` in UI to keep frontend operational

🏷️ Version Information
- Backend API: v2.0.0 (FastAPI, advanced deal analysis, mock mode)
- Frontend: Premium UI with Deal Badges, Savings, chart integration
- Testing: Unit tests for core processing (`tests/test_processing.py`)

🎓 Learning Outcomes
This project demonstrates:

REST API design

Frontend–backend separation

Cloud deployment

Handling real-world scraping limitations

Error-tolerant system design

Data visualization

Production-oriented thinking

🔮 Future Enhancements
🔗 Integration with official e-commerce APIs

🛒 Multi-store price comparison

🤖 AI-based buying recommendations

📆 Best-time-to-buy predictions

👤 User accounts and wishlists

👤 Authors
Mridul Gupta 
Aahona Mukhopadhyay
Krishna Kumar
Engineering Student | Web & Backend Development

This project was built to explore real-world web architecture and constraints, not just academic demos.
