"""
TRUSTMATE - Agent Orchestrator (Person B)
Implements the core agent loop according to Person B specification:
1. Extract query & budget from user request.
2. Call TRUST_MCP_URL rank_offers.
   STRICT RULE: Person B NEVER re-ranks, re-scores, or hides offers.
3. Show offers in the order given by Person A's server.
4. When tapped, fetch explain_score.
5. Create PayPal order only after explicit customer approval.
6. Enforce second confirmation if trust.score < 2.5.
7. Treat "Unrated" (score: null) as Unrated, never bad.
"""

import os
import re
import json
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)
load_dotenv()

import httpx
from typing import Dict, Any, Optional, Tuple, List
from storage import log_search
from services.trustmate_mcp import trustmate_mcp_service, TrustmateMCPError

DEFAULT_MOCK_MCP_URL = "http://127.0.0.1:8001"

def parse_user_request(user_input: str) -> Tuple[str, float, str, str]:
    """
    Extracts search query, budget, currency ('USD' or 'INR'), and target_country ('US' or 'IN').
    Examples:
    - 'laptop under 60000 for programming' -> ('laptop for programming', 60000.0, 'INR', 'IN')
    - 'laptop under $1000' -> ('laptop', 1000.0, 'USD', 'US')
    - 'headphones under Rs 15,000' -> ('headphones', 15000.0, 'INR', 'IN')
    - 'ipad under $800' -> ('ipad', 800.0, 'USD', 'US')
    """
    text = user_input.strip()
    is_usd = bool(re.search(r'(?:\$|\busd\b|\bdollars?\b)', text, re.IGNORECASE))
    currency = "USD" if is_usd else "INR"
    target_country = "US" if is_usd else "IN"
    budget = 1000.0 if is_usd else 60000.0

    # Match patterns with 'k': under 60k, $1k
    k_match = re.search(r'(?:under|below|max|within)?\s*(?:\$|rs\.?|inr|₹|usd)?\s*(\d+(?:\.\d+)?)\s*k\b', text, re.IGNORECASE)
    if k_match:
        budget = float(k_match.group(1)) * 1000
        clean_query = re.sub(r'\b(?:under|below|max|within)?\s*(?:\$|rs\.?|inr|₹|usd)?\s*\d+(?:\.\d+)?\s*k\b', '', text, flags=re.IGNORECASE)
    else:
        # Match patterns with numbers: under $1000, under 60000, under rs 60,000
        num_match = re.search(r'(?:under|below|budget|within|max)\s*(?:of\s*)?(?:\$|rs\.?|inr|₹|usd)?\s*([\d,]+(?:\.\d+)?)', text, re.IGNORECASE)
        if num_match:
            raw_num = num_match.group(1).replace(',', '')
            try:
                budget = float(raw_num)
            except ValueError:
                budget = 1000.0 if is_usd else 60000.0
            clean_query = re.sub(r'(?:under|below|budget|within|max)\s*(?:of\s*)?(?:\$|rs\.?|inr|₹|usd)?\s*[\d,]+(?:\.\d+)?', '', text, flags=re.IGNORECASE)
        else:
            clean_query = text

    clean_query = re.sub(r'[\$₹]', '', clean_query)
    clean_query = re.sub(r'\b(?:usd|inr|rs\.?)\b', '', clean_query, flags=re.IGNORECASE)
    clean_query = re.sub(r'\s+', ' ', clean_query).strip()
    if not clean_query:
        clean_query = "Product"

    return clean_query, budget, currency, target_country

