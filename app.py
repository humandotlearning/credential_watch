import os
import sys
import asyncio
from fastapi import FastAPI
import gradio as gr
import uvicorn

# Add src to path so we can import the package
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from credentialwatch_agent.main import demo, mcp_client

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    print("Connecting to MCP servers...")
    try:
        await mcp_client.connect()
    except Exception as e:
        print(f"Error connecting to MCP servers: {e}")
    
    yield
    
    print("Closing MCP connections...")
    await mcp_client.close()

# Create FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# Mount Gradio app
# path="/" mounts it at the root
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    # Run with uvicorn
    # This ensures everything runs on the same async loop
    uvicorn.run(app, host="0.0.0.0", port=7860)
