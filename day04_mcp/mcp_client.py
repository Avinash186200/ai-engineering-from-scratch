"""A stdio MCP client: start the server as a child process, list tools, call them.

Run from the repo root:  python day04_mcp/mcp_client.py
The prints are also assertions, so a broken server fails loudly (a tiny end-to-end test).
"""
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parents[1]


def is_error(res) -> bool:          # mcp 1.x says isError, 2.x says is_error
    return bool(getattr(res, "isError", getattr(res, "is_error", False)))


async def main():
    params = StdioServerParameters(command=sys.executable,
                                    args=["day04_mcp/fund_mcp_server.py"],
                                    cwd=str(ROOT))

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print([t.name for t in tools.tools])
            assert "rank_funds" in [t.name for t in tools.tools]

            res = await session.call_tool("rank_funds", {"top_n": 3})
            print(json.loads(res.content[0].text))

            res = await session.call_tool("rank_funds", {"as_of": "2025-06-19", "top_n": 3})
            ranking = json.loads(res.content[0].text)
            print(ranking)
            assert [r["rank"] for r in ranking["top"]] == [1, 2, 3]

            res = await session.call_tool("rank_funds", {"as_of": "2025-06-21"})   # a Saturday
            print("weekend ->", json.loads(res.content[0].text), "| isError:", is_error(res))

            res = await session.call_tool("rank_funds", {"top_n": 500})            # schema says <= 20
            print("top_n=500 -> isError:", is_error(res), "|", res.content[0].text[:90])
            assert is_error(res)

            res = await session.call_tool("lookup_definition", {"term": "SIP"})
            print(json.loads(res.content[0].text))


if __name__ == "__main__":
    asyncio.run(main())
