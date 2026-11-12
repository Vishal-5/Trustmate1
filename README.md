# TRUSTMATE AI — Truecaller for Online Sellers

> **Autonomous Seller Trust & Anti-Fraud Microservice for PayPal**  
> *PayPal AI Hackathon: Build What's Next with PayPal and AI*  

---

## 1. Project Overview

**TRUSTMATE** acts as a pre-checkout trust layer—like **Truecaller for online payments**. 

When shopping online, traditional e-commerce algorithms rank products solely by the lowest price, frequently exposing buyers to newly minted scam storefronts and counterfeit goods. 

TRUSTMATE enforces a strict **Trust-First, Price-Second** golden rule:
* **Hard Safety Gating:** Any seller scoring below **2.5 / 5.0** is flagged as **Risky**, gated, and **never recommended**, no matter how cheap their deal is.
* **Fair Price Comparison:** Price competition only takes place among verified, trusted sellers ($\ge 2.5$).
* **Real-Time Verification:** Before payment is authorized, TRUSTMATE cross-examines the seller across domain records, physical store presence, and threat intelligence feeds.
* **PayPal Pre-Checkout Escrow:** Transactions require explicit human-in-the-loop approval on PayPal Sandbox before any funds can be captured.

---

## 2. Key Features

- **Trust-First Offer Ranking (70/30 Formula):** Blends merchant authenticity (70%) and product price (30%) to prioritize trustworthy merchants over suspicious bargains.
- **Multi-Signal Authenticity Engine:** Evaluates domain age (via RDAP), physical business corroboration (Google Places / OpenStreetMap), website TLS security, and URL reputation (URLhaus).
- **Tap-to-Explain AI Transparency:** An interactive modal breaking down each verification signal with plain-English AI explanations (`explain_score`).
- **Autonomous Fraud Interception:** Double-gated protection—the frontend displays a prominent high-risk warning modal, and the FastAPI backend enforces a strict confirmation check before creating any PayPal order for sellers scored $< 2.5$.
- **PayPal Sandbox Checkout:** Seamless order creation and capture via PayPal Sandbox REST API v2, with a built-in high-fidelity local simulator fallback for offline testing.
- **Purchase & Trust Audit Dashboard:** Persistent SQLite-backed audit trails logging verified searches and completed PayPal orders.

---

## 3. System Architecture

TRUSTMATE operates on a decoupled architecture consisting of a Next.js user interface, a FastAPI agent orchestrator, and a FastMCP Model Context Protocol scoring server:

```
┌────────────────────────────────────────────────────────┐
│             Next.js 14 Frontend (Port 3000)            │
│         Search Bar • Badges • Inspect Modals           │
└───────────────────────────┬────────────────────────────┘
                            │ (Proxied /api/* requests)
                            ▼
┌────────────────────────────────────────────────────────┐
│         FastAPI Agent Gateway (Port 8000)              │
│       Intent Parsing • Risk Gating • SQLite Audit      │
└─────────────┬────────────────────────────┬─────────────┘
              │ (Streamable HTTP / SSE)    │ (REST API v2)
              ▼                            ▼
┌───────────────────────────┐  ┌─────────────────────────┐
│   Trust-MCP Server (8001) │  │  PayPal Sandbox Engine   │
│ ───────────────────────── │  │ ─────────────────────── │
│ • rank_offers tool        │  │ • Order Create & Capture│
│ • get_trust_score tool    │  │ • Webhook / Popup Flow  │
│ • explain_score tool      │  │ • High-Fidelity Mock    │
│ • SQLite Cache (72h TTL)  │  │ • Human Approval Loop   │
└───────────────────────────┘  └─────────────────────────┘
```

---

