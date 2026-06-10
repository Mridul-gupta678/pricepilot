<div align="center">

# 🛒 PricePilot

### Intelligent Price Comparison & Tracking Platform

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Frontend-HTML%20%7C%20CSS%20%7C%20JavaScript-2962FF?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Database-SQLite-455A64?style=for-the-badge&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/Charts-Chart.js-FF6F00?style=for-the-badge&logo=chartdotjs&logoColor=white" />
  <img src="https://img.shields.io/badge/Deployment-Render%20%7C%20GitHub%20Pages-212121?style=for-the-badge" />
</p>

<p align="center">
  <b>A modern full-stack web application that helps users track product prices, analyze price history, and make smarter buying decisions.</b>
</p>

</div>

---

# 📌 Overview

PricePilot is a production-oriented price comparison and tracking platform designed to monitor product prices and visualize historical trends through an interactive dashboard.

Unlike basic academic projects, PricePilot focuses on:

- ⚡ Real-world architecture.
- 🧠 Scalable frontend–backend separation.
- 🛡️ Error-tolerant API design.
- 🎨 Modern premium UI/UX.
- ☁️ Deployment-ready engineering practices.

The platform allows users to track products, monitor price fluctuations, and analyze historical pricing trends before making purchasing decisions.

---

# ✨ Features

## 🔍 Product Price Tracking
Track product prices using product URLs.

## 📉 Historical Price Analysis
Store and analyze historical pricing data over time.

## 📊 Interactive Charts
Visualize pricing trends using Chart.js.

## 🌗 Dark / Light Mode
Modern responsive interface with theme switching.

## ⚡ RESTful API
Fast and scalable backend powered by FastAPI.

## 🛡️ Robust Error Handling
Gracefully handles blocked or unavailable product data.

## ☁️ Cloud Deployment
Independent frontend and backend deployment support.

---

# 🧠 System Architecture

```text
Frontend (Static Web App)
        ↓
REST API (FastAPI Backend)
        ↓
Database (SQLite)
```

PricePilot follows a decoupled architecture similar to modern production systems, enabling independent scaling and deployment.

---

# 🖥️ Frontend

## 🚀 Technologies
- HTML5
- CSS3
- JavaScript

## 🎯 Responsibilities
- User Interface
- Product Input Handling
- API Communication
- Data Visualization
- Theme Management

## 🌐 Hosting
GitHub Pages

---

# ⚙️ Backend

## 🚀 Technologies
- Python
- FastAPI

## 🎯 Responsibilities
- API Endpoints
- Business Logic
- Data Validation
- Historical Data Storage
- Error Management

## ☁️ Hosting
Render

---

# 🗄️ Database

| Database | Purpose |
|----------|----------|
| SQLite | Stores historical product pricing data |

---

# 🔌 API Endpoints

## 📥 POST `/compare-advanced`

Stores and processes product pricing data.

### Request Body

```json
{
  "url": "https://example.com/product-link"
}
```

---

## 📤 GET `/price-history`

Returns historical pricing data for a product.

### Example

```bash
/price-history?product_url=...
```

---

# 🛠️ Tech Stack

| Layer | Technologies |
|------|---------------|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, FastAPI |
| Database | SQLite |
| Charts | Chart.js |
| Hosting | GitHub Pages, Render |

---

# 📂 Project Structure

```bash
PricePilot/
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── routes/
│   └── models/
│
├── tests/
│
├── requirements.txt
│
└── README.md
```

---

# 🚀 Deployment

## 🌐 Frontend Deployment
Hosted using GitHub Pages.

## ⚙️ Backend Deployment
Hosted on Render with auto-deployment from GitHub.

---

# 📦 Deployment Guide

## 1️⃣ Prepare the Project

- Build optimized frontend assets
- Configure production API URLs
- Verify dependencies
- Configure FastAPI entrypoint

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

---

## 2️⃣ Configure Hosting Environment

### Render Setup
- Python Runtime
- Environment Variables
- Persistent Storage (optional)
- CORS Configuration

---

## 3️⃣ Deploy the Application

### Backend
- Connect GitHub repository to Render
- Enable Auto Deploy
- Configure Start Command

### Frontend
- Push frontend files to GitHub Pages branch

---

## 4️⃣ Verify Deployment

### Health Check

```bash
GET /health
```

### Expected Response

```json
{
  "status": "healthy"
}
```

### Test API

```bash
POST /compare-advanced?mock_mode=true
```

---

# 🛑 Rollback Strategy

## Backend
Redeploy previous stable build on Render.

## Frontend
Restore previous GitHub commit.

## Database
Maintain periodic SQLite backups.

---

# 🧪 Testing

## Run Backend Tests

```bash
pytest
```

## Run Local Server

```bash
uvicorn backend.main:app --reload
```

---

# 🏷️ Version Information

| Component | Version |
|----------|----------|
| Backend API | v2.0.0 |
| Frontend UI | Premium Dashboard UI |
| Testing | Unit Tests Included |

---

# 🎯 Learning Outcomes

This project demonstrates:

- REST API Development
- Full-Stack Engineering
- Frontend–Backend Separation
- Cloud Deployment
- Error-Tolerant Architecture
- Data Visualization
- Production-Oriented Thinking

---

# 🔮 Future Enhancements

- 🔗 Official E-Commerce API Integration
- 🛒 Multi-Store Price Comparison
- 🤖 AI-Based Buying Recommendations
- 📆 Best-Time-To-Buy Predictions
- 👤 User Accounts & Wishlists
- 📱 Mobile Responsive Enhancements

---

# 👨‍💻 Authors

## Mridul Gupta
Full-Stack Developer • Backend Engineering

## Aahona Mukhopadhyay
Frontend Developer • UI/UX

## Krishna Kumar
Backend Developer • System Design

---

# ⭐ Support

If you found this project useful, consider giving it a ⭐ on GitHub.

---

# 📄 License

This project is built for educational and learning purposes.

---

# 📬 Contact

### GitHub


### LinkedIn


---

<div align="center">

### 🚀 Built with FastAPI, JavaScript, and Modern Web Technologies

</div>
