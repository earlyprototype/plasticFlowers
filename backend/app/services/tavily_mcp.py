"""Tavily MCP SSE Client for remote web search.

This module connects to Tavily's remote MCP server over HTTP + SSE.
Spec: https://github.com/tavily-ai/tavily-mcp#remote-mcp-server

The remote MCP server accepts requests at:
    https://mcp.tavily.com/mcp/?tavilyApiKey=<api-key>
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, List, Optional, Dict

import httpx
from httpx_sse import aconnect_sse

from ..config import get_settings

logger = logging.getLogger(__name__)


class TavilyMCPError(RuntimeError):
    """Raised when Tavily MCP request fails."""


class _MCPInvalidParamsError(TavilyMCPError):
    """JSON-RPC invalid-params-class rejection of a tools/call request.

    Internal: used to trigger a single retry without the optional Tavily
    passthrough arguments (see _OPTIONAL_TOOL_ARGS).
    """

    def __init__(self, error: Any):
        super().__init__(f"MCP error: {error}")
        self.error = error


# Optional Tavily API passthrough args. The Tavily MCP tool schema has not
# always accepted these (an old comment here claimed include_answer was
# "not supported by MCP"), so if the server rejects the call with an
# invalid-params error we retry once without them.
_OPTIONAL_TOOL_ARGS = ("search_depth", "include_answer")


def _is_invalid_params_error(error: Any) -> bool:
    """True when a JSON-RPC error object looks like an invalid-params rejection."""
    if isinstance(error, dict):
        # -32602 is the JSON-RPC 2.0 "Invalid params" code.
        if error.get("code") == -32602:
            return True
        message = str(error.get("message", ""))
    else:
        message = str(error)
    message = message.lower()
    return any(
        marker in message
        for marker in ("invalid param", "invalid argument", "unknown argument", "unrecognized")
    )


def _build_client() -> httpx.AsyncClient:
    """Create the HTTP client for MCP calls (separate seam for test stubs)."""
    return httpx.AsyncClient(timeout=30.0)


@dataclass
class TavilySearchResult:
    """Single search result from Tavily."""
    title: str
    url: str
    content: str
    score: float = 0.0


@dataclass
class TavilySearchResponse:
    """Parsed response from Tavily search."""
    query: str
    results: List[TavilySearchResult]
    answer: Optional[str] = None  # Tavily can provide a direct answer


async def tavily_search(
    query: str,
    *,
    max_results: int = 5,
    search_depth: str = "basic",
    include_answer: bool = True,
) -> TavilySearchResponse:
    """Search using Tavily MCP remote server via httpx.

    Args:
        query: Search query string
        max_results: Maximum number of results (1-10)
        search_depth: "basic" or "advanced"
        include_answer: Ask Tavily for a synthesised direct answer
            (maps to the Tavily API's include_answer flag)

    Returns:
        TavilySearchResponse with results and optional answer

    Raises:
        TavilyMCPError: If the search fails. If the server rejects the
            optional args (invalid params), the call is retried once without
            them and only raises if that retry also fails.
    """
    settings = get_settings()
    api_key = settings.tavily_api_key.get_secret_value()

    if not api_key:
        raise TavilyMCPError("TAVILY_API_KEY is not configured")

    # Build MCP URL with API key
    mcp_url = f"{settings.tavily_mcp_url}?tavilyApiKey={api_key}"

    arguments = {
        "query": query,
        "max_results": max_results,
        "search_depth": search_depth,
        "include_answer": include_answer,
    }

    logger.info("tavily_mcp.search query=%s max_results=%d", query, max_results)

    try:
        result_data = await _call_tool(mcp_url, arguments)
    except _MCPInvalidParamsError as exc:
        # Self-heal: the server rejected the arguments; retry once without the
        # optional passthrough args. If the retry fails too, that error
        # propagates as TavilyMCPError.
        retry_arguments = {
            k: v for k, v in arguments.items() if k not in _OPTIONAL_TOOL_ARGS
        }
        logger.warning(
            "tavily_mcp.invalid_params rejected_args=%s error=%s - retrying without them",
            [k for k in _OPTIONAL_TOOL_ARGS if k in arguments],
            exc.error,
        )
        result_data = await _call_tool(mcp_url, retry_arguments)

    return _parse_tavily_response(query, result_data)


async def _call_tool(mcp_url: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute one tavily_search tools/call over HTTP+SSE, return result data.

    Raises:
        _MCPInvalidParamsError: server rejected the arguments (invalid params)
        TavilyMCPError: any other failure (HTTP, timeout, other MCP error)
    """
    # MCP tool call payload - JSON-RPC 2.0
    tool_call = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "tavily_search",
            "arguments": arguments,
        }
    }

    try:
        async with _build_client() as client:
            # We use client.stream directly to ensure Headers are exactly what Tavily wants
            # aconnect_sse helper might override Accept header
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }
            
            async with client.stream("POST", mcp_url, json=tool_call, headers=headers) as response:
                # Check initial response status
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise TavilyMCPError(
                        f"Tavily MCP returned {response.status_code}: {error_text.decode()}"
                    )

                # Wrap stream in EventSource parser from httpx_sse
                # We need to import EventSource class locally or at top
                from httpx_sse import EventSource
                
                # Iterate over SSE events
                result_data = {}
                async for sse in EventSource(response).aiter_sse():
                    if sse.data:
                        try:
                            # MCP sends JSON-RPC responses in the 'data' field
                            # e.g. data: {"jsonrpc": "2.0", "result": { ... }}
                            data = json.loads(sse.data)
                            
                            # Check for success result
                            if "result" in data:
                                result_data = data["result"]
                                # In typical MCP, we might get multiple events, but usually one result.
                                # Should we break on first result? 
                                # Tavily implementation tends to send one result block.
                                break 
                                
                            # Check for error
                            if "error" in data:
                                if _is_invalid_params_error(data["error"]):
                                    raise _MCPInvalidParamsError(data["error"])
                                raise TavilyMCPError(f"MCP error: {data['error']}")

                        except json.JSONDecodeError:
                            logger.warning("Failed to parse SSE data: %s", sse.data)
                            continue

                if not result_data:
                    # If we exhausted the stream without a result
                    raise TavilyMCPError("No result received from Tavily MCP stream")

                return result_data

    except httpx.TimeoutException:
        raise TavilyMCPError("Tavily MCP request timed out after 30s")
    except httpx.RequestError as exc:
        raise TavilyMCPError(f"Tavily MCP connection failed: {exc}") from exc


