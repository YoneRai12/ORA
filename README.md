<div align="center">

# ORA (v5.1.14-Singularity) 🌌
### **The Artificial Lifeform AI System for High-End PC**

![ORA Banner](https://raw.githubusercontent.com/YoneRai12/ORA/main/docs/banner.png)

[![Release](https://img.shields.io/github/v/release/YoneRai12/ORA?style=for-the-badge&logo=github&color=blue)](https://github.com/YoneRai12/ORA/releases)
[![Build and Test](https://github.com/YoneRai12/ORA/actions/workflows/test.yml/badge.svg?style=for-the-badge)](https://github.com/YoneRai12/ORA/actions/workflows/test.yml)
[![Discord](https://img.shields.io/badge/Discord-Join-7289DA?style=for-the-badge&logo=discord)](https://discord.gg/YoneRai12)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

[**[📖 Manual]**](docs/USER_GUIDE.md) | [**[📂 Releases]**](https://github.com/YoneRai12/ORA/releases) | [**[🌐 Dashboard]**](http://localhost:3000)
| [**[📝 Release Notes]**](docs/RELEASE_NOTES.md)

---

[**English**](README.md) | [日本語](README_JP.md)

</div>

---

## 📖 What is ORA?

ORA is no longer just a "Bot". It is a **Living AI Operating System** that inhabits your high-end PC.
Designed to push the **RTX 5090** to its limits, she combines self-healing code, autonomous evolution, and multimodal vision into a single, seamless personal AI experience.

### 🚀 Key Features

*   **⚡ Hybrid Intelligence**: Intelligent routing between **Qwen 2.5-VL** (Fast Local) and **GPT-5.1** (Deep Cloud Reasoning).
*   **🧬 Auto-Healer**: When ORA encounters an error, she writes her own Python patch and hot-reloads herself.
*   **👁️ True Vision**: Real-time desktop/gameplay analysis via advanced Vision Transformers.
*   **🔒 Privacy First**: Your data stays on your machine. PII is handled exclusively by local models.

### 📊 Module Readiness Status

| Category | Component | Status | Description |
| :--- | :--- | :--- | :--- |
| **Thinking** | Omni-Router (Intent) | ✅ Stable | Context-aware brain routing |
| **Visual** | Vision / OCR | ✅ Stable | Real-time screen capture & analysis |
| **System** | Auto-Healer | 🛠️ In-Dev | Self-repair & GitHub sync logic |
| **Media** | Image Gen / Video | ✅ Stable | Local FLUX.2 / yt-dlp integration |
| **Platform** | Windows / Mac / Web | ✅ Active | Multi-frontend ecosystem support |

---

## 🔥 The "Big Three" Core Pillars

### 1. 🧬 Immortal Code (Self-Healing)
**"I fell down, but I fixed my leg and stood up. I am stronger now."**

Most software crashes when it hits a bug. ORA treats bugs as **learning opportunities**.
When a runtime error occurs (e.g., specific API failure), ORA:
1.  **Freezes** the crash state.
2.  **Analyzes** the traceback with her Logic Brain (GPT-5/4o).
3.  **Writes a Patch**: She edits her own `.py` source code locally.
4.  **Hot-Reloads**: She restarts *only* the broken component (Cog) without disconnecting from Voice.

> *Result: You can leave ORA running for months, and she will theoretically become more stable over time.*

### 2. 🧠 Current System Flow (Hub + Spoke)
ORA currently runs as a **Hub/Spoke agent pipeline**:
- `ChatHandler` (Discord/Web thin client) builds context, attachments, and selected tool schemas.
- `ORA Core API` (`/v1/messages`, `/v1/runs/{id}/events`) owns the reasoning loop.
- Tool calls are dispatched to the client, executed locally, then submitted back to Core via `/v1/runs/{id}/results`.
- Core resumes reasoning with tool outputs and emits the final answer.

### 🔄 End-to-End Request Path (Sequence)
```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant P as Discord/Web
    participant CH as ORA Bot (ChatHandler)
    participant EX as ORA Bot (Tool Executor + Policy Gate)
    participant CORE as ORA Core API (Run Owner)
    participant LT as Local Tools (Skills/MCP)
    participant ST as State/Storage (Audit DB + Temp Artifacts)

    U->>P: Prompt + attachments
    P->>CH: Normalized request (source, user, channel)
    CH->>CH: RAG + ToolSelector<br/>(filter available_tools)
    CH->>CORE: POST /v1/messages (create run)
    CORE-->>CH: run_id
    CH->>CORE: GET /v1/runs/{run_id}/events (SSE)

    loop Core-driven agent loop (Run Owner)
        CORE-->>CH: dispatch tool_call(tool, args, tool_call_id)
        CH->>EX: dispatch(tool, args, tool_call_id)
        EX->>EX: risk scoring (tags + args)
        opt approval required (HIGH/CRITICAL)
            EX->>P: show approval UI (buttons/modals)
            P-->>EX: approve/deny (request owner)
        end
        alt approved
            EX->>ST: audit log (decision + tool_call_id)
            EX->>LT: execute tool
            LT-->>EX: result (+ artifacts)
            EX->>ST: save artifacts (TTL cleanup)
            EX->>CORE: POST /v1/runs/{run_id}/results<br/>(tool_call_id + tool result)
        else denied/timeout
            EX->>ST: audit log (denied/timeout)
            EX->>CORE: POST /v1/runs/{run_id}/results<br/>(tool_call_id + denied/error)
        end
    end

    CORE-->>CH: final response event
    CH-->>P: formatted reply + files/links
    P-->>U: answer

    Note over EX,CORE: Tool results are at-least-once. Core should dedupe by tool_call_id (idempotency).
```

### 🧭 End-to-End Request Path (Swimlane)
```mermaid
flowchart LR
  subgraph L1["Platform"]
    U["User"] --> P["Discord/Web"]
    APPROVE["Approval UI<br/>(buttons/modals)"]
  end

  subgraph L2["Client (ORA Bot)"]
    CH["ChatHandler<br/>(context + RAG + tool selection)"]
    EX["Tool Executor (ToolHandler)<br/>+ Policy Gate (risk/approvals)"]
  end

  subgraph L3["Core (ORA Core API)"]
    MSG["POST /v1/messages<br/>(create run)"] --> EV["GET /v1/runs/{run_id}/events<br/>(SSE)"]
    RES["POST /v1/runs/{run_id}/results<br/>(tool output)"]
    ENG["Run Engine<br/>(agentic loop owner)"]
  end

  subgraph L4["Local Executors"]
    TOOLS["Skills/Tools"]
    MCP["MCP servers (stdio)"]
  end

  subgraph L5["State & Storage"]
    DB1[("Client SQLite<br/>ora_bot.db<br/>(audit/approvals/scheduler)")]
    MEM["Memory JSON<br/>memory/ (users + guilds)"]
    ART["Temp artifacts<br/>(downloads/screenshots, TTL)"]
    LOGS["Logs<br/>(ORA_LOG_DIR)"]
    VEC["Vector/RAG store<br/>(optional)"]
  end

  P --> CH --> MSG
  MSG --> EV --> CH --> EX
  EX --> TOOLS
  EX --> MCP
  EX --> RES --> ENG --> EV

  EX <--> APPROVE

  CH -.context.-> MEM
  CH -.rag.-> VEC
  EX -.audit.-> DB1
  EX -.artifacts.-> ART
  CH -.logs.-> LOGS
```

### 🏗️ Runtime Architecture (Current)
```mermaid
flowchart TB
  subgraph Platform["Clients"]
    D["Discord"]
    W["Web UI / API client"]
    AUI["Approval UI<br/>(buttons/modals)"]
  end

  subgraph Client["ORA Bot Process (this repo)"]
    CH["ChatHandler<br/>(context, routing, SSE)"]
    VH["VisionHandler"]
    RT["RAG + ToolSelector (local)"]
    TH["ToolHandler<br/>(Tool Executor + Policy Gate)"]
    WS["Web Service<br/>(admin/audit/browser endpoints)"]
    ST[("Client SQLite<br/>ora_bot.db")]
    MEM["Memory JSON<br/>memory/ (users + guilds)"]
    LOGS["Logs<br/>(ORA_LOG_DIR)"]
    ART["Temp artifacts<br/>(TTL cleanup)"]
  end

  subgraph Core["ORA Core Process (core/)"]
    API["Core API"]
    RUN["Run Engine<br/>(run state owner)"]
    CDB[("Core DB")]
  end

  subgraph Exec["Local Executors"]
    TOOLS["Tools/Skills"]
    MCP["MCP Servers (stdio)"]
    BROW["Browser Agent (Playwright)"]
  end

  subgraph Obs["Observability IDs"]
    IDS["correlation_id / run_id / tool_call_id"]
  end

  D --> CH
  W --> CH

  CH --> VH
  CH --> RT

  CH --> API
  API --> RUN --> CDB
  RUN --> API --> CH

  CH --> TH
  TH --> TOOLS
  TH --> MCP
  TH --> API
  TH <--> AUI

  TH -.audit.-> ST
  CH -.state.-> MEM
  CH -.logs.-> LOGS
  TH -.artifacts.-> ART
  TH --> BROW

  CH -.trace.-> IDS
  TH -.trace.-> IDS
```

### Routing & Tooling Notes (As Implemented)
1. Platform metadata (`source`, guild/channel context, admin flags) is injected before Core call.
2. The **agentic loop is Core-driven**: Core owns `run_id` state and emits tool calls; the client executes tools and submits results back.
3. Complexity-aware routing is done locally (ToolSelector/RAG) to keep tool exposure small and relevant.
3. Vision attachments are normalized and sent in canonical `image_url` shape for cloud models.
4. `web_download` supports Discord size-aware delivery and temporary 30-minute download pages.
5. Safety/permissions are enforced at a single choke point (Policy Gate at ToolHandler): risk scoring, approvals, and audit logging.
5. CAPTCHA/anti-bot pages are detected and handled by strategy switch, not bypass attempts.

### 3. 👥 Shadow Clone (Zero Downtime)
Updates usually mean "Downtime". Not for ORA.
When ORA needs to restart (for an update or self-healing), she spawning a **"Shadow Clone"** (Watcher Process).
*   The Shadow keeps the Voice Connection alive.
*   The Main Body dies, updates, and reborns.
*   **Crash Safety**: If the Shadow detects configuration errors (missing tokens), it forcefully kills itself to prevent zombie processes.

---

## 👁️ True Multimodal I/O (The "Senses")

ORA processes the world through **Images**, **Sound**, and **Text**.

### 1. Vision (The Eyes) 🖼️
ORA uses **Qwen 2.5-VL (Visual Language Model)** or **GPT-5-Vision** to "see" images.
*   **Screenshot Analysis**: Share a screenshot of your game or code, and she understands it.

### 2. Audio (The Ears & Voice) 🎤
*   **Multi-User Recognition**: ORA distinguishes *who* is speaking within 0.2s.
*   **Dynamic Tone**: Through prompt engineering, she acts as distinct personas (e.g., Tsundere, Maid) that you configure.

### 3. Generation (The Hands) 🎨
ORA creates content locally.
*   **Image Generation**: Uses **FLUX.2** or **Stable Diffusion XL** locally.

---

## 🛡️ NERV User Interface
A dedicated Web Dashboard (`http://localhost:3000`) for monitoring ORA's brain.
*   **Hex-Grid Visualizer**: See the status of every module.
*   **Memory Explorer**: View what ORA remembers about you.
*   **Process Killer**: One-click "Gaming Mode" to kill background bloatware and free up VRAM.

---

## ⚙️ Configuration Bible (.env)

| Variable | Description |
| :--- | :--- |
| `DISCORD_BOT_TOKEN` | **Required**. Your Bot Token. |
| `ADMIN_USER_ID` | **Required**. Your Discord User ID. |
| `OPENAI_API_KEY` | Optional. Required if using `gpt-*` models. |
| `LLM_BASE_URL` | Endpoint for Local LLM (Default: `http://localhost:8001/v1`). |
| `GAMING_PROCESSES` | Process names that trigger Gaming Mode (Low VRAM usage). |

---

## 🔁 Reproducible Setup & Versioning

### Local Repro Steps (same as CI)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -U pip
pip install -r requirements.txt
pip install ruff mypy pytest pytest-asyncio

ruff check .
mypy src/ --ignore-missing-imports
python -m compileall src/
pytest tests/test_smoke.py
```

### Release/Tag Rules
1. Update `VERSION` using SemVer (`X.Y.Z`).
2. Update changelog entries.
3. Create a git tag as `vX.Y.Z` and push it.

```bash
python scripts/verify_version.py --tag v5.1.8
git tag v5.1.8
git push origin v5.1.8
```

`release.yml` now fails if tag and `VERSION` do not match, so others can reproduce the same release artifact.

---

## 🤝 Contributing
1.  **Fork** the repository.
2.  **Create** a feature branch.
3.  **Commit** your changes.
4.  **Open a PR**.

**Rules:**
*   No hardcoded API keys.
*   Run `tools/debug/check_transformers.py` before submitting.

---

## 📜 License
Project ORA is licensed under **MIT License**.
You own your data. You own your intelligence.

<div align="center">

**Architected by YoneRai12**
*A project to blur the line between Software and Life.*

</div>
