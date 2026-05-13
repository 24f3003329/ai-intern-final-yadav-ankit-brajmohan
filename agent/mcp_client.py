"""
agent/mcp_client.py
===================
Public API for the MCP filesystem integration.

Bridges the async MCP protocol to Streamlit's synchronous execution model.
Each public function runs a self-contained asyncio event loop internally,
so callers never need to think about async.
"""

import asyncio
import os
from typing import List

from agent.mcp_filesystem import MCPFilesystemManager, TARGET_EXPORT_DIR


async def _async_list_reports() -> List[str]:
    """
    Connects to the MCP filesystem server, reads the exports directory,
    and returns a clean sorted list of .pdf / .txt filenames.

    The server prefixes each entry with its type, e.g. '[FILE] report.pdf',
    so we strip that prefix before filtering by extension.
    """
    async with MCPFilesystemManager() as mcp:
        result = await mcp.list_exported_reports()

    filenames: List[str] = []
    for block in result.content:
        if getattr(block, "type", None) == "text":
            for line in block.text.strip().splitlines():
                name = line.strip()
                for prefix in ("[FILE] ", "[DIR] "):
                    if name.startswith(prefix):
                        name = name[len(prefix):]
                        break
                if name.endswith(".pdf") or name.endswith(".txt"):
                    filenames.append(name)

    return sorted(filenames)


def list_reports() -> List[str]:
    """Returns a sorted list of exported report filenames via MCP."""
    return asyncio.run(_async_list_reports())


def delete_report(filename: str) -> None:
    """
    Removes a report from the exports directory.

    The MCP filesystem server does not expose a delete tool by design
    File removal is handled directly via os.remove instead.
    """
    file_path = os.path.join(TARGET_EXPORT_DIR, filename)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {filename}")
    os.remove(file_path)