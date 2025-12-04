from typing import Annotated, Literal, TypedDict, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from credentialwatch_agent.mcp_client import mcp_client
from credentialwatch_agent.agents.common import AgentState

# --- Tool Definitions ---

# Tools are now dynamically loaded from mcp_client


# --- Graph Definition ---

# We can use the prebuilt AgentState or our custom one.
# For simplicity, we'll use a state compatible with ToolNode (requires 'messages').

def get_interactive_query_graph():
    """
    Factory function to create the graph with dynamic tools.
    """
    tools = mcp_client.get_tools()
    
    async def agent_node(state: AgentState):
        """
        Invokes the LLM to decide the next step.
        """
        messages = state["messages"]
        model = ChatOpenAI(model="gpt-4o", temperature=0) 
        
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

    return workflow.compile()
