import sys
import os
import asyncio

# Add src to path so we can import the package
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from credentialwatch_agent.main import demo, mcp_client

if __name__ == "__main__":
    # Simple async wrapper to run the app
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        print("Connecting to MCP servers...")
        loop.run_until_complete(mcp_client.connect())
        print("Starting Gradio app...")
        demo.launch()
    except KeyboardInterrupt:
        pass
    finally:
        print("Closing MCP connections...")
        loop.run_until_complete(mcp_client.close())
