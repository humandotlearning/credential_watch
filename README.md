---
title: CredentialWatch
emoji: 🛡️
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 6.0.1
app_file: app.py
pinned: false
python_version: 3.11
---

# CredentialWatch 🛡️

**CredentialWatch** is a demo product for the **"MCP 1st Birthday / Gradio Agents Hackathon" (Hugging Face)**.

## 0. What I’m building (TL;DR)

- **Domain:** US-style healthcare admin / provider credentialing & expiries (state licenses, board certs, DEA/CDS, malpractice, hospital privileges, etc.).
- **Goal:** Show how **Model Context Protocol (MCP)** + **LangGraph agents** + **Gradio** + **Modal** + **SQLite** can turn messy, fragmented credential data into:
  - One unified, queryable view of each provider, and
  - A proactive alerting system for expiring / at-risk credentials.
- **Constraint:** Use only open / public tools & APIs (no closed vendor APIs, no real PHI).

## 1. Problem & motivation

**Real-world (simplified):**

- Provider groups (clinics, hospitals, multi-specialty practices) have **dozens of contracts** with different health plans and institutions.
- Multiple credentials can expire or go stale:
  - State licenses, board certifications, DEA/CDS numbers,
  - Malpractice insurance,
  - Hospital privileges, etc.
- Today:
  - Each health plan / hospital sends its own emails / portal tasks asking to update credentials and directory data.
  - Staff maintain local **spreadsheets, trackers, email threads**, often with inconsistent formats.
- It’s easy to miss an expiry, leading to:
  - Compliance issues,
  - Denied claims (revenue loss),
  - Inability to schedule or bill a provider after a certain date.

**CredentialWatch acts as a central radar:**
> “For all my providers, tell me what’s expiring when, what’s high risk, and log alerts we can action.”

## 2. Solution concept

CredentialWatch provides:

- A single, internal **“source-of-truth” SQLite DB** for providers, credentials and alerts.
- **Three separate MCP servers** (strict separation of concerns, each can be its own HF Space/repo):
  1. `npi_mcp` → read-only public provider info from **NPPES NPI Registry API**.
  2. `cred_db_mcp` → internal provider & credential DB operations.
  3. `alert_mcp` → alert logging, listing & resolution.
- A **LangGraph-based agent** that:
  - Periodically runs an **expiry sweep** and logs alerts.
  - Answers free-text questions like:
    - “Who has credentials expiring in the next 60 days in Cardiology?”
    - “Show me the credential snapshot for Dr. Jane Doe.”
- A **Gradio UI** where:
  - Judges/users chat with the agent,
  - They can click a “Run Nightly Sweep” button,
  - They see tables for “expiring soon” and an **Alert Inbox**.

## 3. Hackathon & design constraints

- **Event:** Hugging Face – MCP 1st Birthday / Gradio Agents Hackathon.
- **Judging goals:**
  - Strong MCP usage (tools/resources as first-class interfaces).
  - Agentic sophistication: planning, multi-step tool use, long-running flows.
  - Clear UX/Teachability.

**Constraints & safety:**
- Only **public / open APIs** (NPPES NPI Registry, OpenAI GPT).
- No real PHI: use synthetic/internal IDs + public NPI data.
- Safety boundaries:
  - Read-only to **external** systems.
  - Writes only to **internal** SQLite DB.

## 4. Tech stack 🧱

- **Language:** Python 3.11
- **Package management:** `uv`
- **Frontend / UI:** Gradio 6 (Hosted as a Hugging Face Space)
- **Agents:** LangGraph (Python)
- **LLM:** OpenAI `gpt-5.1` (or `gpt-4o`)
- **Tool protocol:** Model Context Protocol (MCP), via SSE.
- **Backend web framework:** FastAPI, running on **Modal**.
- **Database:** SQLite, persisted on a Modal volume.
- **ORM:** SQLAlchemy 2.x.

## 5. Architecture overview 🧩

### Logical components

**HF Space #1 – Agent UI (`credentialwatch-agent-ui`)**
- Gradio frontend.
- LangGraph agent runtime (`expiry_sweep_graph`, `interactive_query_graph`).
- MCP client configured for 3 remote MCP servers (via SSE).

**HF Space #2 – `npi_mcp`**
- MCP server for **NPI/NPPES** tools (`search_providers`, `get_provider_by_npi`).
- Calls `NPI_API` FastAPI service on Modal.

**HF Space #3 – `cred_db_mcp`**
- MCP server for internal data tools (`sync_provider_from_npi`, `add_or_update_credential`, etc.).
- Calls `CRED_API` FastAPI service on Modal.

**HF Space #4 – `alert_mcp`**
- MCP server for alert tools (`log_alert`, `get_open_alerts`, etc.).
- Calls `ALERT_API` FastAPI service on Modal.

**Modal backend**
- **FastAPI microservices**: `NPI_API`, `CRED_API`, `ALERT_API`.
- Shared **SQLite DB** on a Modal volume.

## 6. The 3 MCP servers – separation of concerns 🧱

### 6.1 `npi_mcp`
Read-only access to public provider data.
- `search_providers(query, state?, taxonomy?)`
- `get_provider_by_npi(npi)`

### 6.2 `cred_db_mcp`
Interface to internal provider & credential data.
- `sync_provider_from_npi(npi)`
- `add_or_update_credential(...)`
- `list_expiring_credentials(...)`
- `get_provider_snapshot(...)`

### 6.3 `alert_mcp`
Manage alerts generated by the agent.
- `log_alert(...)`
- `get_open_alerts(...)`
- `mark_alert_resolved(...)`

## 7. Agent behaviors (LangGraph) 🧠

### 7.1 `expiry_sweep_graph`
Batch / nightly graph.
1. Call `cred_db_mcp.list_expiring_credentials`.
2. Decide severity.
3. Call `alert_mcp.log_alert`.

### 7.2 `interactive_query_graph`
Chat / Q&A graph (ReAct-style).
- Plans tool calls (NPI, DB, Alerts).
- Summarizes results.

## 8. Database model 🗄️

**DB engine:** SQLite on Modal volume.

- `providers`: Internal provider records.
- `credentials`: Licenses, certifications, etc.
- `alerts`: Generated alerts for expiries.

---

## How to Run Locally

To run the CredentialWatch Agent UI locally:

1.  **Prerequisites:**
    - Python 3.11+
    - `uv` package manager

2.  **Environment Variables:**
    Create a `.env` file or set the following environment variables:
    ```bash
    OPENAI_API_KEY=sk-...
    # URLs for your deployed MCP servers (or local if running locally)
    NPI_MCP_URL=https://<your-npi-space>.hf.space/sse
    CRED_DB_MCP_URL=https://<your-cred-db-space>.hf.space/sse
    ALERT_MCP_URL=https://<your-alert-space>.hf.space/sse
    ```

3.  **Run the Agent:**
    ```bash
    uv run -m credentialwatch_agent.main
    ```
    This will start the Gradio interface locally at `http://localhost:7860`.
