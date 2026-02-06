# ORA Release Notes

This page is a curated summary of what changed across releases (beyond GitHub’s auto-generated notes).

## v5.0.0 -> v5.1.12 (2026-02-06)

### Big Picture (What You Actually Got)
- **Hub/Spoke agent runtime stabilized**: thin client (Discord/Web) delegates the reasoning loop to ORA Core; tools execute locally and results are fed back to Core.
- **Security posture tightened**: fewer “surprise side effects” at startup; approvals/audit added so powerful tooling doesn’t silently become dangerous as features grow.
- **Multi-platform direction clarified**: Discord bot is no longer “the product”; it’s one client for a broader ORA API + web dashboards + future mobile/desktop clients.

### Security & Safety (High Impact)
- **Risk-based approvals gate + audit trail**:
  - Tool execution is gated at the ToolHandler boundary (skills, dynamic tools, MCP tools all funnel through one checkpoint).
  - **Owner is NOT exempt**: HIGH requires approval; CRITICAL requires 2-step confirmation (button + code).
  - SQLite tables `tool_audit` and `approval_requests` store “who did what, when, with what args (redacted), and what happened”.
- **Safe startup defaults (no auto-expose)**:
  - Bot no longer auto-opens local browser UIs unless explicitly enabled.
  - Bot no longer auto-starts Cloudflare tunnels unless explicitly enabled.
  - Quick tunnels (trycloudflare) blocked by default unless explicitly enabled.

### Tooling & Extensibility
- **MCP client support (stdio)**:
  - ORA can connect to configured MCP servers and expose their tools as ORA tools named like `mcp__<server>__<tool>`.
  - MCP tools are routed through the same approvals/audit gate.
- **Router/tool selection hardening**:
  - Caps tool exposure to avoid massive tool lists.
  - Adds categories so “codebase inspection” tools are only exposed when appropriate.
  - Avoids selecting remote browser tools unless the user explicitly asks for screenshot/control.

### Memory (User + Server Context)
- **Guild/server context memory**:
  - Adds guild-level hints to bias acronym/domain disambiguation (example: VALORANT servers).
  - Keeps it deterministic (no extra LLM calls) and injects into system context.

### Web / Media / UX Fixes That Matter
- **Discord embed hard limit fix**:
  - Prevents 400 errors caused by embed title length > 256.
- **Downloads & screenshots cleanup**:
  - Temp artifacts (screenshots/download files) are deleted after use in tool implementations.
  - Large downloads can be delivered via temporary link pages when Discord limits are exceeded (TTL based).

### Observability & Reproducibility
- **Portable logging paths**:
  - Logging now follows `config.log_dir` (env-driven) rather than hardcoding `L:\...` paths.
  - Guild logs and local log reader follow the same base directory.
- **CI/release pipeline made stricter and reproducible**:
  - Release workflow verifies tag == `VERSION`.
  - CI runs `ruff`, `mypy`, `compileall`, smoke tests without requiring real secrets.

### Upgrade Notes (If You Want Old Behavior)
If you previously relied on “startup auto-open” and “startup auto-tunnel”, set these in your `.env`:
- `ORA_AUTO_OPEN_LOCAL_INTERFACES=1`
- `ORA_AUTO_START_TUNNELS=1`
- `ORA_TUNNELS_ALLOW_QUICK=1` (only if you explicitly want quick tunnels without a named token)

## Per-Version Highlights (Quick Index)
- **v5.1.12**: CI mypy fix (`Store.create_scheduled_task()` return).
- **v5.1.11**: Startup safety defaults (no auto browser/tunnels unless enabled).
- **v5.1.10**: Portable logging paths (no L:\ hardcoding).
- **v5.1.9**: Discord embed title length safety.
- **v5.1.8**: Risk-based approvals gate + tool audit (SQLite).
- **v5.1.6 / v5.1.7**: MCP tool server support + routing category.
- **v5.1.5**: Guild memory + router cap + final response robustness + CI convenience.
- **v5.1.4**: Core SSE retry robustness.
- **v5.1.3**: Owner-only scheduler scaffold (disabled by default).
- **v5.1.2**: Dynamic task board; cleanup guarantees; download page cleanup loop.
- **v5.1.0 / v5.0.0**: Architecture diagrams + reproducible release alignment.

