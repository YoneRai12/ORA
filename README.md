# ORA Discord BOT - The "Singularity" Edition 🌌

[![Build](https://github.com/YoneRai12/ORA/actions/workflows/test.yml/badge.svg)](https://github.com/YoneRai12/ORA/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)](https://www.python.org/)
[![Discord](https://img.shields.io/badge/Discord-Join-7289DA?logo=discord)](https://discord.gg/YoneRai12)

### *The Living, Self-Healing AI Operating System for High-End PC*

ORA is not just a chatbot. It is a persistent **Artificial Lifeform** designed to inhabit a local high-performance PC (e.g., RTX 4090/5090). She listens to voice, sees your screen, manages your memories, and even **fixes her own code** when she crashes.

---

## 🔥 Key Technical Features

### 1. 🧬 Self-Healing Code (Immortal Architecture)
ORA catches unhandled exceptions at runtime and patches herself without shutting down.
- **Mechanism**: When a crash occurs, the `Healer` analyzes the traceback using GPT-5/4o.
- **Action**: It generates a git-compatible patch, applies it to the `.py` file, and hot-reloads the specific component (`Cog`).
- **Result**: "I fell, but I learned." The bot becomes more stable the longer it runs.

### 2. 🏠 Omni-Router (Hybrid Intelligence)
ORA dynamically routes requests between **Local VLLM** (Privacy/Speed) and **OpenAI Cloud** (Intelligence).

```mermaid
graph TD
    UserInput["User Prompt"] --> ModeCheck{User Mode?}

    %% Mode Selection
    ModeCheck -- "Private Mode" --> LocalPath
    ModeCheck -- "Smart Mode" --> ImageCheck{Has Image?}

    %% Image Branch
    ImageCheck -- "Yes" --> VisionRouter{Vision Router}
    VisionRouter -- "Use Burn Lane" --> Gemini[Gemini 2.0 Flash (Cloud)]
    VisionRouter -- "Fallback" --> LocalVision[Local VLLM (Visual)]

    %% Text Branch (Omni-Router)
    ImageCheck -- "No" --> OmniRouter{Analysis Logic}
    
    OmniRouter -- "Keyword: 'Code/Fix/API'" --> CodingModel[Model: gpt-4o/5.1-codex]
    OmniRouter -- "Length > 50 chars OR 'Explain/Deep'" --> HighModel[Model: gpt-4o / gpt-5.1]
    OmniRouter -- "Standard Chat" --> StdModel[Model: gpt-4o-mini]
    
    %% Cost & Limit Check
    CodingModel --> LimitCheck{Cost / Rate Limit OK?}
    HighModel --> LimitCheck
    StdModel --> LimitCheck
    
    LimitCheck -- "Yes" --> CloudDispatch
    LimitCheck -- "No (Quota Exceeded)" --> LocalPath

    %% Connection Layer (LLM Client)
    subgraph "🔌 Connection Router (LLMClient)"
        CloudDispatch[Selected Cloud Model] --> IsCloud{Name contains 'gpt-', 'codex', 'o1'?}
        LocalPath[Selected Local Model] --> IsCloud
        
        IsCloud -- "Yes" --> OpenAI["☁️ OpenAI API (Cloud)"]
        IsCloud -- "No" --> LocalAPI["🏠 Local VLLM (Localhost:8001)"]
    end

    %% Final Output
    OpenAI --> Response[Final Reply]
    LocalAPI --> Response
    Gemini --> Response
```

### 3. 👥 Shadow Clone (Zero-Downtime Updates)
- **Shadow Watcher**: A secondary process that monitors the Main Bot.
- **Seamless Restart**: When dragging/dropping a new file or updating, the Shadow keeps the Voice Connection alive.
- **Crash Safety**: If the Shadow detects a missing token or configuration error, it executes a `taskkill` on itself to prevent zombie processes.

### 4. 🧠 Memory & Context
- **Short-Term**: Remembers the last 20 messages in active RAM.
- **Long-Term**: Stores "Facts" and "Impressions" in `data/users/{id}.json`.
- **RAG**: Automatically recalls past conversations if the user asks "What did we talk about yesterday?".

---

## 🛠️ Installation & Setup

### Prerequisites
- **OS**: Windows 11 (Recommended) / Linux / Mac (M-Series)
- **Python**: 3.12+
- **GPU**: NVIDIA RTX 3060 or better (for Local LLM features)
- **Tools**: Git, FFmpeg (added to PATH)

### 1. Clone & Environment
```bash
git clone https://github.com/YoneRai12/ORA.git
cd ORA
python -m venv .venv
# Activate venv (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
```

### 2. Configuration (.env)
Create a `.env` file in the root directory. **DO NOT COMMIT THIS FILE.**

```ini
# Core Credentials
DISCORD_BOT_TOKEN=your_token_here
ADMIN_USER_ID=your_discord_id

# Cloud AI (Optional but Recommended)
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...

# Local AI Configuration (for VLLM)
LLM_BASE_URL=http://localhost:8001/v1
LLM_MODEL=Qwen/Qwen2.5-VL-32B-Instruct-AWQ

# System Settings
LOG_LEVEL=INFO
GAMING_PROCESSES=valorant.exe,ffxiv_dx11.exe
```

### 3. Launch
- **Windows**: Double-click `scripts/run_l.bat` (Auto-restart & Log rotation).
- **Manual**: `python src/bot.py`

---

## 🚀 Usage Guide

### Chat Modes
- **Smart Mode**: Routing enabled. Uses OpenAI for complex tasks, Local for simple ones.
- **Private Mode**: Forces Local LLM only. No data leaves your PC.
- **Switching**: `/mode smart` or `/mode private`

### Voice & Music
- **Join**: `/join` (Supports 24/7 connection)
- **TTS**: Uses local T5-Gemma or VoiceVox.
- **Music**: `/play [url]` (YouTube/Spotify support via `yt-dlp`).

### Imaging (Vision & Generation)
- **Analyze**: Drag & drop an image and ask "What is this?".
- **Generate**: "Draw a cyberpunk city" (Uses Local FLUX/SDXL or DALL-E 3 based on config).

---

## ⚠️ Security & Privacy
- **Local First**: By default, logs and memories are stored locally in `./data`.
- **Token Safety**: The bot includes a `TokenScanner` that prevents startup if `.env` is committed or exposed.
- **Admin Control**: Sensitive commands (`/heal`, `/shell`) are restricted to `ADMIN_USER_ID`.

---

## 🤝 Contributing
1. Fork the repo.
2. Create a feature branch.
3. Submit a PR. 
**Note**: Ensure `pre-commit` hooks pass and no secrets are included.

---

**License**: MIT
**Author**: YoneRai12
