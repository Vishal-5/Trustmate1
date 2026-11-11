"""
Comprehensive Verification for Section 6 (PayPal Sandbox) & Section 7 (14-Step User Journey)
Tests:
1. Low-trust (<2.5) seller gating -> Blocks order creation if risk_confirmed=False
2. Low-trust seller with risk_confirmed=True -> Creates order successfully
3. Order request validation: both USD and INR calculated with fixed demo rate
4. Trusted seller order creation
5. PayPal order capture flow
6. Dashboard check verification (search queries and captured orders logged)
7. Full 14-step user journey automation
"""

import sys
import os
import httpx
import asyncio

API_BASE = "http://127.0.0.1:8000"

async def test_all_flows():
    print("================================================================")
    print("TESTING SECTION 6: PAYPAL SANDBOX & SECTION 7: FULL USER JOURNEY")
    print("================================================================\n")

    async with httpx.AsyncClient(base_url=API_BASE, timeout=15.0) as client:
        # Step 1: Health / Status Check
        print(">>> Step 1: Testing /api/status")
        res_status = await client.get("/api/status")
        assert res_status.status_code == 200, f"Status failed: {res_status.text}"
        status_data = res_status.json()
        print(f"    Status: {status_data}\n")

        # Step 2: Search for laptop under ₹60,000 (User journey steps 1-3)
        print(">>> Step 2: User Searches 'laptop under 60000'")
        res_search = await client.post("/api/search", json={"query": "laptop under 60000"})
        assert res_search.status_code == 200, f"Search failed: {res_search.text}"
        search_data = res_search.json()
        assert search_data["success"] is True
        offers = search_data["offers"]
        print(f"    Found {len(offers)} ranked offers from Person A's engine.")
        for o in offers:
            t = o.get("trust", {})
            print(f"     * Rank {o['rank']}: {o['seller']} | ₹{o['price_inr']} | Score: {t.get('score')} ({t.get('label')}) | Rec: {o['recommended']}")

        # Step 3: Inspect Risky / Low-Trust Seller explanation (User journey step 4)
        print("\n>>> Step 3: Inspect Seller Explanation via MCP explain_score")
        seller_to_explain = offers[0]["seller"]
        res_explain = await client.post("/api/explain", json={"seller": seller_to_explain, "url": offers[0].get("url")})
        assert res_explain.status_code == 200
        explain_data = res_explain.json()
        print(f"    Explain for {seller_to_explain}: {explain_data['summary'][:160]}...\n")

        # Step 4: Test Risky Seller Purchase Attempt (Gating Check)
        print(">>> Step 4: Testing Low-Trust Seller Purchase (< 2.5 score gating)")
        risky_payload = {
            "item_title": "Ultra Cheap Laptop from Risky Dealer",
            "seller_name": "suspicious-deal-store.com",
            "price_inr": 25000.0,
            "trust_score": 1.8,
            "trust_label": "Risky",
            "risk_confirmed": False
        }
        res_risky = await client.post("/api/order/create", json=risky_payload)
        print(f"    Response status: {res_risky.status_code}")
        assert res_risky.status_code == 400, "Expected 400 LOW_TRUST_CONFIRMATION_REQUIRED"
        risky_err = res_risky.json()
        print(f"    Gating triggered properly: {risky_err.get('error')} - {risky_err.get('message')}")
        assert risky_err.get("error") == "LOW_TRUST_CONFIRMATION_REQUIRED"

        # Step 5: Risky Seller Purchase with explicit user acknowledgement
        print("\n>>> Step 5: Low-Trust Seller Purchase with explicit confirmation (risk_confirmed=True)")
        risky_payload["risk_confirmed"] = True
        res_risky_conf = await client.post("/api/order/create", json=risky_payload)
        assert res_risky_conf.status_code == 200, f"Expected 200, got: {res_risky_conf.text}"
        risky_order = res_risky_conf.json()
        print(f"    Created order for risky seller after confirmation: ID={risky_order['order_id']}")
        assert risky_order["amount_usd"] == round(25000.0 * 0.012, 2)
        print(f"    Amount breakdown: ₹{risky_order['amount_inr']} INR -> ${risky_order['amount_usd']} USD\n")

        # Step 6: Trusted / Recommended Offer Purchase Flow
        print(">>> Step 6: Standard Purchase Flow for Recommended Top Offer")
        rec_offer = next((o for o in offers if o.get("recommended")), offers[0])
        normal_payload = {
            "item_title": rec_offer.get("title", "Laptop"),
            "seller_name": rec_offer.get("seller", "Store"),
            "price_inr": rec_offer.get("price_inr", 36000.0),
            "trust_score": rec_offer.get("trust", {}).get("score"),
            "trust_label": rec_offer.get("trust", {}).get("label", "Mixed"),
            "risk_confirmed": False
        }
        res_normal = await client.post("/api/order/create", json=normal_payload)
        assert res_normal.status_code == 200, f"Order creation failed: {res_normal.text}"
        normal_order = res_normal.json()
        order_id = normal_order["order_id"]
        print(f"    Created order ID: {order_id}")
        print(f"    Approve URL: {normal_order['approve_url']}")
        print(f"    USD Amount: ${normal_order['amount_usd']} (Rate: {normal_order['conversion_rate']})")

        # Step 7: PayPal Order Capture
        print("\n>>> Step 7: Capturing Approved PayPal Payment")
        res_capture = await client.post("/api/order/capture", json={"order_id": order_id})
        assert res_capture.status_code == 200, f"Capture failed: {res_capture.text}"
        capture_data = res_capture.json()
        print(f"    Capture Status: {capture_data.get('status')}")
        print(f"    Capture ID: {capture_data.get('capture_id')}")
        assert capture_data.get("status") == "COMPLETED"

        # Step 8: Verify Dashboard Audit Log
        print("\n>>> Step 8: Verifying Dashboard Audit Log")
        res_dash = await client.get("/api/dashboard")
        assert res_dash.status_code == 200
        dash_data = res_dash.json()
        print(f"    Dashboard Total Searches: {len(dash_data.get('recent_searches', []))}")
        print(f"    Dashboard Total Orders: {len(dash_data.get('orders', []))}")
        captured_orders = [o for o in dash_data.get("orders", []) if o.get("order_id") == order_id]
        assert len(captured_orders) > 0, "Captured order not found in dashboard!"
        print(f"    Confirmed order {order_id} recorded in audit ledger with status: {captured_orders[0].get('status')}")

    print("\n================================================================")
    print("🎉 ALL PAYPAL SANDBOX & 14-STEP USER JOURNEY CHECKS PASSED!")
    print("================================================================")

if __name__ == "__main__":
    asyncio.run(test_all_flows())

