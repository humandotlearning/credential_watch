import os
import asyncio
import logging
from typing import Any, Dict, List, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient

class MCPClient:
    """
    Abstraction for calling MCP tools from multiple servers.
    Manages connections to NPI, Credential DB, and Alert MCP servers.
    """

    def __init__(self):
        self.npi_url = os.getenv("NPI_MCP_URL", "http://localhost:8001/sse")
        self.cred_db_url = os.getenv("CRED_DB_MCP_URL", "http://localhost:8002/sse")
        self.alert_url = os.getenv("ALERT_MCP_URL", "http://localhost:8003/sse")
        
        self._client: Optional[MultiServerMCPClient] = None
        self._tools: Dict[str, Any] = {} # Cache tools
        self._mock_mode = False
        self._connected = False
        self._connect_lock = asyncio.Lock()
        
        # Configure logger
        self.logger = logging.getLogger("mcp_client")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    async def connect(self):
        """Establishes connections to all MCP servers."""
        async with self._connect_lock:
            if self._connected:
                return

            # Check if running on HF Spaces and using default localhost URLs
            is_hf = os.getenv("SPACE_ID") is not None
            
            # Helper to check if URL is localhost
            def is_localhost(url):
                return "localhost" in url or "127.0.0.1" in url

            # Normalize URLs for SSE
            def normalize_sse_url(url):
                if url.endswith("/"):
                    url = url[:-1]
                if not url.endswith("/sse"):
                    url += "/sse"
                return url

            npi_url = normalize_sse_url(self.npi_url)
            cred_db_url = normalize_sse_url(self.cred_db_url)
            alert_url = normalize_sse_url(self.alert_url)

            if is_hf and (is_localhost(npi_url) or is_localhost(cred_db_url) or is_localhost(alert_url)):
                self.logger.info("Detected Hugging Face Spaces environment with localhost URLs.")
                self.logger.info("Skipping actual MCP connections and defaulting to mock data.")
                self._mock_mode = True
                self._connected = True
                return

            self.logger.info("Initializing MultiServerMCPClient...")
            
            servers = {
                "npi": {
                    "transport": "sse",
                    "url": npi_url,
                },
                "cred_db": {
                    "transport": "sse",
                    "url": cred_db_url,
                },
                "alert": {
                    "transport": "sse",
                    "url": alert_url,
                }
            }
            
            # Add auth headers if needed
            if os.getenv("HF_TOKEN"):
                headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"}
                for server in servers.values():
                    server["headers"] = headers

            try:
                self._client = MultiServerMCPClient(servers)
                # Pre-fetch tools to verify connection and cache them
                tools_list = await self._client.get_tools()
                self._tools = {tool.name: tool for tool in tools_list}
                self.logger.info(f"Successfully connected. Loaded {len(self._tools)} tools.")
                self._connected = True
            except Exception as e:
                self.logger.error(f"Failed to initialize MCP client: {e}", exc_info=True)
                # If initialization fails, we might want to fallback to mock mode or just fail
                # For now, let's allow retry or fail gracefully
                pass

    async def close(self):
        """Closes all connections."""
        # MultiServerMCPClient might not have an explicit close, but we can clear it
        self._client = None
        self._connected = False
        self.logger.info("MCP connections closed.")

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Calls a tool. server_name is mostly for compatibility/mocking, as tools are flattened."""
        if not self._connected:
            await self.connect()
            
        if self._mock_mode:
             return self._get_mock_response(server_name, tool_name, arguments)

        # In MultiServerMCPClient, tools are flattened. 
        tool = self._tools.get(tool_name)
        
        # Fuzzy match if exact match fails
        if not tool:
            # Try to find a tool that contains the tool_name
            # We prioritize matches that end with the tool_name or tool_name_tool
            for name, t in self._tools.items():
                if name == tool_name:
                    tool = t
                    break
                if name.endswith(f"_{tool_name}") or name.endswith(f"_{tool_name}_tool") or name == f"{tool_name}_tool":
                    tool = t
                    break
                # Fallback: check if tool_name is in the name (less safe but helpful)
                if tool_name in name:
                    tool = t
                    # Keep searching for a better match (suffix)
                    continue
            
        if not tool:
            # Try to refresh tools
            if self._client:
                try:
                    tools_list = await self._client.get_tools()
                    self._tools = {t.name: t for t in tools_list}
                    tool = self._tools.get(tool_name)
                    # Retry fuzzy match after refresh
                    if not tool:
                        for name, t in self._tools.items():
                            if name.endswith(f"_{tool_name}") or name.endswith(f"_{tool_name}_tool") or name == f"{tool_name}_tool":
                                tool = t
                                break
                            if tool_name in name:
                                tool = t
                except Exception as e:
                     self.logger.error(f"Error refreshing tools: {e}")
        
        if not tool:
            self.logger.warning(f"Tool '{tool_name}' not found in loaded tools. Using mock if available.")
            return self._get_mock_response(server_name, tool_name, arguments)

        try:
            self.logger.info(f"Calling tool '{tool_name}' with args: {arguments}")
            # LangChain tools are callable or have .invoke
            result = await tool.ainvoke(arguments)
            self.logger.info(f"Tool '{tool_name}' returned successfully.")
            return result
        except Exception as e:
            self.logger.error(f"Error calling tool '{tool_name}': {e}", exc_info=True)
            raise

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
