from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from credentialwatch_agent.agents.common import ExpirySweepState
from credentialwatch_agent.mcp_client import mcp_client

async def fetch_expiring_credentials(state: ExpirySweepState) -> Dict[str, Any]:
    """
    Fetches expiring credentials from the Credential DB MCP.
    """
    print("Fetching expiring credentials...")
    # We check for a window defined in state or default to 90.
    window_days = state.get("window_days", 90)
    result = await mcp_client.call_tool(
        "cred_db", 
        "list_expiring_credentials", 
        {"window_days": window_days}
    )
    
    # Handle mock/real response structure
    expiring_items = result.get("expiring", []) if isinstance(result, dict) else []
    
    return {"providers": expiring_items}

async def create_alerts(state: ExpirySweepState) -> Dict[str, Any]:
    """
    Creates alerts for the expiring credentials found.
    """
    expiring_items = state.get("providers", [])
    alerts_count = 0
    errors = []

    print(f"Found {len(expiring_items)} expiring items. Creating alerts...")

    for item in expiring_items:
        try:
            # Determine severity based on days_remaining
            days = item.get("days_remaining", 90)
            severity = "low"
            if days <= 30:
                severity = "critical"
            elif days <= 60:
                severity = "high"
            elif days <= 90:
                severity = "medium"

            provider_id = item.get("provider_id")
            credential_id = item.get("credential_id", "unknown") # Fallback if not provided in list
            message = f"Credential {item.get('credential')} for {item.get('name')} expires in {days} days."

            await mcp_client.call_tool(
                "alert",
                "log_alert",
                {
                    "provider_id": provider_id,
                    "credential_id": credential_id,
                    "severity": severity,
                    "message": message
                }
            )
            alerts_count += 1
        except Exception as e:
            errors.append(f"Failed to create alert for {item}: {e}")

    return {"alerts_created": alerts_count, "errors": errors}

async def summarize_sweep(state: ExpirySweepState) -> Dict[str, Any]:
    """
    Summarizes the sweep results.
    """
    count = len(state.get("providers", []))
    alerts = state.get("alerts_created", 0)
    errors = state.get("errors", [])
    
    summary = f"Sweep completed. Scanned {count} expiring items. Created {alerts} alerts."
    if errors:
        summary += f" Encountered {len(errors)} errors."
    
    return {"summary": summary}

# Build the graph
workflow = StateGraph(ExpirySweepState)

workflow.add_node("fetch_expiring_credentials", fetch_expiring_credentials)
workflow.add_node("create_alerts", create_alerts)
workflow.add_node("summarize_sweep", summarize_sweep)

workflow.set_entry_point("fetch_expiring_credentials")

workflow.add_edge("fetch_expiring_credentials", "create_alerts")
workflow.add_edge("create_alerts", "summarize_sweep")
workflow.add_edge("summarize_sweep", END)

expiry_sweep_graph = workflow.compile()
