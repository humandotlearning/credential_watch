import os
import asyncio
from typing import Any, Dict, List, Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

class MCPClient:
    """
    Abstraction for calling MCP tools from multiple servers.
    Manages connections to NPI, Credential DB, and Alert MCP servers.
    """

    def __init__(self):
        self.npi_url = os.getenv("NPI_MCP_URL", "http://localhost:8001/sse")
        self.cred_db_url = os.getenv("CRED_DB_MCP_URL", "http://localhost:8002/sse")
        self.alert_url = os.getenv("ALERT_MCP_URL", "http://localhost:8003/sse")
        
        self._exit_stack = AsyncExitStack()
        self._sessions: Dict[str, ClientSession] = {}
        self._connected = False
        self._connect_lock = asyncio.Lock()

    async def connect(self):
        """Establishes connections to all MCP servers. Idempotent."""
        async with self._connect_lock:
            if self._connected:
                return

            # Connect to NPI MCP
            try:
                # Note: mcp.client.sse.sse_client is a context manager that yields (read_stream, write_stream)
                # We need to keep the context open.
                npi_transport = await self._exit_stack.enter_async_context(sse_client(self.npi_url))
                self._sessions["npi"] = await self._exit_stack.enter_async_context(
                    ClientSession(npi_transport[0], npi_transport[1])
                )
                await self._sessions["npi"].initialize()
            except Exception as e:
                print(f"Warning: Failed to connect to NPI MCP at {self.npi_url}. Using mock data. Error: {e}")

            # Connect to Cred DB MCP
            try:
                cred_transport = await self._exit_stack.enter_async_context(sse_client(self.cred_db_url))
                self._sessions["cred_db"] = await self._exit_stack.enter_async_context(
                    ClientSession(cred_transport[0], cred_transport[1])
                )
                await self._sessions["cred_db"].initialize()
            except Exception as e:
                print(f"Warning: Failed to connect to Cred DB MCP at {self.cred_db_url}. Using mock data. Error: {e}")

            # Connect to Alert MCP
            try:
                alert_transport = await self._exit_stack.enter_async_context(sse_client(self.alert_url))
                self._sessions["alert"] = await self._exit_stack.enter_async_context(
                    ClientSession(alert_transport[0], alert_transport[1])
                )
                await self._sessions["alert"].initialize()
            except Exception as e:
                print(f"Warning: Failed to connect to Alert MCP at {self.alert_url}. Using mock data. Error: {e}")
            
            self._connected = True

    async def close(self):
        """Closes all connections."""
        await self._exit_stack.aclose()

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Calls a tool on a specific MCP server."""
        session = self._sessions.get(server_name)
        if not session:
            # Fallback for testing/mocking if connection failed
            print(f"Warning: No active session for {server_name}. Returning mock data.")
            return self._get_mock_response(server_name, tool_name, arguments)

        result = await session.call_tool(tool_name, arguments)
        return result

    def _get_mock_response(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Returns mock data when MCP server is unavailable."""
        if server_name == "npi":
            if tool_name == "search_providers":
                return {"providers": [{"npi": "1234567890", "name": "Dr. Jane Doe", "taxonomy": "Cardiology"}]}
            if tool_name == "get_provider_by_npi":
                return {"npi": arguments.get("npi"), "name": "Dr. Jane Doe", "licenses": []}
        
        if server_name == "cred_db":
            if tool_name == "list_expiring_credentials":
                return {"expiring": [{"provider_id": 1, "name": "Dr. Jane Doe", "credential": "Medical License", "days_remaining": 25}]}
            if tool_name == "get_provider_snapshot":
                return {"name": "Dr. Jane Doe", "status": "Active", "credentials": []}

        if server_name == "alert":
            if tool_name == "log_alert":
                return {"success": True, "alert_id": 101}
            if tool_name == "get_open_alerts":
                return {"alerts": []}

        return {"error": "Mock data not found for this tool"}

# Global instance
mcp_client = MCPClient()
