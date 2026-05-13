"""
agent/mcp_filesystem.py
=======================
Manages the lifecycle of the File System Model Context Protocol (MCP) server.
Provides clean orchestration for listing tools and calling filesystem resources.
"""

import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Absolute path to the exports directory — required by the MCP filesystem server
TARGET_EXPORT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "exports")
)

class MCPFilesystemManager:
    """Manages connection, initialization, and tool execution for the MCP Filesystem Server."""

    def __init__(self):
        self.server_params = StdioServerParameters(
            command="npx",
            args=[
                "-y",
                "@modelcontextprotocol/server-filesystem",
                TARGET_EXPORT_DIR,  
            ]
        )
        self._client_context = None
        self._session_context = None
        self.session = None

    async def __aenter__(self):
        """Asynchronously initializes the MCP process and handles protocol handshake."""
        self._client_context = stdio_client(self.server_params)
        read, write = await self._client_context.__aenter__()

        self._session_context = ClientSession(read, write)
        self.session = await self._session_context.__aenter__()
        await self.session.initialize()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Gracefully tears down open sessions and terminates the node sub-process."""
        if self._session_context:
            await self._session_context.__aexit__(exc_type, exc_val, exc_tb)
        if self._client_context:
            await self._client_context.__aexit__(exc_type, exc_val, exc_tb)

    async def list_available_tools(self):
        """Fetches capabilities exposed by the server filesystem plugin."""
        return await self.session.list_tools()

    async def list_exported_reports(self):
        """
        Lists all files in the exports directory.
        Path is the absolute exports dir — the server's allowed root —
        so this call is always within the permitted boundary.
        """
        return await self.session.call_tool(
            "list_directory", {"path": TARGET_EXPORT_DIR}
        )

# ---------------------------------------------------------------------------
# Standalone debug entry point
# ---------------------------------------------------------------------------
async def main():
    async with MCPFilesystemManager() as mcp:
        tools = await mcp.list_available_tools()
        print("Available Tools:", tools)

        reports = await mcp.list_exported_reports()
        print("Reports found:", reports)

if __name__ == "__main__":
    asyncio.run(main())