# CredentialWatch Agent

MCP-powered agent system for monitoring healthcare provider credentials. This system uses LangGraph to orchestrate workflows for checking credential expiry and answering interactive queries, leveraging Model Context Protocol (MCP) to connect to external data sources.

## Features

- **Interactive Query Agent**: Ask natural language questions about provider credentials.
- **Expiry Sweep Agent**: Automated workflow to check for expiring credentials and generate alerts.
- **MCP Integration**: Connects to NPI Registry, Credential Database, and Alerting systems via MCP.
- **Gradio UI**: User-friendly interface for interaction.

## Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) (recommended)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd credential_watch
    ```

2.  **Install dependencies:**
    ```bash
    uv sync
    ```

## Configuration

Create a `.env` file in the root directory (or copy `.env.local`) and configure your environment variables:

```env
OPENAI_API_KEY=your_openai_api_key
# MCP Server URLs (defaults shown)
NPI_MCP_URL=http://localhost:8001/sse
CRED_DB_MCP_URL=http://localhost:8002/sse
ALERT_MCP_URL=http://localhost:8003/sse
```

## Running the Application

To run the agent system with the Gradio UI using `uv`:

```bash
uv run python src/credentialwatch_agent/main.py
```
OR
```bash
uv run -m credentialwatch_agent.main
```

The UI will be available at `http://localhost:7860`.

## Architecture

- **`src/credentialwatch_agent/agents/`**: Contains LangGraph workflow definitions.
- **`src/credentialwatch_agent/mcp_client.py`**: Handles connections to MCP servers.
- **`src/credentialwatch_agent/main.py`**: Entry point and Gradio UI.

## MCP Servers

The agent expects the following MCP servers to be running:
1.  **NPI Server** (Port 8001)
2.  **Credential DB Server** (Port 8002)
3.  **Alert Server** (Port 8003)

If these servers are not reachable, the client will fall back to using mock data for demonstration purposes.
