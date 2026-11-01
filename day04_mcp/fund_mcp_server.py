"""An MCP server (FastMCP, stdio) exposing the same three tools as day03.

Run directly:  python day04_mcp/fund_mcp_server.py     (waits for a client on stdin)
Test it:       python day04_mcp/mcp_client.py
"""
import sys
from pathlib import Path

try:                                   # mcp 1.x (what the videos show)
    from mcp.server.fastmcp import FastMCP
except ModuleNotFoundError:            # mcp 2.x renamed FastMCP to MCPServer
    from mcp.server.mcpserver import MCPServer as FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import fund_model  # noqa: E402

mcp = FastMCP("fund-research")


@mcp.tool()
def rank_funds(as_of: str | None = None, top_n: int = 5) -> dict:
    """Rank synthetic funds by predicted 21-day return on a business day (YYYY-MM-DD)."""
    return fund_model.rank_funds(as_of, top_n)


@mcp.tool()
def lookup_term(term: str) -> dict:
    """Define a mutual-fund term such as NAV, SIP, expense ratio or exit load."""
    return fund_model.lookup_term(term)


@mcp.tool()
def fund_info(name: str) -> dict:
    """Latest facts (category, NAV, expense ratio, AUM) for one fund by exact name."""
    return fund_model.fund_info(name)


if __name__ == "__main__":
    mcp.run()  # stdio transport by default
