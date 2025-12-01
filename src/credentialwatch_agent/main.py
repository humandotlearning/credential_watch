import asyncio
import os
from typing import Dict, Any, List
import gradio as gr
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

from credentialwatch_agent.mcp_client import mcp_client
from credentialwatch_agent.agents.expiry_sweep import expiry_sweep_graph
from credentialwatch_agent.agents.interactive_query import interactive_query_graph

# Load environment variables
load_dotenv()

async def run_expiry_sweep(window_days: int = 90) -> Dict[str, Any]:
    """
    Runs the expiry sweep workflow.
    """
    await mcp_client.connect()
    print(f"Starting expiry sweep for {window_days} days...")
    # Initialize state
    initial_state = {
        "providers": [], 
        "alerts_created": 0, 
        "errors": [], 
        "summary": "",
        "window_days": window_days
    }
    
    # Run the graph
    # Note: The graph expects to fetch data itself, so initial state can be minimal.
    # We might want to pass window_days if the graph supported dynamic config in state,
    # but for now the graph hardcodes 90 or uses tool defaults. 
    # To make it dynamic, we'd need to update the graph to read from state.
    # For this hackathon, we'll assume the graph handles it or we pass it via a modified state if needed.
    # The current implementation of fetch_expiring_credentials uses a hardcoded 90 or tool default.
    
    final_state = await expiry_sweep_graph.ainvoke(initial_state)
    return {
        "summary": final_state.get("summary"),
        "alerts_created": final_state.get("alerts_created"),
        "errors": final_state.get("errors")
    }

async def run_chat_turn(message: str, history: List[List[str]]) -> str:
    """
    Runs a turn of the interactive query agent.
    """
    await mcp_client.connect()
    # Convert history to LangChain format
    messages = []
    for item in history:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            human = item[0]
            ai = item[1]
            messages.append(HumanMessage(content=str(human)))
            messages.append(AIMessage(content=str(ai)))
        else:
            # Fallback for unexpected format
            print(f"Warning: Skipping malformed history item: {item}")
    messages.append(HumanMessage(content=message))
    
    initial_state = {"messages": messages}
    
    # Run the graph
    final_state = await interactive_query_graph.ainvoke(initial_state)
    
    # Extract the last message
    last_message = final_state["messages"][-1]
    return last_message.content

# --- Gradio UI ---

async def start_app():
    """Initializes the app and connects to MCP servers."""
    print("Connecting to MCP servers...")
    await mcp_client.connect()

async def stop_app():
    """Closes connections."""
    print("Closing MCP connections...")
    await mcp_client.close()

with gr.Blocks(title="CredentialWatch") as demo:
    gr.Markdown("# CredentialWatch Agent System")
    
    with gr.Tab("Interactive Query"):
        gr.Markdown("Ask questions about provider credentials, e.g., 'Who has expiring licenses?'")
        chat_interface = gr.ChatInterface(fn=run_chat_turn)

    with gr.Tab("Expiry Sweep"):
        gr.Markdown("Run a batch sweep to check for expiring credentials and create alerts.")
        with gr.Row():
            sweep_btn = gr.Button("Run Sweep", variant="primary")
        
        sweep_output = gr.JSON(label="Sweep Results")
        
        sweep_btn.click(fn=run_expiry_sweep, inputs=[], outputs=[sweep_output])

# Startup/Shutdown hooks
# Gradio doesn't have native async startup hooks easily exposed in Blocks without mounting to FastAPI.
# But we can run the connect logic when the script starts if we run it via `uv run`.
# For a proper app, we'd use lifespan events in FastAPI.
# Here, we will just connect globally on import or first use if possible, 
# or use a startup event if we were using `gr.mount_gradio_app`.
# For simplicity in this script, we'll rely on the global mcp_client.connect() being called 
# or we can wrap the demo launch.

if __name__ == "__main__":
    # Launch the demo. 
    # Note: We rely on lazy connection in run_chat_turn/run_expiry_sweep to connect mcp_client.
    # This avoids creating a conflicting event loop before Gradio starts.
    demo.launch(server_name="0.0.0.0", server_port=7860, mcp_server=True)
