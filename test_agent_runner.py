import asyncio
import os
import sys

# Ensure agent-app is on sys.path
sys.path.insert(0, os.path.abspath("agent-app"))

from agent import agent

async def main():
    print("--- 1. Testing Agent Search ---")
    res = await agent.execute_search("laptop under 60000 for programming")
    print(f"Success: {res.get('success')}")
    print(f"Query: {res.get('query')}")
    print(f"Budget: {res.get('budget_inr')}")
    print(f"Unverified notes: {res.get('unverified_notes')}")
    offers = res.get("offers", [])
    print(f"Total offers returned: {len(offers)}")
    for o in offers:
        score = o.get("trust", {}).get("score")
        label = o.get("trust", {}).get("label")
        rec = o.get("recommended")
        rank = o.get("rank")
        print(f"Rank {rank}: {o.get('seller')} - Rs {o.get('price_inr')} - Score: {score} ({label}) - Rec: {rec}")

    print("\n--- 2. Testing Explain Score ---")
    if offers:
        for o in offers[:2]:
            seller = o.get("seller")
            url = o.get("url")
            exp = await agent.get_seller_explanation(seller, url)
            print(f"Explain [{seller}]: {exp[:150]}...")

if __name__ == "__main__":
    asyncio.run(main())

