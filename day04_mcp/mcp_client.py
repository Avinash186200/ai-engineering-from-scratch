"""A stdio MCP client: start the server as a subprocess, list tools, call them.

Run:  python day04_mcp/mcp_client.py
"""
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

SERVER = Path(__file__).with_name("fund_mcp_server.py")


async def main():
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("tools:", [t.name for t in tools.tools])
            for name, args in [("rank_funds", {"as_of": "2024-11-04", "top_n": 3}),
                               ("rank_funds", {"as_of": "2024-11-09"}),
                               ("lookup_term", {"term": "SIP"})]:
                res = await session.call_tool(name, args)
                text = res.content[0].text if res.content else res
                print(f"{name}({args}) -> {text}")


if __name__ == "__main__":
    asyncio.run(main())
