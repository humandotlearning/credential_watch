import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from credentialwatch_agent.mcp_client import mcp_client

async def reproduce():
    print("Connecting using mcp_client...")
    await mcp_client.connect()
    print("Connected (or failed gracefully).")
    
    # Simulate some work
    await asyncio.sleep(1)
    
    print("Closing...")
    await mcp_client.close()
    print("Closed.")

if __name__ == "__main__":
    try:
        asyncio.run(reproduce())
    except Exception as e:
        print(f"Top level error: {e}")
