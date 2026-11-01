"""An MCP server (FastMCP, stdio) exposing the fund tools from core/fund_model.py.

Run directly:  python day04_mcp/fund_mcp_server.py     (waits for a client on stdin)
Test it:       python day04_mcp/mcp_client.py
Never print() here: on stdio, stdout carries the protocol. Logs go to stderr.
"""
import logging
import sys
from pathlib import Path
from typing import Annotated

from pydantic import Field

try:                                   # mcp 1.x (what the videos show)
    from mcp.server.fastmcp import FastMCP
except ModuleNotFoundError:            # mcp 2.x renamed FastMCP to MCPServer
    from mcp.server.mcpserver import MCPServer as FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import fund_model  # noqa: E402
from core.fund_model import rank_funds as _rank_funds  # noqa: E402

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
log = logging.getLogger("fund-server")

mcp = FastMCP("fund-research")


@mcp.tool()
def rank_funds(
    as_of: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$",
                     description="Trading day, YYYY-MM-DD")] = "",
    top_n: Annotated[int, Field(ge=1, le=20,
                     description="How many funds to return")] = 5,
) -> dict:
    """Rank mutual funds by predicted return on a date."""
    return _rank_funds(as_of, top_n)


@mcp.tool()
def lookup_definition(term: str) -> dict:
    """Define a mutual fund term such as NAV, SIP, expense ratio or exit load."""
    return fund_model.lookup_definition(term)


@mcp.tool()
def model_info() -> dict:
    """Facts about the ranking models: features, target, training window."""
    return fund_model.model_info()


@mcp.tool()
def fund_info(name: str) -> dict:
    """Latest facts (category, NAV, expense ratio, AUM) for one fund by exact name."""
    return fund_model.fund_info(name)


# print("model loaded")          # WRONG: corrupts the protocol
log.info("model loaded")         # RIGHT: goes to stderr

if __name__ == "__main__":
    mcp.run()                              # stdio: local, for development
    # mcp.run(transport="streamable-http") # shared web service