## 4. Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Next.js 14 (App Router), React 18, Tailwind CSS, Lucide React, FontAwesome |
| **Agent Backend** | Python 3.11, FastAPI, Uvicorn, Pydantic v2, HTTPX |
| **Trust Engine (MCP)** | FastMCP v2 (Official Model Context Protocol Python SDK), Streamable HTTP / SSE with Bearer Authentication |
| **Databases & Cache** | SQLite (`trustmate_agent.db` for audit logs, `trustmate.sqlite` for 72h assessment cache), SQLAlchemy / asyncpg |
| **Payment Integration** | PayPal REST API v2 (Sandbox mode) with fallback local simulator |
| **Verification Feeds** | Google Places / OpenStreetMap Nominatim, RDAP domain registry, URLhaus threat intelligence, Channel3 product provider |

---

## 5. Project Structure

```
Trustmate/
├── agent-app/                       # Customer Application & Agent Gateway
│   ├── frontend/                    # Next.js 14 Single-Page Application
│   │   ├── src/app/
│   │   │   ├── page.jsx             # Main UI: Search, verified badges, modals, dashboard
│   │   │   ├── layout.jsx           # Root layout and styling fonts
│   │   │   └── globals.css          # Tailwind CSS styling
│   │   ├── next.config.mjs          # API reverse proxy configuration (/api/* -> backend)
│   │   └── package.json             # Frontend dependencies
│   ├── services/
│   │   └── trustmate_mcp.py         # Streamable HTTP MCP client wrapper
│   ├── mock/
│   │   └── mock_mcp_server.py       # High-fidelity mock MCP server (port 8001)
│   ├── agent.py                     # Agent orchestrator & search intent parser
│   ├── main.py                      # FastAPI REST API server (port 8000)
│   ├── paypal_client.py             # PayPal Sandbox order create & capture client
│   ├── storage.py                   # SQLite database for audit history
│   ├── run_all.py                   # Single-command launcher for all 3 tiers
│   ├── requirements.txt             # Python backend dependencies
│   └── .env.example                 # Environment variable template
├── Trust-mcp/                       # FastMCP Trust & Authenticity Server
│   ├── app/
│   │   ├── api/routes/              # Health and readiness endpoints (/health)
│   │   ├── mcp/tools/               # MCP tools: rank_offers, get_trust_score, explain_score
│   │   ├── providers/               # Evidence providers (RDAP, OSM, URLhaus, Channel3)
│   │   ├── services/                # Evidence collection and scoring policies
│   │   └── main.py                  # Trust-MCP ASGI entrypoint
│   ├── requirements.txt             # MCP server dependencies
│   └── render.yaml                  # Cloud deployment configuration
├── test_paypal_and_user_journey.py  # End-to-end integration test suite
└── README.md                        # Project documentation
```

---

## 6. Installation & Setup

### Prerequisites
- **Python 3.10+** (Tested on Python 3.11)
- **Node.js 18+** (Tested on Node.js v20/v24 and npm)

### Step 1: Clone the Repository
```bash
git clone https://github.com/Vishal-5/Trustmate.git
cd Trustmate
```

### Step 2: Set Up Python Backend Dependencies
```bash
# Recommended: Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Agent App dependencies
cd agent-app
pip install -r requirements.txt
cd ..

# Install Trust-MCP dependencies
cd Trust-mcp
pip install -r requirements.txt
cd ..
```

### Step 3: Set Up Next.js Frontend
```bash
cd agent-app/frontend
npm install
cd ../..
```

---


## 7. Running the Project

### Option A: One-Command Master Launcher (Recommended)
You can start all three tiers (Trust-MCP server, FastAPI backend, and Next.js frontend) with one command from the project root:

```bash
python agent-app/run_all.py
```

