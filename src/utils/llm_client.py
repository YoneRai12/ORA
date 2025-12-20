"""OpenAI-compatible client for LM Studio."""

from __future__ import annotations

import time
import asyncio
import json
import logging
import random
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)

class TransientHTTPError(RuntimeError):
    pass

# Global semaphore for rate limiting
_SEM = asyncio.Semaphore(10)

async def robust_json_request(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_data: Any = None,
    total_retry_budget: float = 300.0,
    max_attempts: int = 5,
    # Injectables for testing
    _sleep_func = asyncio.sleep,
    _time_func = time.monotonic
) -> Any:
    start_time = _time_func()
    deadline = start_time + total_retry_budget
    
    backoff = 1.0
    last_err = None
    
    for attempt in range(1, max_attempts + 1):
        # 1. Check Budget
        now = _time_func()
        remaining = deadline - now
        
        if remaining <= 0:
            raise asyncio.TimeoutError(f"Total retry budget ({total_retry_budget}s) exceeded")
            
        # 2. Determine Per-Attempt Timeout
        # Min of 300s or remaining budget (Large models take time to load)
        req_timeout_val = min(300.0, remaining)
        
        # 3. Acquire Semaphore
        try:
            async with _SEM:
                # 4. Execute Request
                timeout = aiohttp.ClientTimeout(
                    total=req_timeout_val,
                    connect=5.0,
                    sock_connect=5.0,
                    sock_read=300.0
                )
                
                try:
                    async with session.request(
                        method, 
                        url, 
                        headers=headers, 
                        params=params,
                        json=json_data, 
                        timeout=timeout
                    ) as resp:
                        status = resp.status
                        
                        # 5. Handle Retry-After
                        if status == 429 or 500 <= status < 600:
                            retry_after = float(resp.headers.get("Retry-After", 0))
                            if retry_after > 0:
                                # Check if we can afford to wait
                                current_remaining = deadline - _time_func()
                                if retry_after > current_remaining:
                                    logger.warning(f"Retry-After ({retry_after}s) > Remaining ({current_remaining:.2f}s). Aborting.")
                                    raise TransientHTTPError(f"Retry-After {retry_after}s exceeds budget")
                                await _sleep_func(retry_after)
                                continue
                            
                            raise TransientHTTPError(f"Transient status {status}")
                            
                        if 400 <= status < 500:
                            text = await resp.text()
                            raise RuntimeError(f"Non-retryable status {status}: {text[:200]}")
                        
                        # 6. Parse JSON
                        try:
                            return await resp.json(content_type=None)
                        except Exception as e:
                            text = await resp.text()
                            logger.error(f"JSON decode failed: {e}. Body: {text[:100]}...")
                            raise
                            
                except asyncio.CancelledError:
                    raise # Propagate immediately
                except Exception as e:
                    logger.warning(f"Request failed (Attempt {attempt}/{max_attempts}): {e}")
                    if isinstance(e, TransientHTTPError) and "exceeds budget" in str(e):
                        raise
                    last_err = e
                    # Fallthrough to retry logic
                    
        except asyncio.CancelledError:
            raise # Propagate immediately from semaphore wait
            
        # 7. Backoff
        if attempt < max_attempts:
            # Calculate backoff
            sleep_time = min(backoff + random.random() * 0.5, 8.0)
            
            # Check if sleep fits in budget
            now = _time_func()
            if now + sleep_time > deadline:
                 logger.warning("Backoff sleep would exceed budget. Aborting.")
                 break
                 
            await _sleep_func(sleep_time)
            backoff *= 2.0
            
    if last_err and not isinstance(last_err, TransientHTTPError):
        raise last_err
    raise RuntimeError("Max attempts reached")

