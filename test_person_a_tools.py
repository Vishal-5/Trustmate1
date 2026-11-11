"""
Direct Verification Test for Person A's TRUSTMATE MCP Server Tools
Tests:
- Test A: rank_offers
- Test B: get_trust_score
- Test C: explain_score
"""

import asyncio
import sys
import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from mcp.types import TextContent

MCP_URL = "http://127.0.0.1:8001/mcp"
BEARER_TOKEN = "trustmate_test_secret_bearer_token_32chars"

async def test_mcp_tools():
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
    }
    timeout = httpx2.Timeout(30.0, read=60.0)

    print("Connecting to Person A's MCP server at", MCP_URL)
    async with httpx2.AsyncClient(headers=headers, timeout=timeout) as http_client:
        transport = streamable_http_client(MCP_URL, http_client=http_client)
        async with Client(transport) as client:
            print("Connected! Listing available tools:")
            tools = await client.list_tools()
            for t in tools.tools:
                print(f" - Tool: {t.name}: {t.description[:60]}...")

            # ----------------------------------------------------
            # TEST A: rank_offers
            # ----------------------------------------------------
            print("\n>>> TEST A: Testing rank_offers (laptop, budget 60,000 INR)...")
            res_rank = await client.call_tool(
                "rank_offers",
                {
                    "query": "laptop",
                    "budget": 60000.0,
                    "currency": "INR",
                    "target_country": "IN"
                }
            )
            assert not res_rank.is_error, f"Tool error: {res_rank.content}"
            data_rank = res_rank.structured_content
            print("rank_offers output keys:", list(data_rank.keys()))
            offers_obj = data_rank.get("offers", {})
            items = offers_obj.get("items", [])
            print(f"Offers found: {len(items)}, recommended count: {offers_obj.get('recommended')}")

            assert len(items) > 0, "No offers returned by rank_offers"
            first_offer = items[0]
            print(f"Top Offer: [{first_offer.get('seller')}] {first_offer.get('title')} - Price: {first_offer.get('price')} {first_offer.get('currency')}")
            print(f"Trust: {first_offer.get('trust')}")
            print(f"Recommended: {first_offer.get('recommended')}, Rank: {first_offer.get('rank')}")

            # Verify low score gating (< 2.5 never recommended)
            for item in items:
                trust = item.get("trust", {})
                score = trust.get("score")
                if score is not None and score < 2.5:
                    assert item.get("recommended") is False, f"Seller {item.get('seller')} scored {score} but was recommended!"

            print("TEST A PASSED!")

            # ----------------------------------------------------
            # TEST B: get_trust_score
            # ----------------------------------------------------
            test_seller = first_offer.get("seller", "bestbuy.com")
            test_url = first_offer.get("url")
            print(f"\n>>> TEST B: Testing get_trust_score for seller '{test_seller}'...")
            res_score = await client.call_tool(
                "get_trust_score",
                {
                    "seller": test_seller,
                    "url": test_url,
                    "target_country": "IN"
                }
            )
            assert not res_score.is_error, f"Tool error: {res_score.content}"
            data_score = res_score.structured_content
            print("get_trust_score result:", data_score)
            assert "score" in data_score or "label" in data_score
            assert "factors" in data_score
            print("TEST B PASSED!")

            # ----------------------------------------------------
            # TEST C: explain_score
            # ----------------------------------------------------
            print(f"\n>>> TEST C: Testing explain_score for seller '{test_seller}'...")
            res_explain = await client.call_tool(
                "explain_score",
                {
                    "seller": test_seller,
                    "url": test_url,
                    "target_country": "IN"
                }
            )
            assert not res_explain.is_error, f"Tool error: {res_explain.content}"
            data_explain = res_explain.structured_content
            print("explain_score summary:", data_explain.get("summary"))
            assert "summary" in data_explain and len(data_explain["summary"]) > 0
            print("TEST C PASSED!")

            print("\n=======================================================")
            print("🎉 ALL TESTS A, B, AND C PASSED ON PERSON A'S SERVER!")
            print("=======================================================")

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())

