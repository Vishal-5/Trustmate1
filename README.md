# 🛡️ TRUSTMATE: Truecaller for Online Sellers

> **PayPal AI Hackathon** — *Build What's Next with PayPal and AI*  
> **Repository:** [https://github.com/Vishal-5/Trustmate.git](https://github.com/Vishal-5/Trustmate.git)

---

## 💡 What is TRUSTMATE?

**TRUSTMATE** is an AI agent that performs Truecaller-style authenticity and trust checks on online merchants before you pay. 

Instead of traditional shopping algorithms where the cheapest price always wins, TRUSTMATE enforces a **Trust-First, Price-Second** golden rule:
> 🚫 **Any seller scoring below 2.5 is gated and NEVER recommended, however cheap they are.** Price is only compared among verified, trusted sellers.

When a customer searches for a product, TRUSTMATE evaluates merchant authenticity signals (Places verification, domain age, HTTPS certificates, contact & return policy validity, and Safe Browsing reputation), displays an intuitive **1.0 to 5.0 Trust Score**, provides instant **Tap-to-Explain** AI transparency, and routes payment securely through **PayPal Sandbox** with explicit human-in-the-loop approval.

---

## 🏛️ System Architecture

TRUSTMATE follows a **Dual-MCP Server + Agent Orchestrator** architecture:

```
                          ┌─────────────────────────────┐
                          │    Next.js 14 Frontend      │
                          │    http://localhost:3000    │
                          └──────────────┬──────────────┘
                                         │  (Proxied /api/*)
                                         ▼
                      ┌──────────────────────────────────────┐
                      │    FastAPI Agent Backend (/agent-app)│
                      │    http://127.0.0.1:8000             │
                      │ ──────────────────────────────────── │
                      │ • Intent extraction (query + budget) │
                      │ • Strict rank preservation           │
                      │ • Low-score (<2.5) secondary confirm │
                      │ • Fixed INR -> USD demo conversion   │
                      │ • SQLite Audit Log (Searches/Orders) │
                      └───────────┬──────────────┬───────────┘
                                  │              │
                                  ▼              ▼
         ┌────────────────────────────────┐  ┌─────────────────────────────────┐
         │     TRUSTMATE MCP Server       │  │      PayPal Sandbox Engine      │
         │   (Price Search & Trust)       │  │        (Payment Capture)        │
         │ ────────────────────────────── │  │ ─────────────────────────────── │
         │ • rank_offers (Trust-First)    │  │ • PayPal MCP JSON-RPC           │
         │ • get_trust_score              │  │ • PayPal Sandbox REST API       │
         │ • explain_score (AI Summary)   │  │ • High-Fidelity Local Simulator │
         │ • SQLite Cache (3-Day TTL)     │  │ • Order Create & Capture Flow   │
         │ (HTTP endpoint: TRUST_MCP_URL) │  └─────────────────────────────────┘
         └────────────────────────────────┘
```

---

## 📁 Repository Structure

```
Trustmate/
├── .gitignore                   # Ignores .env, node_modules, .next, cache, *.db
├── README.md                    # Project overview & quickstart guide
└── agent-app/                   # Customer App, Agent & Payments (Person B)
    ├── frontend/                # Next.js 14 Single-Page Application
    │   ├── src/app/
    │   │   ├── page.jsx         # UI with Search, Badges, Modals & Checkout
    │   │   ├── layout.jsx       # FontAwesome & Plus Jakarta Sans
    │   │   └── globals.css      # Tailwind styling & glassmorphism
    │   ├── next.config.mjs      # API reverse proxy configuration
    │   ├── package.json         # Frontend dependencies
    │   ├── postcss.config.js    # PostCSS configuration
    │   └── tailwind.config.js   # Tailwind CSS configuration
    │
    ├── main.py                  # FastAPI REST API Gateway (Port 8000)
    ├── agent.py                 # Agent loop (orchestrates TRUSTMATE MCP calls)
    ├── paypal_client.py         # PayPal Sandbox order create & capture
    ├── storage.py               # SQLite search audit & captured orders store
    ├── run_all.py               # One-click launcher for all 3 services
    ├── requirements.txt         # Python dependencies
    ├── .env.example             # Example environment variables
    ├── mock/
    │   └── mock_mcp_server.py   # Mock TRUSTMATE MCP server (Port 8001)
    └── tests/
        └── test_person_b_flow.py# Automated test suite
```

---

## 🚀 Quickstart: How to Run the Project

### Prerequisites
- **Python 3.10+** (Tested with Python 3.11)
- **Node.js 18+** (Tested with Node.js v20/v24 and npm)

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/Vishal-5/Trustmate.git
cd Trustmate
```

---

### Step 2: Install Python Backend Dependencies
```bash
cd agent-app
pip install -r requirements.txt
```

---

### Step 3: Install Next.js Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

---

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Default settings in `agent-app/.env`:
```ini
# Person A TRUSTMATE MCP server URL (defaults to local mock on port 8001)
TRUST_MCP_URL=http://127.0.0.1:8001

# PayPal Sandbox settings (uses built-in simulator if credentials left blank)
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
PAYPAL_MODE=simulator

PORT=8000
HOST=127.0.0.1
```

---

### Step 5: Start All Services (One Command)
Run the master launcher from the project root:
```bash
python agent-app/run_all.py
```

The script automatically starts all 3 services:
1. **Next.js Frontend:** [http://localhost:3000](http://localhost:3000)
2. **FastAPI Backend:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
3. **Mock MCP Server:** [http://127.0.0.1:8001](http://127.0.0.1:8001)

---

## 🎬 3-Minute Interactive Demo Walkthrough

1. **Open the App:** Navigate to **[http://localhost:3000](http://localhost:3000)** in your browser.
2. **Search for a Deal:** Click the chip:
   > `💻 Laptop under ₹60,000 for programming`
3. **Observe the Trust-First Gate:**
   - **MegaElectronics Bargain (₹42,000):** Far cheaper, but flagged **1.9 (Risky)** with an explicit trade-off banner:
     > *"₹12,600 cheaper but scored 1.9: newly registered domain (18 days old), no physical location verified, and multiple non-delivery complaints."*
   - **TechWorld Prime (₹54,600):** Ranked #1 as the **Recommended Pick** with a **4.7 (Trusted)** rating and verified Google Places track record.
4. **Tap-to-Explain Transparency:**
   - Click **"Inspect signals"** on any merchant card to view verified signal factors (Google Places, Reviews, Domain Age/HTTPS, Contact/Policy, Safe Browsing) and read the compact AI authenticity summary.
5. **Human-in-the-Loop Gating:**
   - Try clicking **"Approve & Pay with PayPal"** on the 1.9 Risky seller. An explicit warning modal blocks autonomous payment and requires user confirmation.
6. **PayPal Sandbox Payment:**
   - Click **"Approve & Pay with PayPal"** on the recommended pick (*TechWorld Prime*).
   - Price is converted to USD at the fixed demo rate (`$655.20 USD`).
   - The PayPal Sandbox approval window opens and captures the payment.
7. **Audit Dashboard:**
   - Click **"Audit Dashboard"** in the top navigation to view the logged search history and completed PayPal transactions.

---

## 🔒 Honest Limits & Pitch Transparency

- **Decision Support, Not Guarantee:** TRUSTMATE aggregates verifiable public authenticity signals to help customers decide. It does not claim 100% fraud immunity.
- **Respects Web Boundaries:** Never bypasses CAPTCHAs, bot gates, or scrapers. Signals that cannot be verified are transparently labeled `"unverified"` in the breakdown.
- **Fair to New Businesses:** Unknown sellers with insufficient data receive `"Unrated"`, not an arbitrary low score.

---

## 🛠️ Running Tests

To verify that the agent loop, contract shapes, and PayPal integration pass:
```bash
python agent-app/run_tests.py
```

All 6 test suites verify:
- Query intent and budget extraction
- Fixed demo INR to USD currency conversion
- Contract shape compliance
- Trust score calculation and explanations
- Low-score gating enforcement
- SQLite storage and dashboard persistence

---

## 📤 Pushing to GitHub

```bash
git add .
git commit -m "feat: complete TRUSTMATE agent with Next.js frontend, FastAPI API, and PayPal integration"
git branch -M main
git remote add origin https://github.com/Vishal-5/Trustmate.git
git push -u origin main
```

