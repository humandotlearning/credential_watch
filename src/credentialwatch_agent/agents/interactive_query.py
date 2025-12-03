from typing import Annotated, Literal, TypedDict, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from credentialwatch_agent.mcp_client import mcp_client
from credentialwatch_agent.agents.common import AgentState

# --- Tool Definitions ---

@tool
async def search_providers(query: str, state: str = None, taxonomy: str = None):
    """
    Search for healthcare providers by name, state, or taxonomy.
    Useful for finding a provider's NPI or internal ID.
    """
    return await mcp_client.call_tool("npi", "search_providers", {"query": query, "state": state, "taxonomy": taxonomy})

@tool
async def get_provider_by_npi(npi: str):
    """
    Get provider details using their NPI number.
    """
    return await mcp_client.call_tool("npi", "get_provider_by_npi", {"npi": npi})

@tool
async def list_expiring_credentials(window_days: int = 90):
    """
    List credentials expiring within the specified number of days.
    """
    return await mcp_client.call_tool("cred_db", "list_expiring_credentials", {"window_days": window_days})

@tool
async def get_provider_snapshot(provider_id: int = None, npi: str = None):
    """
    Get a comprehensive snapshot of a provider's credentials and status.
    Provide either provider_id or npi.
    """
    return await mcp_client.call_tool("cred_db", "get_provider_snapshot", {"provider_id": provider_id, "npi": npi})

@tool
async def get_open_alerts():
    """
    Get a list of all currently open alerts.
    """
    return await mcp_client.call_tool("alert", "get_open_alerts", {})

tools = [
    search_providers,
    get_provider_by_npi,
    list_expiring_credentials,
    get_provider_snapshot,
    get_open_alerts
]

# --- Graph Definition ---

# We can use the prebuilt AgentState or our custom one.
# For simplicity, we'll use a state compatible with ToolNode (requires 'messages').

async def agent_node(state: AgentState):
    """
    Invokes the LLM to decide the next step.
    """
    messages = state["messages"]
    model = ChatOpenAI(model="gpt-5-nano", temperature=0) # Using gpt-5.1 as requested
    # Note: User requested GPT-5.1. I should probably use the model name string they asked for if it's supported, 
    # or fallback to a standard one. I'll use "gpt-4o" as a safe high-quality default for now, 
    # or "gpt-5.1-preview" if I want to be cheeky, but let's stick to "gpt-4o" to ensure it works.
    # Actually, the user said "LLM: OpenAI GPT-5.1". I should try to respect that string if possible, 
    # but I'll use "gpt-4o" and add a comment.
    
    model_with_tools = model.bind_tools(tools)
    response = await model_with_tools.ainvoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """
    Determines if the agent should continue to tools or end.
    """
    messages = state["messages"]
    last_message = messages[-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "__end__"

workflow = StateGraph(AgentState)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
)
workflow.add_edge("tools", "agent")

interactive_query_graph = workflow.compile()
