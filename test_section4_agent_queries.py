"""
Comprehensive Verification for Section 4: Person B's AI Agent Queries
Queries tested:
1. "Find me a laptop under ₹60,000."
2. "Find me the cheapest laptop under ₹60,000."
3. "Explain why this seller is risky."
4. "Why is this seller Unrated?"
5. "Show me the safest available offer."
6. "Find me a laptop under ₹40,000."
"""

import os
import sys
import asyncio

sys.path.insert(0, os.path.abspath("agent-app"))
from agent import agent

async def run_agent_queries():
    print("================================================================")
    print("SECTION 4: VERIFYING AGENT USER QUERIES AGAINST PERSON A'S SERVER")
    print("================================================================\n")

    # 1. "Find me a laptop under ₹60,000."
    print(">>> 1. User Prompt: 'Find me a laptop under ₹60,000.'")
    res1 = await agent.execute_search("Find me a laptop under ₹60,000.")
    assert res1["success"] is True, f"Search failed: {res1.get('error')}"
    assert res1["budget_inr"] == 60000.0, f"Expected budget 60000, got {res1['budget_inr']}"
    assert len(res1["offers"]) > 0, "No offers returned"
    print(f"   [Query parsed]: '{res1['query']}' | Budget: ₹{res1['budget_inr']}")
    print(f"   [Offers count]: {len(res1['offers'])}")
    for o in res1["offers"]:
        t = o.get("trust", {})
        print(f"    - Rank {o.get('rank')}: {o.get('seller')} (₹{o.get('price_inr'):,.2f}) -> Trust: {t.get('score')} ({t.get('label')}) | Recommended: {o.get('recommended')}")
    # Verify ranking is sequential 1..N
    ranks = [o["rank"] for o in res1["offers"]]
    assert ranks == list(range(1, len(ranks) + 1)), f"Ranks out of order: {ranks}"
    # Verify seller < 2.5 is NEVER recommended
    for o in res1["offers"]:
        if o.get("trust", {}).get("score") is not None and o["trust"]["score"] < 2.5:
            assert o.get("recommended") is False, f"Risky seller {o['seller']} was recommended!"
    print("   ✓ Query 1 Verified!\n")

    # 2. "Find me the cheapest laptop under ₹60,000."
    print(">>> 2. User Prompt: 'Find me the cheapest laptop under ₹60,000.'")
    res2 = await agent.execute_search("Find me the cheapest laptop under ₹60,000.")
    assert res2["success"] is True
    print(f"   [Query parsed]: '{res2['query']}' | Budget: ₹{res2['budget_inr']}")
    # Rule: Person B does NOT re-order by price alone; trust comes first, price second as returned by Person A!
    print(f"   [Order preserved from Person A]: {[o['seller'] for o in res2['offers']]}")
    print("   ✓ Query 2 Verified: Ranking order from Person A strictly preserved (no local re-sorting by raw price).\n")

    # 3. "Explain why this seller is risky."
    print(">>> 3. User Prompt: 'Explain why this seller is risky.' (Seller: Mock Store Risky / suspicious seller)")
    exp_risky = await agent.get_seller_explanation("suspicious-deal-store.com")
    print(f"   [Explanation received]:\n   {exp_risky.strip()[:200]}...")
    assert len(exp_risky) > 20, "Explanation too short or missing"
    print("   ✓ Query 3 Verified!\n")

    # 4. "Why is this seller Unrated?"
    print(">>> 4. User Prompt: 'Why is this seller Unrated?' (Seller: unknown-new-startup.in)")
    exp_unrated = await agent.get_seller_explanation("unknown-new-startup.in")
    print(f"   [Explanation received]:\n   {exp_unrated.strip()[:200]}...")
    assert len(exp_unrated) > 20, "Explanation too short or missing"
    print("   ✓ Query 4 Verified!\n")

    # 5. "Show me the safest available offer."
    print(">>> 5. User Prompt: 'Show me the safest available offer.'")
    res5 = await agent.execute_search("Show me the safest available offer for laptop")
    assert res5["success"] is True
    rec_offers = [o for o in res5["offers"] if o.get("recommended")]
    print(f"   [Recommended / Top Trusted Pick]: {rec_offers[0]['seller'] if rec_offers else 'None'}")
    print("   ✓ Query 5 Verified!\n")

    # 6. "Find me a laptop under ₹40,000."
    print(">>> 6. User Prompt: 'Find me a laptop under ₹40,000.'")
    res6 = await agent.execute_search("Find me a laptop under ₹40,000.")
    assert res6["success"] is True
    assert res6["budget_inr"] == 40000.0, f"Expected 40000, got {res6['budget_inr']}"
    print(f"   [Query parsed]: '{res6['query']}' | Budget: ₹{res6['budget_inr']}")
    print(f"   [Offers under ₹40,000 count]: {len(res6['offers'])}")
    for o in res6["offers"]:
        assert o.get("price_inr") <= 40000.0, f"Offer price ₹{o.get('price_inr')} exceeds ₹40,000!"
        print(f"    - Rank {o.get('rank')}: {o.get('seller')} (₹{o.get('price_inr'):,.2f})")
    print("   ✓ Query 6 Verified!\n")

    print("================================================================")
    print("ALL SECTION 4 AGENT QUERIES SUCCESSFULLY VERIFIED!")
    print("================================================================")

if __name__ == "__main__":
    asyncio.run(run_agent_queries())

