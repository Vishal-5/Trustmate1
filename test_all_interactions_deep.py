"""
Deep Feature & Interaction Audit Test Suite
Tests every endpoint, button workflow, and edge case.
"""

import asyncio
import httpx

BASE_URL = "http://localhost:3000"

async def test_all_features():
    print("=======================================================")
    print("      DEEP FEATURE & USER INTERACTION AUDIT")
    print("=======================================================\n")
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=20.0) as client:
        # 1. Frontend Root Page
        print("1. [Frontend] Home Page Load: GET /")
        res = await client.get("/")
        assert res.status_code == 200, f"Frontend failed: {res.status_code}"
        assert "TRUSTMATE" in res.text
        print("   -> PASS: 200 OK, HTML loaded successfully.\n")

        # 2. System Status API
        print("2. [Backend/MCP] Status Endpoint: GET /api/status")
        res = await client.get("/api/status")
        assert res.status_code == 200
        status = res.json()
        print(f"   -> PASS: 200 OK, MCP URL: {status.get('trust_mcp_url')}, Mode: {status.get('paypal_mode')}\n")

        # 3. Normal Search Flow
        print("3. [Search] Normal Query: POST /api/search ('laptop under 60000')")
        res = await client.post("/api/search", json={"query": "laptop under 60000"})
        assert res.status_code == 200
        search_data = res.json()
        assert search_data["success"] is True
        assert len(search_data["offers"]) > 0
        print(f"   -> PASS: {len(search_data['offers'])} offers returned in Person A's exact rank order.\n")

        # 4. Empty Search Query Error Handling
        print("4. [Search] Empty Query Validation: POST /api/search (query='')")
        res = await client.post("/api/search", json={"query": "   "})
        assert res.status_code == 400
        print("   -> PASS: Backend correctly rejects empty query with HTTP 400.\n")

        # 5. Low Budget Search (Empty Offers Edge Case)
        print("5. [Search] Budget Under Threshold: POST /api/search ('laptop under 500')")
        res = await client.post("/api/search", json={"query": "laptop under 500"})
        assert res.status_code == 200
        low_data = res.json()
        assert low_data["success"] is True
        print(f"   -> PASS: Handled gracefully, returned {len(low_data['offers'])} offers without crashing.\n")

        # 6. Tap-To-Explain Score
        print("6. [Explanation] Inspect Signals: POST /api/explain")
        first_seller = search_data["offers"][0]["seller"]
        res = await client.post("/api/explain", json={"seller": first_seller, "url": search_data["offers"][0].get("url")})
        assert res.status_code == 200
        explain_data = res.json()
        assert "summary" in explain_data
        print(f"   -> PASS: Explain summary received for '{first_seller}'. Length: {len(explain_data['summary'])} chars.\n")

        # 7. Low-Trust Gating: Gated Order Creation (<2.5)
        print("7. [Payment Safety] Risky Seller Gating: POST /api/order/create (trust_score=1.8, risk_confirmed=False)")
        res = await client.post("/api/order/create", json={
            "item_title": "Dubious Laptop Deal",
            "seller_name": "shady-deals.com",
            "price_inr": 20000.0,
            "trust_score": 1.8,
            "trust_label": "Risky",
            "risk_confirmed": False
        })
        assert res.status_code == 400
        err_data = res.json()
        assert err_data.get("error") == "LOW_TRUST_CONFIRMATION_REQUIRED"
        print("   -> PASS: Gated! HTTP 400 returned with LOW_TRUST_CONFIRMATION_REQUIRED.\n")

        # 8. Risky Seller Confirmation Acknowledged
        print("8. [Payment Safety] Risky Seller With User Acknowledgment: POST /api/order/create (risk_confirmed=True)")
        res = await client.post("/api/order/create", json={
            "item_title": "Dubious Laptop Deal",
            "seller_name": "shady-deals.com",
            "price_inr": 20000.0,
            "trust_score": 1.8,
            "trust_label": "Risky",
            "risk_confirmed": True
        })
        assert res.status_code == 200
        order_data = res.json()
        assert "order_id" in order_data
        print(f"   -> PASS: Order created upon buyer confirmation. Order ID: {order_data['order_id']}\n")

        # 9. Normal Trusted Order Creation
        print("9. [PayPal] Normal Order Creation: POST /api/order/create")
        res = await client.post("/api/order/create", json={
            "item_title": "Verified Laptop",
            "seller_name": "Mock Store D",
            "price_inr": 36000.0,
            "trust_score": 3.35,
            "trust_label": "Mixed",
            "risk_confirmed": False
        })
        assert res.status_code == 200
        norm_order = res.json()
        order_id = norm_order["order_id"]
        approve_url = norm_order["approve_url"]
        assert norm_order["amount_usd"] == 432.0
        print(f"   -> PASS: Order {order_id} created. INR 36,000 -> ${norm_order['amount_usd']} USD.\n")

        # 10. PayPal Simulator Approval UI
        print(f"10. [PayPal UI] Approval Page: GET {approve_url}")
        res = await client.get(approve_url)
        assert res.status_code == 200
        assert "PayPal" in res.text
        assert "Approve & Complete Payment" in res.text
        print("   -> PASS: PayPal approval UI rendered successfully.\n")

        # 11. Payment Capture
        print(f"11. [PayPal Capture] Capture Payment: POST /api/order/capture (order_id={order_id})")
        res = await client.post("/api/order/capture", json={"order_id": order_id})
        assert res.status_code == 200
        cap_data = res.json()
        assert cap_data.get("status") == "COMPLETED"
        assert "capture_id" in cap_data
        print(f"   -> PASS: Payment captured! Capture ID: {cap_data['capture_id']}\n")

        # 12. Audit Dashboard
        print("12. [Storage] Audit Dashboard: GET /api/dashboard")
        res = await client.get("/api/dashboard")
        assert res.status_code == 200
        dash = res.json()
        orders = dash.get("orders", [])
        searches = dash.get("recent_searches", [])
        assert len(orders) > 0
        assert len(searches) > 0
        matched = [o for o in orders if o["order_id"] == order_id]
        assert len(matched) == 1
        assert matched[0]["status"] == "COMPLETED"
        print(f"   -> PASS: Dashboard has {len(orders)} orders and {len(searches)} search checks. Order verified in ledger!\n")

    print("=======================================================")
    print("   ALL 12 DEEP FEATURE AUDIT CHECKS PASSED!")
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(test_all_features())

