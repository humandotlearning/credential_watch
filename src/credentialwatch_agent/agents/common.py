from typing import TypedDict, List, Optional, Any, Dict, Annotated
import operator

class AgentState(TypedDict):
    """
    Common state for agents.
    """
    messages: List[Dict[str, Any]]
    # Add other common fields if needed

class ExpirySweepState(TypedDict):
    """
    State for the expiry sweep graph.
    """
    providers: List[Dict[str, Any]]
    alerts_created: int
    errors: List[str]
    summary: str
    window_days: int

def merge_dicts(a: Dict, b: Dict) -> Dict:
    return {**a, **b}
