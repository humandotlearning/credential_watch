---
title: CredentialWatch MCP Server
emoji: 🩺
colorFrom: blue
colorTo: purple
sdk: gradio
python_version: 3.10
sdk_version: 6.0.0
app_file: src/credentialwatch_agent/main.py
short_description: "MCP-enabled Gradio Space for credential monitoring."
tags:
  - mcp
  - gradio
  - healthcare
  - tools
pinned: false
---

# CredentialWatch MCP Server

Agent-ready Gradio Space that exposes healthcare credential tools (lookups, expiry checks, risk scoring) over **Model Context Protocol (MCP)**.

## Hugging Face Space

- **SDK**: Gradio
- **Entry file**: `src/credentialwatch_agent/main.py`
- **Python**: 3.10+

Deploy this repo as a Gradio Space and it will automatically serve both the web UI and an MCP server.

## MCP Server

This Space exposes its tools via Model Context Protocol (MCP) using Gradio.

### How MCP is enabled
In `src/credentialwatch_agent/main.py` we:
1. Install Gradio with MCP support: `pip install "gradio[mcp]"`
2. Define typed Python functions with docstrings
3. Launch the app with MCP support:
   ```python
   demo.launch(mcp_server=True)
   ```

Alternatively, you can set the environment variable:
```bash
export GRADIO_MCP_SERVER=True
```

### MCP endpoints
When the Space is running, Gradio exposes:
- **MCP SSE endpoint**: `https://<space-host>/gradio_api/mcp/sse`
- **MCP schema**: `https://<space-host>/gradio_api/mcp/schema`

## Using this Space from an MCP client

### Easiest: Hugging Face MCP Server (no manual config)
1. Go to your HF **MCP settings**: https://huggingface.co/settings/mcp
2. Add this Space under **Spaces Tools** (look for the MCP badge on the Space).
3. Restart your MCP client (VS Code, Cursor, Claude Code, etc.).
4. The tools from this Space will appear as MCP tools and can be called directly.

### Manual config (generic MCP client using mcp-remote)
If your MCP client uses a JSON config, you can point it to the SSE endpoint via `mcp-remote`:

```jsonc
{
  "mcpServers": {
    "credentialwatch": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://<space-host>/gradio_api/mcp/sse"
      ]
    }
  }
}
```
Replace `<space-host>` with the full URL of your Space.

## Local development

```bash
# 1. Install deps
uv sync

# 2. Run locally
uv run python src/credentialwatch_agent/main.py
# or
GRADIO_MCP_SERVER=True uv run python src/credentialwatch_agent/main.py
```

The local server will be available at `http://127.0.0.1:7860`, and MCP at `http://127.0.0.1:7860/gradio_api/mcp/sse`.

## Deploying to Hugging Face Spaces

1. Create a new Space with SDK = **Gradio**.
2. Push this repo to the Space (Git or `huggingface_hub`).
3. Ensure the YAML header in `README.md` is present and correct.
4. Wait for the Space to build and start — it should show an **MCP badge** automatically.

## Troubleshooting

- **README.md location**: Must be at the repo root and named `README.md` (all caps).
- **YAML Header**: Must be the very first thing in the file, delimited by `---`.
- **Configuration Error**: Check `sdk`, `app_file`, and `python_version` in the YAML.
- **MCP Badge Missing**: Ensure `demo.launch(mcp_server=True)` is called or `GRADIO_MCP_SERVER=True` is set, and the Space is public.

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
