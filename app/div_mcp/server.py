from __future__ import annotations

import asyncio

from app.db.conn.db_async import async_engine
from app.div_mcp.tools import get_dividend_snapshot


try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover - optional runtime dependency
    FastMCP = None


if FastMCP is not None:
    mcp = FastMCP("divcore")

    @mcp.tool()
    async def get_dividend_snapshot_tool(limit: int = 100) -> dict:
        async with async_engine.begin() as db:
            return await get_dividend_snapshot(db, limit=limit)
else:
    mcp = None


async def main() -> None:
    if mcp is None:
        raise RuntimeError("Install the mcp package to run the dividend MCP server.")
    await mcp.run_stdio_async()


if __name__ == "__main__":
    asyncio.run(main())
