import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Load env vars
load_dotenv(".env.local")

from credentialwatch_agent.mcp_client import mcp_client

async def verify_connection():
    print("Attempting to connect to MCP servers...")
    print(f"NPI URL: {os.getenv('NPI_MCP_URL')}")
    print(f"Cred DB URL: {os.getenv('CRED_DB_MCP_URL')}")
    print(f"Alert URL: {os.getenv('ALERT_MCP_URL')}")
    
    await mcp_client.connect()
    
    # Check internal state if possible, or try to call a tool
    # We can check if we are using mock data by inspecting the client's state if we exposed it,
    # but mcp_client.py doesn't expose a "is_mock" flag directly other than printing.
    # However, we can try to call a tool and see if we get a real response or the mock response.
    # The mock response for "npi" -> "search_providers" returns "Dr. Jane Doe".
    
    print(f"Mock mode: {mcp_client._mock_mode}")
    print(f"Connected: {mcp_client._connected}")
    print(f"Loaded tools: {list(mcp_client._tools.keys())}")
    
    print("\nTesting NPI tool call...")
    try:
        result = await mcp_client.call_tool("npi", "search_providers", {"query": "test"})
        print(f"Result: {result}")
    except Exception as e:
        print(f"Tool call failed: {e}")

    print("\nClosing...")
    await mcp_client.close()

if __name__ == "__main__":
    asyncio.run(verify_connection())