def _parse_tavily_response(query: str, data: Dict[str, Any]) -> TavilySearchResponse:
    """Convert raw Tavily response to typed dataclass."""
    
    # Handle MCP wrapper if present
    # The result structure from Tavily MCP tool is usually inside content list
    if "content" in data:
        # MCP returns tool results in content array
        # content: [{type: 'text', text: '...JSON string...'}]
        for content_item in data.get("content", []):
            if content_item.get("type") == "text":
                try:
                    # The inner text is the actual Tavily API JSON response
                    raw_text = content_item.get("text", "{}")
                    # Sometimes it's double encoded, or direct. 
                    # If it parses to a dict with 'results', we use it.
                    parsed_inner = json.loads(raw_text)
                    if isinstance(parsed_inner, dict) and ("results" in parsed_inner or "answer" in parsed_inner):
                        data = parsed_inner
                except json.JSONDecodeError:
                    pass

    # Now map 'results' list to our dataclass
    results = []
    for item in data.get("results", []):
        results.append(TavilySearchResult(
            title=item.get("title", ""),
            url=item.get("url", ""),
            content=item.get("content", item.get("snippet", "")),
            score=item.get("score", 0.0),
        ))
    
    return TavilySearchResponse(
        query=query,
        results=results,
        answer=data.get("answer"),
    )

__all__ = [
    "tavily_search",
    "TavilySearchResult",
    "TavilySearchResponse",
    "TavilyMCPError",
]