class LLMClient:
    """Minimal async client for OpenAI-compatible chat completions."""

    def __init__(self, base_url: str, api_key: str, model: str, session: Optional[aiohttp.ClientSession] = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._session = session

    async def chat(self, messages: List[Dict[str, Any]], temperature: float = 0.7) -> str:
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }
        payload: Dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        
        # Use provided session or create temporary one
        if self._session:
            try:
                data = await robust_json_request(self._session, "POST", url, headers=headers, json_data=payload)
                return str(data["choices"][0]["message"]["content"])
            except (KeyError, IndexError, TypeError) as exc:
                raise RuntimeError("LLM応答の形式が不正です。") from exc
        else:
            async with aiohttp.ClientSession() as session:
                try:
                    data = await robust_json_request(session, "POST", url, headers=headers, json_data=payload)
                    return str(data["choices"][0]["message"]["content"])
                except (KeyError, IndexError, TypeError) as exc:
                    raise RuntimeError("LLM応答の形式が不正です。") from exc

    async def _unload_model_via_api(self) -> bool:
        """Attempt to unload the model via LM Studio/Ollama HTTP APIs and CLI fallbacks."""
        urls = [
            f"{self._base_url}/internal/model/unload",  # LM Studio
            f"{self._base_url}/chat/completions",  # Ollama fallback (keep_alive=0)
        ]

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        ollama_payload = {"model": self._model, "keep_alive": 0}
        success = False

        # Use throw-away session or existing
        session = self._session or aiohttp.ClientSession()
        owns_session = self._session is None

        try:
            if owns_session:
                await session.__aenter__()

            # 1. Try LM Studio Unload
            try:
                async with session.post(urls[0], headers=headers, json={}, timeout=2) as resp:
                    if resp.status == 200:
                        logger.info("✅ LM Studio Model Unloaded.")
                        return True
            except Exception as exc:
                logger.debug(f"LM Studio unload failed: {exc}")

            # 2. Try Ollama Unload
            try:
                async with session.post(urls[1], headers=headers, json=ollama_payload, timeout=2) as resp:
                    if resp.status == 200:
                        logger.info("✅ Ollama Model Unloaded (keep_alive=0).")
                        return True
            except Exception as exc:
                logger.debug(f"Ollama unload failed: {exc}")

        finally:
            if owns_session:
                await session.__aexit__(None, None, None)

        # 3. Try 'lms' CLI (Definitive Fix for LM Studio 0.3+)
        try:
            proc = await asyncio.create_subprocess_exec(
                "lms",
                "unload",
                "--all",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()

            if proc.returncode == 0:
                logger.info("✅ 'lms unload --all' executed successfully.")
                success = True
            else:
                logger.warning(f"'lms' CLI failed with code {proc.returncode}: {stderr.decode()}")
        except Exception as cli_e:
            logger.debug(f"Failed to run 'lms' CLI: {cli_e}")

        # 4. NUCLEAR OPTION: Taskkill
        try:
            proc = await asyncio.create_subprocess_exec(
                "taskkill",
                "/F",
                "/IM",
                "LM Studio.exe",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            logger.info("☢️ Nuclear Option Executed: Killed 'LM Studio.exe'")
            success = True
        except Exception as tk_e:
            logger.debug(f"Failed to taskkill LM Studio: {tk_e}")

        return success

    async def start_service(self) -> None:
        """Starts the LLM service (vLLM on WSL2)."""
        try:
            logger.info("🚀 Starting vLLM Service (WSL2)...")
            
            # Use 'wsl' command to launch vLLM in background (nohup or detached)
            # We use 'start' to detach from Python process
            cmd = (
                "wsl -d Ubuntu-22.04 nohup python3 -m vllm.entrypoints.openai.api_server "
                "--model Qwen/Qwen2.5-VL-32B-Instruct-AWQ --quantization awq --dtype half --gpu-memory-utilization 0.90 "
                "--max-model-len 2048 --enforce-eager --disable-custom-all-reduce --tensor-parallel-size 1 --port 8000 "
                "--trust-remote-code > vllm.log 2>&1 &"
            )
            
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            # Wait for it to spin up? (It takes ~20s)
            # We won't block here, the first request will just fail/retry.
            # But we should give it a head start.
            logger.info("⏳ Waiting 10s for vLLM to initialize...")
            await asyncio.sleep(10) 
            logger.info("✅ vLLM Launch signal sent.")
            
        except Exception as e:
            logger.error(f"Failed to start LLM service: {e}")

    async def _stop_vllm_service(self) -> bool:
        """Stops the LLM service (vLLM) to free VRAM."""
        try:
            logger.info("🛑 Stopping vLLM Service (pkill)...")
            cmd = "wsl -d Ubuntu-22.04 pkill -f vllm"

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            logger.info("✅ vLLM Stopped.")
            return True
        except Exception as e:
            logger.debug(f"Failed to stop vLLM: {e}")
            return False

    async def unload_model(self) -> None:
        """Best-effort VRAM release across both API-based and vLLM services."""
        try:
            api_released = await self._unload_model_via_api()
            service_stopped = await self._stop_vllm_service()

            if api_released or service_stopped:
                return

            logger.warning("Could not unload model (no API or service stop succeeded).")
        except Exception as e:
            logger.warning(f"Failed to unload model: {e}")


