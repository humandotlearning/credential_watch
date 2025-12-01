import os
import sys
import asyncio
from fastapi import FastAPI
import gradio as gr
import uvicorn

# Add src to path so we can import the package
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from credentialwatch_agent.main import demo, mcp_client

# Create FastAPI app
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Connect to MCP servers on startup."""
    print("Connecting to MCP servers...")
    # We can't use run_until_complete here because the loop is already running
    await mcp_client.connect()

@app.on_event("shutdown")
async def shutdown_event():
    """Close connections on shutdown."""
    print("Closing MCP connections...")
    await mcp_client.close()

# Mount Gradio app
# path="/" mounts it at the root
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    # Run with uvicorn
    # This ensures everything runs on the same async loop
    uvicorn.run(app, host="0.0.0.0", port=7860)
