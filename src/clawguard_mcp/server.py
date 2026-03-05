"""
ClawGuard Shield MCP Server

Exposes the ClawGuard Shield security scanning API as MCP tools
for use with Claude Desktop, Claude Code, Cursor, Windsurf, etc.

Usage:
    # Via uvx (recommended, zero-install):
    uvx clawguard-mcp

    # Via pip:
    pip install clawguard-mcp
    clawguard-mcp

    # Via python:
    python -m clawguard_mcp

Configuration:
    Set CLAWGUARD_API_KEY environment variable with your Shield API key.
    Get a free key at https://prompttools.co/api/v1/
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# Logging to stderr (CRITICAL: stdout is reserved for JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("clawguard-mcp")


@dataclass
class AppContext:
    """Typed context holding the HTTP client and config."""
    client: httpx.AsyncClient
    api_key: str
    base_url: str


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Create and manage the httpx client for the server's lifetime."""
    api_key = os.environ.get("CLAWGUARD_API_KEY", "")
    base_url = os.environ.get(
        "CLAWGUARD_BASE_URL", "https://prompttools.co/api/v1"
    )

    if not api_key:
        logger.warning(
            "CLAWGUARD_API_KEY not set. Get a free key at "
            "https://prompttools.co/api/v1/ — tools will return auth errors."
        )

    async with httpx.AsyncClient(
        base_url=base_url,
        headers={
            "X-API-Key": api_key,
            "Content-Type": "application/json",
            "User-Agent": "clawguard-mcp/0.1.0",
        },
        timeout=30.0,
    ) as client:
        logger.info(f"ClawGuard MCP server started (API: {base_url})")
        yield AppContext(client=client, api_key=api_key, base_url=base_url)
    logger.info("ClawGuard MCP server stopped")


mcp = FastMCP(
    "ClawGuard Shield",
    lifespan=app_lifespan,
)


def _get_app_context() -> AppContext:
    """Helper to retrieve the app context from the current request."""
    ctx = mcp.get_context()
    return ctx.request_context.lifespan_context


@mcp.tool()
async def scan_text(text: str, source: str = "mcp") -> dict[str, Any]:
    """Scan text for prompt injection and security threats.

    Analyzes the provided text using ClawGuard Shield's 42+ detection
    patterns to identify prompt injection attacks, jailbreak attempts,
    data exfiltration, social engineering, and other AI security threats.

    Returns a scan result with:
    - is_clean: whether the text is safe
    - risk_score: threat level from 0 (safe) to 10 (critical)
    - severity: NONE, LOW, MEDIUM, HIGH, or CRITICAL
    - findings: list of detected threats with pattern names and descriptions
    - scan_id: unique identifier for this scan

    Args:
        text: The text to scan for security threats.
        source: Optional source identifier for tracking (default: "mcp").

    Returns:
        Scan result with clean/dirty status, risk score, and findings.
    """
    app = _get_app_context()

    try:
        response = await app.client.post(
            "/scan",
            json={"text": text, "source": source},
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        return _format_error(e)
    except httpx.ConnectError:
        return {"error": "Cannot connect to ClawGuard Shield API. Is it running?"}


@mcp.tool()
async def scan_batch(texts: list[str]) -> list[dict[str, Any]]:
    """Scan multiple texts for security threats.

    Scans each text individually and returns all results. Useful for
    checking multiple user inputs, chat messages, or document sections
    in one call.

    Args:
        texts: List of texts to scan (max 10 per call).

    Returns:
        List of scan results, one per input text.
    """
    app = _get_app_context()

    if len(texts) > 10:
        return [{"error": "Maximum 10 texts per batch. Split into multiple calls."}]

    results = []
    for text in texts:
        try:
            response = await app.client.post(
                "/scan",
                json={"text": text, "source": "mcp-batch"},
            )
            response.raise_for_status()
            results.append(response.json())
        except httpx.HTTPStatusError as e:
            results.append(_format_error(e))
        except httpx.ConnectError:
            results.append({"error": "Connection failed", "text_preview": text[:50]})
    return results


@mcp.tool()
async def get_patterns() -> dict[str, Any]:
    """List all available ClawGuard detection patterns.

    Returns all 42+ security detection patterns organized by category:
    - prompt_injection: Override attempts, system tag spoofing
    - jailbreak: DAN, roleplay, hypothetical bypasses
    - data_exfiltration: Markdown image leaks, URL injection
    - social_engineering: Authority claims, credential phishing

    Each pattern includes its name, severity level, and description.
    No API key required.

    Returns:
        Dictionary with total pattern count and categories breakdown.
    """
    app = _get_app_context()

    try:
        response = await app.client.get("/patterns")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        return _format_error(e)
    except httpx.ConnectError:
        return {"error": "Cannot connect to ClawGuard Shield API."}


@mcp.tool()
async def get_usage() -> dict[str, Any]:
    """Get API usage statistics for your ClawGuard Shield account.

    Shows your current tier (free/pro/enterprise), daily request limits,
    today's usage count, remaining quota, and rate limit status.

    Requires a valid API key.

    Returns:
        Usage statistics including tier, limits, and request counts.
    """
    app = _get_app_context()

    try:
        response = await app.client.get("/usage")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        return _format_error(e)
    except httpx.ConnectError:
        return {"error": "Cannot connect to ClawGuard Shield API."}


@mcp.tool()
async def health_check() -> dict[str, Any]:
    """Check if the ClawGuard Shield API is healthy and responding.

    No API key required. Returns the service status, API version,
    number of active detection patterns, and response time.

    Use this to verify connectivity before running scans.

    Returns:
        Health status with service info and pattern count.
    """
    app = _get_app_context()

    try:
        response = await app.client.get("/health")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        return _format_error(e)
    except httpx.ConnectError:
        return {
            "error": "Cannot connect to ClawGuard Shield API.",
            "hint": "Check that the API is running at " + app.base_url,
        }


def _format_error(e: httpx.HTTPStatusError) -> dict[str, Any]:
    """Format HTTP errors into structured error responses."""
    status = e.response.status_code
    try:
        body = e.response.json()
        message = body.get("error", str(e))
    except Exception:
        message = str(e)

    error_map = {
        401: "Invalid API key. Get a free key at https://prompttools.co/api/v1/",
        403: "Access denied. Your tier may not support this feature.",
        429: "Rate limit exceeded. Upgrade at https://prompttools.co/shield",
    }

    return {
        "error": error_map.get(status, message),
        "status_code": status,
    }


def main():
    """Run the ClawGuard Shield MCP server (stdio transport)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
