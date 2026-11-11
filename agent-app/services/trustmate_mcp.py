"""
TRUSTMATE MCP Client Service for Person B
Uses official MCP Python SDK v2 Streamable HTTP client to communicate with Person A's server.
"""

import os
from typing import Any, Dict
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)
load_dotenv()

import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from mcp.types import TextContent

class TrustmateMCPError(RuntimeError):
    """Raised when the TRUSTMATE MCP call fails or returns invalid data."""

class TrustmateMCPService:
    """Client wrapper for the deployed TRUSTMATE MCP server."""

    ALLOWED_TOOLS = {
        "rank_offers",
        "get_trust_score",
        "explain_score",
    }

    def __init__(self) -> None:
        raw_url = os.getenv("TRUSTMATE_MCP_URL", os.getenv("TRUST_MCP_URL", "http://127.0.0.1:8001/mcp")).strip()
        if not raw_url.endswith("/mcp"):
            raw_url = f"{raw_url.rstrip('/')}/mcp"
        self.url = raw_url
        self.token = os.getenv("TRUSTMATE_MCP_BEARER_TOKEN", os.getenv("MCP_BEARER_TOKEN", "trustmate_test_secret_bearer_token_32chars")).strip()

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Call one of TRUSTMATE's public tools and return structured data."""

        if tool_name not in self.ALLOWED_TOOLS:
            raise TrustmateMCPError(f"Unsupported TRUSTMATE tool: {tool_name}")

        raw_url = os.getenv("TRUSTMATE_MCP_URL", os.getenv("TRUST_MCP_URL", self.url)).strip()
        if not raw_url.endswith("/mcp"):
            raw_url = f"{raw_url.rstrip('/')}/mcp"
        url = raw_url
        token = os.getenv("TRUSTMATE_MCP_BEARER_TOKEN", os.getenv("MCP_BEARER_TOKEN", self.token)).strip()

        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        timeout = httpx2.Timeout(30.0, read=120.0)

        try:
            async with httpx2.AsyncClient(
                headers=headers,
                timeout=timeout,
            ) as http_client:
                transport = streamable_http_client(
                    url,
                    http_client=http_client,
                )

                async with Client(transport) as client:
                    result = await client.call_tool(
                        tool_name,
                        arguments,
                        read_timeout_seconds=120.0,
                    )

            if result.is_error:
                messages = [
                    block.text
                    for block in result.content
                    if isinstance(block, TextContent)
                ]
                message = "\n".join(messages).strip()
                raise TrustmateMCPError(
                    message or f"TRUSTMATE tool '{tool_name}' returned an error."
                )

            structured = result.structured_content
            if isinstance(structured, dict):
                return structured

            # Fallback if content has text
            if result.content and len(result.content) > 0 and isinstance(result.content[0], TextContent):
                return {"summary": result.content[0].text}

            return {}

        except TrustmateMCPError:
            raise
        except (httpx2.TimeoutException, TimeoutError) as exc:
            raise TrustmateMCPError(
                "TRUSTMATE MCP request timed out. The service may be waking up "
                "or an upstream evidence provider may be slow."
            ) from exc
        except Exception as exc:
            raise TrustmateMCPError(
                f"Could not connect to TRUSTMATE MCP at {self.url}: {exc}"
            ) from exc

trustmate_mcp_service = TrustmateMCPService()
