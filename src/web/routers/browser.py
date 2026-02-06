from fastapi import APIRouter, HTTPException, Body, Depends, Header, Query, Request
from fastapi.responses import StreamingResponse, Response, JSONResponse
from pydantic import BaseModel
from typing import Optional, Any, Dict, List
import io
import asyncio
import json
import logging
import os
import traceback
import uuid
from datetime import datetime, timezone

from src.utils.browser import browser_manager
from src.utils.redaction import redact_text

router = APIRouter(tags=["browser"])
logger = logging.getLogger(__name__)


def _browser_log_dir() -> str:
    # Prefer env-driven log dir (same as config.log_dir) but keep router import-safe.
    base = (os.getenv("ORA_LOG_DIR") or "").strip() or "logs"
    os.makedirs(base, exist_ok=True)
    return base


def _write_browser_api_error(endpoint: str, exc: Exception, *, context: Optional[dict] = None) -> str:
    """Persist browser API errors to a dedicated log file for post-mortem debugging."""
    error_id = uuid.uuid4().hex[:10]
    ts = datetime.now(timezone.utc).isoformat()
    ctx = context if isinstance(context, dict) else {}
    ctx_text = ""
    try:
        ctx_text = json.dumps(ctx, ensure_ascii=False)[:2000]
    except Exception:
        ctx_text = ""
    payload = (
        f"[{ts}] endpoint={endpoint} error_id={error_id}\n"
        f"context={ctx_text}\n"
        f"type={type(exc).__name__}\n"
        f"message={redact_text(str(exc))}\n"
        f"{traceback.format_exc()}\n"
    )
    with open(os.path.join(_browser_log_dir(), "browser_api.log"), "a", encoding="utf-8", errors="ignore") as f:
        f.write(payload)
    return error_id

async def verify_token(
    request: Request,
    x_auth_token: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
):
    # Do not call Config.load() here; browser API may run standalone without Discord env vars.
    # Token can be provided via env only.
    browser_token = (
        os.getenv("BROWSER_REMOTE_TOKEN")
        or os.getenv("ORA_BROWSER_REMOTE_TOKEN")
        or ""
    ).strip()

    presented = (x_auth_token or token or "").strip()
    if browser_token:
        if presented != browser_token:
            raise HTTPException(status_code=401, detail="Invalid Remote Control Token")
        return

    # Security fallback: if no token is configured, only allow loopback callers.
    host = (request.client.host if request.client else "") or ""
    if host not in {"127.0.0.1", "::1", "localhost"}:
        raise HTTPException(status_code=503, detail="Remote control token is not configured")

    # Optional hardening switch: require token even on localhost.
    if os.getenv("REQUIRE_BROWSER_TOKEN", "0").strip() in {"1", "true", "yes", "on"}:
        raise HTTPException(status_code=503, detail="Browser token required but not configured")

class ActionRequest(BaseModel):
    action: Dict[str, Any]

class ModeRequest(BaseModel):
    headless: bool
    scope: Optional[str] = "session"
    domain: Optional[str] = ""
    apply: Optional[bool] = True

@router.post("/launch", dependencies=[Depends(verify_token)])
async def launch_browser():
    """Starts the browser session."""
    try:
        await browser_manager.start()
        return {"status": "started", "headless": browser_manager.headless}
    except Exception as e:
        error_id = _write_browser_api_error("/launch", e, context={"headless": getattr(browser_manager, "headless", None)})
        logger.exception("Browser /launch failed (error_id=%s)", error_id)
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e), "error_id": error_id})

@router.post("/action", dependencies=[Depends(verify_token)])
async def handle_action(req: ActionRequest = Body(...)):
    """
    Unified endpoint for browser actions, matching MeteoBOT's API.
    Expects payload: { "action": { "type": "...", ... } }
    """
    try:
        if not browser_manager.agent:
            # Auto-start if not running
            await browser_manager.ensure_active()

        # Use the agent's act method if available
        result = await browser_manager.agent.act(req.action)

        # In typical MeteoBOT fashion, some actions might return strict data
        # We need to ensure the response format matches what operator.html expects:
        # { "ok": bool, "result": ..., "observation": ... }

        # Get observation after action
        observation = await browser_manager.agent.observe()

        return {
            "ok": result.get("ok", False),
            "result": result,
            "observation": observation
        }
    except Exception as e:
        error_id = _write_browser_api_error("/action", e)
        logger.exception("Browser /action failed (error_id=%s)", error_id)
        # Match MeteoBOT error structure if possible: {"ok": False, "error": ...}
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e), "error_id": error_id, "result": {"error": str(e)}}
        )