The services will start automatically at:
- **Next.js Web UI:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Agent Gateway:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **TRUSTMATE MCP Server:** [http://127.0.0.1:8001](http://127.0.0.1:8001)

### Option B: Run Services Manually in Separate Terminals

1. **Terminal 1 — Trust-MCP Server:**
   ```bash
   cd Trust-mcp
   uvicorn app.main:app --host 127.0.0.1 --port 8001
   ```

2. **Terminal 2 — FastAPI Agent Backend:**
   ```bash
   cd agent-app
   uvicorn main:app --host 127.0.0.1 --port 8000
   ```

3. **Terminal 3 — Next.js Frontend:**
   ```bash
   cd agent-app/frontend
   npm run dev
   ```

---

## 8. Usage Walkthrough

1. **Open the Application:** Navigate to `http://localhost:3000` in your browser.
2. **Search for an Item:** Type a query or click one of the quick suggestions:
   - `💻 Laptop under ₹60,000 for programming`
   - `🎧 Headphones under ₹15,000`
   - `⌨️ Keyboard under ₹4,000`
3. **Observe Trust-First Gating:**
   - **Recommended Trusted Pick (e.g., TechWorld Prime - 4.7 Trusted):** Highlighted with a blue border and recommended badge based on verified signals and physical business presence.
   - **Gated Risky Offer (e.g., MegaElectronics Bargain - 1.9 Risky):** Flagged with an amber trade-off warning noting reasons such as an 18-day-old domain or unverified physical address.
4. **Inspect Verification Signals:** Click **"Inspect signals"** on any merchant card to view the signal factors (Domain Age, HTTPS, Google Places, Safe Browsing) and read the AI authenticity summary.
5. **Test Autonomous Fraud Interception:** Try clicking **"Approve & Pay with PayPal"** on the 1.9 Risky seller. An explicit risk confirmation modal intercepts the checkout flow, preventing accidental payment.
6. **Complete PayPal Checkout:** Click checkout on the recommended merchant. A PayPal Sandbox approval window opens. Once approved, the payment is captured.
7. **View the Audit Dashboard:** Click **"Audit Dashboard"** in the top navigation to inspect recorded searches and captured PayPal transactions stored in SQLite.

---

## 9. API Reference

### Customer Gateway Endpoints (`agent-app/main.py`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check endpoint returning `{"status": "ok"}` |
| `GET` | `/api/status` | Current MCP connection target and PayPal mode |
| `POST` | `/api/search` | Parses query and calls `rank_offers` on MCP server |
| `POST` | `/api/explain` | Fetches AI explanation summary for a seller |
| `POST` | `/api/order/create` | Initiates PayPal Sandbox order (enforces $< 2.5$ risk gating) |
| `POST` | `/api/order/capture` | Captures authorized PayPal order and logs to SQLite |
| `GET` | `/api/dashboard` | Returns recent searches and captured PayPal transactions |

### Trust-MCP Tools (`Trust-mcp/app/mcp/`)

| Tool Name | Input Parameters | Purpose |
|---|---|---|
| `rank_offers` | `query`, `budget`, `currency`, `target_country` | Gathers offers, calculates 1.0–5.0 trust scores, applies 70/30 ranking formula |
| `get_trust_score` | `seller`, `url` | Evaluates evidence and returns individual trust factors |
| `explain_score` | `seller`, `url` | Generates a concise human-readable summary of seller signals |

---

## 10. Testing

Run the automated integration test suite to verify the end-to-end user journey, PayPal order gating, and MCP tool communication:

```bash
python test_paypal_and_user_journey.py
```

This verifies:
- Query intent parsing and budget extraction
- MCP tool execution and response contract formatting
- Hard gating on sellers scoring under 2.5
- PayPal order creation and capture workflows
- SQLite search and order audit logging

---

## 11. Honest Limitations & Planned Improvements

- **Locale Bridging:** Channel3 currently specializes in US/USD product discovery; Indian INR searches bridge seamlessly to US catalog equivalents at a fixed demonstration exchange rate ($1\text{ USD} \approx ₹83.33$). A live currency feed is planned.
- **Pre-Trained Seller Intelligence:** Sellers without historical domain or business records receive an `"Unrated"` score rather than an arbitrary penalty, ensuring fair treatment of new legitimate merchants.
- **Planned: Chrome / Browser Extension:** Bringing the TRUSTMATE Truecaller verification overlay directly onto checkout pages of third-party e-commerce sites.

---

## 12. License

This project is developed for the **PayPal AI Hackathon** and is open source under the [MIT License](https://opensource.org/licenses/MIT).
