from __future__ import annotations

import asyncio
import json
import logging
import os
import shlex
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _redact_cmd(cmd: list[str]) -> str:
    # Best-effort redaction: never log full tokens/keys even if user passes them in command args.
    sensitive = ("key", "token", "secret", "password", "auth", "bearer")
    out: list[str] = []
    for part in cmd:
        low = part.lower()
        if any(s in low for s in sensitive):
            out.append("[REDACTED]")
        elif len(part) > 120:
            out.append(part[:60] + "…" + part[-20:])
        else:
            out.append(part)
    return " ".join(out)


def _encode_frame(payload: dict) -> bytes:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    return header + body


async def _read_exact(stream: asyncio.StreamReader, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = await stream.read(n - len(buf))
        if not chunk:
            break
        buf.extend(chunk)
    return bytes(buf)


async def _read_mcp_message(stream: asyncio.StreamReader) -> Optional[dict]:
    """
    Read one MCP/JSON-RPC message from a stdio stream.

    Supports:
    - LSP-style framing: Content-Length headers
    - Fallback: newline-delimited JSON
    """
    # Try header framing first.
    header_bytes = bytearray()
    while True:
        line = await stream.readline()
        if not line:
            return None
        header_bytes.extend(line)
        if header_bytes.endswith(b"\r\n\r\n") or header_bytes.endswith(b"\n\n"):
            break
        # Guard: if stream isn't using headers, stop early and try JSON-lines.
        if len(header_bytes) > 8192:
            break

    header_text = header_bytes.decode("utf-8", errors="ignore")
    if "content-length" in header_text.lower():
        length = None
        for raw in header_text.splitlines():
            if raw.lower().startswith("content-length:"):
                try:
                    length = int(raw.split(":", 1)[1].strip())
                except Exception:
                    length = None
                break
        if not length or length <= 0 or length > 50_000_000:
            return None
        body = await _read_exact(stream, length)
        if not body:
            return None
        try:
            return json.loads(body.decode("utf-8", errors="ignore"))
        except Exception:
            return None

    # JSON-lines fallback: header_bytes actually contains the JSON line.
    try:
        txt = header_bytes.decode("utf-8", errors="ignore").strip()
        if not txt:
            return None
        return json.loads(txt)
    except Exception:
        return None


@dataclass(frozen=True)
class MCPTool:
    name: str
    description: str
    input_schema: Dict[str, Any]


class MCPStdioClient:
    """
    Minimal MCP client over stdio.

    This intentionally avoids any external MCP dependency so ORA remains portable.
    """

    def __init__(self, *, name: str, command: str, cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None):
        self.name = name
        self.command_str = command
        self.command = shlex.split(command, posix=os.name != "nt")
        self.cwd = cwd
        self.env = env or {}

        self._proc: Optional[asyncio.subprocess.Process] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._pending: dict[int, asyncio.Future] = {}
        self._id = 1
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        if self._proc and self._proc.returncode is None:
            return

        merged_env = os.environ.copy()
        merged_env.update({k: str(v) for k, v in (self.env or {}).items()})

        logger.info("MCP starting server=%s cmd=%s", self.name, _redact_cmd(self.command))
        self._proc = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.cwd,
            env=merged_env,
        )
        assert self._proc.stdout and self._proc.stdin
        self._reader_task = asyncio.create_task(self._reader_loop())
        # Best-effort initialize. Many servers will accept it; some ignore.
        try:
            await self.request(
                "initialize",
                {
                    "clientInfo": {"name": "ORA", "version": "mcp-0"},
                    "capabilities": {"tools": {}},
                },
                timeout=10,
            )
        except Exception:
            # Don't hard-fail on initialize for compatibility.
            pass

    async def close(self) -> None:
        if self._reader_task:
            self._reader_task.cancel()
            self._reader_task = None
        if self._proc and self._proc.returncode is None:
            try:
                self._proc.terminate()
            except Exception:
                pass
            try:
                await asyncio.wait_for(self._proc.wait(), timeout=3)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
        self._proc = None

    async def _reader_loop(self) -> None:
        assert self._proc and self._proc.stdout
        while True:
            msg = await _read_mcp_message(self._proc.stdout)
            if msg is None:
                return
            if not isinstance(msg, dict):
                continue
            if "id" in msg and (msg.get("result") is not None or msg.get("error") is not None):
                try:
                    mid = int(msg.get("id"))
                except Exception:
                    continue
                fut = self._pending.pop(mid, None)
                if fut and not fut.done():
                    fut.set_result(msg)

    async def request(self, method: str, params: Optional[dict] = None, timeout: int = 60) -> dict:
        await self.start()
        assert self._proc and self._proc.stdin

        async with self._lock:
            req_id = self._id
            self._id += 1

            fut: asyncio.Future = asyncio.get_event_loop().create_future()
            self._pending[req_id] = fut
            payload = {"jsonrpc": "2.0", "id": req_id, "method": method}
            if params is not None:
                payload["params"] = params
            self._proc.stdin.write(_encode_frame(payload))
            await self._proc.stdin.drain()

        try:
            msg = await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError as e:
            self._pending.pop(req_id, None)
            raise TimeoutError(f"MCP timeout server={self.name} method={method}") from e

        if not isinstance(msg, dict):
            raise RuntimeError(f"MCP invalid response server={self.name}")
        if msg.get("error"):
            raise RuntimeError(f"MCP error server={self.name} method={method}: {msg.get('error')}")
        return msg.get("result") or {}

    async def list_tools(self) -> list[MCPTool]:
        # Spec/common: tools/list
        res = None
        for method in ("tools/list", "tools.list", "list_tools"):
            try:
                res = await self.request(method, {}, timeout=20)
                break
            except Exception:
                continue
        if not isinstance(res, dict):
            return []
        tools = res.get("tools") or res.get("result") or res.get("data") or []
        out: list[MCPTool] = []
        if isinstance(tools, list):
            for t in tools:
                if not isinstance(t, dict):
                    continue
                name = str(t.get("name") or "").strip()
                if not name:
                    continue
                desc = str(t.get("description") or "").strip()
                schema = t.get("inputSchema") or t.get("input_schema") or t.get("parameters") or {}
                if not isinstance(schema, dict):
                    schema = {}
                out.append(MCPTool(name=name, description=desc, input_schema=schema))
        return out

    async def call_tool(self, tool_name: str, arguments: Optional[dict] = None, timeout: int = 180) -> dict:
        args = arguments if isinstance(arguments, dict) else {}
        # Spec/common: tools/call
        res = None
        for method in ("tools/call", "tools.call", "call_tool"):
            try:
                res = await self.request(method, {"name": tool_name, "arguments": args}, timeout=timeout)
                break
            except Exception:
                continue
        if not isinstance(res, dict):
            return {"ok": False, "error": "invalid_response", "raw": res}
        return res