@router.get("/state", dependencies=[Depends(verify_token)])
async def get_state():
    """
    Returns the current browser state including observation and headless status.
    Used by operator.html to update title, URL, etc.
    """
    try:
        await browser_manager.ensure_active()

        observation = await browser_manager.agent.observe()

        # Construct response
        return {
            "ok": True,
            "observation": observation,
            "headless": {
                "running": browser_manager.headless,
                "default": True, # config default
                "session": browser_manager.headless,
                "domain": None,
                "domain_name": ""
            }
        }
    except Exception as e:
         error_id = _write_browser_api_error("/state", e)
         logger.exception("Browser /state failed (error_id=%s)", error_id)
         return {"ok": False, "error": str(e), "error_id": error_id}

@router.get("/screenshot", dependencies=[Depends(verify_token)])
async def get_screenshot():
    """Returns a screenshot of the current page as a blob."""
    try:
        await browser_manager.ensure_active()
        data = await browser_manager.get_screenshot()
        if not data:
            raise RuntimeError("No screenshot bytes returned from browser manager.")
        return Response(content=data, media_type="image/jpeg")
    except Exception as e:
        # One hard restart retry helps recover from dead Playwright contexts.
        ctx = {"headless": getattr(browser_manager, "headless", None)}
        try:
            if getattr(browser_manager, "agent", None):
                obs = await browser_manager.agent.observe()
                ctx.update({"url": getattr(obs, "url", None), "title": getattr(obs, "title", None)})
        except Exception:
            pass
        first_error_id = _write_browser_api_error("/screenshot", e, context=ctx)
        logger.exception("Browser /screenshot failed (first attempt, error_id=%s)", first_error_id)
        try:
            await browser_manager.close()
            await browser_manager.start()
            data = await browser_manager.get_screenshot()
            if not data:
                raise RuntimeError("No screenshot bytes returned after browser restart.")
            return Response(content=data, media_type="image/jpeg")
        except Exception as retry_exc:
            second_error_id = _write_browser_api_error("/screenshot(retry)", retry_exc, context=ctx)
            logger.exception("Browser /screenshot failed (retry, error_id=%s)", second_error_id)
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": "Screenshot failed", "error_id": second_error_id, "detail": str(retry_exc)},
            )

@router.post("/mode")
async def set_mode(req: ModeRequest):
    """
    Updates the browser mode (headless/headful).
    """
    try:
        if req.apply:
            # Restart browser with new headless setting
            # This requires browser_manager to support restarting with config
            await browser_manager.close()
            browser_manager.headless = req.headless
            await browser_manager.start()

        return {
            "ok": True,
            "running_headless": browser_manager.headless,
            "default_headless": True,
            "session_headless": browser_manager.headless
        }
    except Exception as e:
        error_id = _write_browser_api_error("/mode", e, context={"headless": req.headless, "scope": req.scope, "domain": req.domain})
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e), "error_id": error_id})


@router.get("/errors", dependencies=[Depends(verify_token)])
async def get_recent_errors(limit: int = 20):
    """Return recent browser API errors (tail of browser_api.log)."""
    limit = max(1, min(200, int(limit)))
    path = os.path.join(_browser_log_dir(), "browser_api.log")
    if not os.path.exists(path):
        return {"ok": True, "data": [], "log_path": os.path.basename(path)}
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.read().splitlines()
        # Group by blocks starting with '[' timestamp.
        blocks: list[str] = []
        current: list[str] = []
        for line in lines:
            if line.startswith("[") and "]" in line and "error_id=" in line:
                if current:
                    blocks.append("\n".join(current))
                current = [line]
            else:
                if current:
                    current.append(line)
        if current:
            blocks.append("\n".join(current))
        blocks = blocks[-limit:]
        return {"ok": True, "data": blocks}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# Legacy endpoints support (optional, can keep for compatibility if needed)
@router.post("/navigate")
async def navigate_legacy(req: ActionRequest):
    # Dummy wrapper if something uses old endpoint, or just remove.
    # For now, let's stick to the new Operator API mainly.
    pass