class TrustmateAgent:
    def __init__(self):
        pass

    @property
    def mcp_url(self):
        return os.getenv("TRUST_MCP_URL", DEFAULT_MOCK_MCP_URL).rstrip("/")

    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Calls a tool on the TRUSTMATE MCP server via:
        1. Official MCP Client Protocol (Streamable HTTP / SSE) with Bearer token
        2. Direct JSON-RPC or REST fallback
        3. Local in-process fallback only if service is completely unreachable
        """
        # Primary: Official Streamable HTTP MCP Client
        try:
            res = await trustmate_mcp_service.call_tool(tool_name, arguments)
            if res:
                return res
        except Exception as primary_err:
            print(f"[Agent] Official MCP client error for {tool_name}: {primary_err}. Attempting fallbacks...")

        # Fallback 1: Standard MCP JSON-RPC
        url = self.mcp_url
        timeout = 10.0
        payload_rpc = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                headers = {}
                token = os.getenv("TRUSTMATE_MCP_BEARER_TOKEN", os.getenv("MCP_BEARER_TOKEN"))
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                res = await client.post(f"{url}/mcp", json=payload_rpc, headers=headers)
                if res.status_code == 200:
                    json_data = res.json()
                    if "result" in json_data:
                        result = json_data["result"]
                        if "data" in result:
                            return result["data"]
                        if "content" in result and len(result["content"]) > 0:
                            content_text = result["content"][0].get("text", "")
                            try:
                                return json.loads(content_text.replace("'", "\""))
                            except Exception:
                                return {"summary": content_text}
            except Exception:
                pass

            # Fallback 2: Direct REST route /tools/{tool_name}
            try:
                res = await client.post(f"{url}/tools/{tool_name}", json=arguments)
                if res.status_code == 200:
                    return res.json()
            except Exception as e:
                # Fallback 3: In-process mock
                if "127.0.0.1" in url or "localhost" in url:
                    print(f"[Agent] Local MCP server offline at {url}, using in-process mock fallback...")
                    try:
                        from mock.mock_mcp_server import (
                            execute_rank_offers,
                            execute_get_trust_score,
                            execute_explain_score
                        )
                        if tool_name == "rank_offers":
                            return execute_rank_offers(arguments.get("query", ""), float(arguments.get("budget", arguments.get("budget_inr", 60000))))
                        elif tool_name == "get_trust_score":
                            return execute_get_trust_score(arguments.get("seller", ""), arguments.get("url"))
                        elif tool_name == "explain_score":
                            return execute_explain_score(arguments.get("seller", ""), arguments.get("url"))
                    except Exception as inner_e:
                        print(f"[Agent] In-process fallback error: {inner_e}")
                print(f"[Agent MCP Error] Calling {tool_name} on {url} failed: {e}")
                raise e

    async def execute_search(self, user_prompt: str) -> Dict[str, Any]:
        """
        Agent Step 1-3:
        Parses user intent, executes rank_offers, logs search, and returns ranked results.
        CRITICAL RULE: Results are returned exactly in Person A's ranked order without any local re-ordering!
        """
        query, budget, currency, target_country = parse_user_request(user_prompt)
        budget_inr = budget if currency == "INR" else round(budget * (1 / 0.012), 2)

        try:
            result = await self._call_mcp_tool("rank_offers", {
                "query": query,
                "budget": budget,
                "budget_inr": budget_inr,
                "currency": currency,
                "target_country": target_country
            })
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to communicate with TRUSTMATE MCP server at {self.mcp_url}: {str(e)}",
                "query": query,
                "budget_inr": budget_inr,
                "offers": [],
                "unverified_notes": []
            }

        # Handle nested offers from Person A: result["offers"]["items"] or result["offers"]
        raw_offers = result.get("offers", [])
        if isinstance(raw_offers, dict):
            items = raw_offers.get("items", [])
            unverified_notes = raw_offers.get("unverified_notes", []) or result.get("unverified_notes", [])
        elif isinstance(raw_offers, list):
            items = raw_offers
            unverified_notes = result.get("unverified_notes", [])
        else:
            items = []
            unverified_notes = []

        # If live provider does not support INR market, automatically retry with USD/US market to get real stores
        if not items and any("not supported by the product provider" in str(n) for n in unverified_notes):
            try:
                budget_usd = round(budget * 0.012, 2)
                res_usd = await self._call_mcp_tool("rank_offers", {
                    "query": query,
                    "budget": max(budget_usd, 50.0),
                    "currency": "USD",
                    "target_country": "US"
                })
                raw_usd = res_usd.get("offers", {})
                if isinstance(raw_usd, dict) and raw_usd.get("items"):
                    items = raw_usd.get("items", [])
                    unverified_notes = raw_usd.get("unverified_notes", []) or res_usd.get("unverified_notes", [])
            except Exception as usd_err:
                print(f"[Agent] US live fallback error: {usd_err}")

        # Normalize price_inr and price on each item while strictly preserving ranking and order
        for item in items:
            raw_price = item.get("price", 0.0)
            curr = item.get("currency", "INR")
            if curr == "USD":
                item["price_inr"] = float(round(raw_price * (1 / 0.012)))
                item["price"] = item["price_inr"]
            else:
                item["price_inr"] = float(round(raw_price))
                item["price"] = item["price_inr"]

        # Log for purchase and checks dashboard
        log_search(query, budget_inr, items, unverified_notes)

        return {
            "success": True,
            "query": query,
            "budget_inr": budget_inr,
            "offers": items,
            "unverified_notes": unverified_notes
        }

    async def get_seller_explanation(self, seller: str, url: Optional[str] = None) -> str:
        """
        Agent Step 4:
        Calls explain_score on TRUSTMATE MCP server.
        """
        try:
            res = await self._call_mcp_tool("explain_score", {
                "seller": seller,
                "url": url or ""
            })
            if isinstance(res, dict):
                return res.get("summary", "No explanation available for this seller.")
            elif isinstance(res, str):
                return res
            return "No explanation available for this seller."
        except Exception as e:
            return f"Could not retrieve AI score explanation: {str(e)}"

agent = TrustmateAgent()
