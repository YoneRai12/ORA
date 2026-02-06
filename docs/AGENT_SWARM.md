# ORA Agent Swarm (v5.1+)

## Goal
Turn ORA into a multi-tenant AI secretary platform ("everyone's assistant"), not a single-user bot.

## 5 Required Swarm Capabilities
1. **Task Decomposition**
   - Split complex requests into independent subtasks (`T1`, `T2`, `T3`...).
2. **Parallel Execution**
   - Run subtasks concurrently with worker limits (`ORA_SWARM_MAX_WORKERS`).
3. **Result Integration**
   - Merge subtask outputs into one execution brief before the main answer.
4. **Retry**
   - Retry failed subtasks automatically (`ORA_SWARM_MAX_RETRIES`).
5. **Observability**
   - Emit structured trace logs (`logs/agent_trace.jsonl`).

## Current Implementation
- Entry: `src/cogs/handlers/chat_handler.py`
- Orchestrator: `src/cogs/handlers/swarm_orchestrator.py`
- Trace sink: `src/utils/agent_trace.py`

Swarm activates on:
- Router complexity = `high`, or
- prompt contains explicit swarm intent (`swarm`, `サブエージェント`, `並列`)

## OpenAI-style Concepts (Mapping)
- **Handoffs**: each subtask has `role` (`researcher/planner/reviewer`) and is handed to a worker.
- **Guardrails**: dangerous patterns blocked before fan-out.
- **Tracing**: every phase emits `trace_event` with correlation ID.

## Claude Code-style Parallel Dev
- Recommended for code changes:
  - use git worktree per feature branch
  - assign sub-agents to separate worktrees
  - merge with CI gates + trace review

## K2-style Self-Orchestration + PARL (Practical Path)
- Keep online routing deterministic (temperature 0 for decomposition/merge).
- Store `(prompt, decomposition, outcome quality)` as training tuples.
- Periodically fine-tune/debias router policy from these tuples (PARL-like improvement loop).

## External Codex Process vs MCP Server
### Option A: External Process (App Server)
- Best when you need full session/thread/turn control and rich state.
- Higher implementation cost, more flexibility.

### Option B: MCP Tool Server (`codex mcp-server`)
- Faster integration, simpler ops, narrower scope.
- Good first production step.

### Recommended rollout
1. Start with MCP for safe, fast capability expansion.
2. Add external process only for advanced long-running dev workflows.

## 2026 Readiness Checklist
1. **MCP compatibility**
   - tool schema versioning
   - health checks and timeout budgets
2. **Permission Model**
   - tenant/guild/user-level ACL
   - tool-level allow/deny policy
3. **Isolation**
   - per-tenant context and storage boundaries
4. **Auditability**
   - immutable trace retention and redaction policy
5. **Safe evolution**
   - require approval for high-impact changes (code/system/network)

## Config
Add to `.env`:
```ini
ORA_SWARM_ENABLED=1
ORA_SWARM_MAX_TASKS=3
ORA_SWARM_MAX_WORKERS=3
ORA_SWARM_MAX_RETRIES=1
ORA_SWARM_SUBTASK_TIMEOUT_SEC=90
ORA_SWARM_MERGE_MODEL=gpt-5-mini
```

## Notes
- Swarm currently runs as **pre-analysis** for complex requests and feeds merged context into the main run.
- For production multi-tenant rollout, add per-tenant quotas and ACL checks before tool dispatch.
