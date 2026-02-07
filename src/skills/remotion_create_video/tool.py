import asyncio
import json
import logging
import os
import shutil
import tempfile
import uuid
from typing import Any, Optional

import discord

from src.utils.temp_downloads import create_temporary_download, ensure_download_public_base_url

logger = logging.getLogger(__name__)


TOOL_SCHEMA = {
    "name": "remotion_create_video",
    "description": (
        "Remotionで短い動画を生成してDiscordへ送信します。Discord上限を超える場合は30分限定DLページを発行します。"
        "用途: タイトルカード、画像+字幕などの簡易動画作成。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "preset": {
                "type": "string",
                "enum": ["title_card", "caption_image"],
                "description": "動画テンプレ。title_card=テキストだけ / caption_image=画像+字幕。",
            },
            "title": {"type": "string", "description": "メインタイトル（title_card用）。"},
            "subtitle": {"type": "string", "description": "サブタイトル（title_card用）。"},
            "caption": {"type": "string", "description": "字幕（caption_image用）。"},
            "image_url": {"type": "string", "description": "背景画像のURL（caption_image用）。"},
            "duration_sec": {"type": "number", "description": "動画秒数。既定6秒。"},
            "fps": {"type": "integer", "description": "FPS。既定30。"},
            "resolution": {
                "type": "string",
                "enum": ["720p", "1080p", "4k"],
                "description": "解像度。既定1080p。",
            },
            "output": {
                "type": "string",
                "enum": ["mp4", "webm", "gif"],
                "description": "出力形式。既定mp4。",
            },
            "filename": {"type": "string", "description": "保存ファイル名（省略可）。"},
        },
        "required": ["preset"],
    },
    "tags": ["video", "create", "render", "remotion", "media", "exec"],
}


def _fmt_size_mb(size_bytes: Optional[int]) -> str:
    if not size_bytes:
        return "unknown"
    return f"{(int(size_bytes) / (1024 * 1024)):.1f}MB"


def _fmt_duration_sec(seconds: Optional[float]) -> str:
    if seconds is None:
        return "unknown"
    try:
        return f"{int(round(float(seconds)))}s"
    except Exception:
        return "unknown"


def _safe_filename(name: str, default: str) -> str:
    raw = (name or "").strip()
    if not raw:
        return default
    raw = raw.replace("\\", "_").replace("/", "_").replace(":", "_")
    raw = raw.replace("*", "_").replace("?", "_").replace("\"", "_")
    raw = raw.replace("<", "_").replace(">", "_").replace("|", "_")
    raw = raw.replace("\n", " ").replace("\r", " ").strip()
    if len(raw) > 180:
        raw = raw[:180]
    return raw or default


def _resolution_to_wh(resolution: str) -> tuple[int, int]:
    r = (resolution or "1080p").lower().strip()
    if r == "720p":
        return 1280, 720
    if r == "4k":
        return 3840, 2160
    return 1920, 1080


def _npx_path() -> Optional[str]:
    # Windows: npx.cmd / npm.cmd
    for cand in ("npx.cmd", "npx"):
        p = shutil.which(cand)
        if p:
            return p
    return None


def _npm_path() -> Optional[str]:
    for cand in ("npm.cmd", "npm"):
        p = shutil.which(cand)
        if p:
            return p
    return None


async def _run_cmd(cmd: list[str], *, cwd: str, timeout_sec: int) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        out_b, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except Exception:
            pass
        return 124, "Timeout while rendering video."
    out = (out_b or b"").decode("utf-8", errors="ignore")
    return int(proc.returncode or 0), out


async def _ensure_node_deps(project_dir: str) -> tuple[bool, str]:
    """
    Optional bootstrap: if node_modules missing, return a helpful instruction message.
    We intentionally do NOT auto-install by default (security + reproducibility).
    """
    if os.path.isdir(os.path.join(project_dir, "node_modules")):
        return True, ""
    return False, (
        "Remotionの依存が未インストールです。\n"
        f"次を実行してください: `cd {project_dir}` → `npm ci` (または `npm install`)"
    )


def _build_result_lines(
    *,
    label: str,
    duration_sec: float,
    width: int,
    height: int,
    size_bytes: int,
    fmt: str,
    filename: str,
    link_url: Optional[str],
) -> list[str]:
    lines = [
        f"💾 **{label} created**",
        f"**Duration** {_fmt_duration_sec(duration_sec)}",
        f"**Resolution** {width}x{height}",
        f"**Size** {_fmt_size_mb(size_bytes)}",
        f"**Format** {fmt}",
        f"**File** `{filename}`",
    ]
    if link_url:
        lines.append(f"🔗 **30分限定DLページ** {link_url}")
    return lines


async def execute(args: dict, message: discord.Message, bot: Any = None) -> Any:
    preset = (args.get("preset") or "").strip()
    if preset not in {"title_card", "caption_image"}:
        return "❌ preset は title_card / caption_image のどちらかです。"

    duration_sec = float(args.get("duration_sec") or 6.0)
    if duration_sec <= 0:
        duration_sec = 6.0

    fps = int(args.get("fps") or 30)
    if fps <= 0 or fps > 120:
        fps = 30

    resolution = (args.get("resolution") or "1080p").strip().lower()
    width, height = _resolution_to_wh(resolution)

    output = (args.get("output") or "mp4").strip().lower()
    if output not in {"mp4", "webm", "gif"}:
        output = "mp4"

    # Remotion CLI codec mapping
    codec = "h264"
    if output == "webm":
        codec = "vp8"
    elif output == "gif":
        codec = "gif"

    project_dir = (os.getenv("ORA_REMOTION_PROJECT_DIR") or os.path.join("tools", "remotion")).strip()
    entry = (os.getenv("ORA_REMOTION_ENTRY") or os.path.join("src", "index.ts")).strip()
    timeout_sec = int(float(os.getenv("ORA_REMOTION_RENDER_TIMEOUT_SEC") or 900))

    if not os.path.isdir(project_dir):
        return f"❌ Remotion project not found: {project_dir}"

    npx = _npx_path()
    if not npx:
        return "❌ npx が見つかりません。Node.js をインストールしてください。"

    ok, msg = await _ensure_node_deps(project_dir)
    if not ok:
        return f"❌ {msg}"

    composition = "OraTitleCard" if preset == "title_card" else "OraCaptionImage"
    props: dict[str, Any] = {
        "preset": preset,
        "durationSec": duration_sec,
        "fps": fps,
    }

    if preset == "title_card":
        title = (args.get("title") or "").strip()
        subtitle = (args.get("subtitle") or "").strip()
        if not title:
            return "❌ title_card には title が必要です。"
        props["title"] = title[:300]
        props["subtitle"] = subtitle[:400]
    else:
        caption = (args.get("caption") or "").strip()
        image_url = (args.get("image_url") or "").strip()
        if not image_url:
            return "❌ caption_image には image_url が必要です。"
        props["caption"] = caption[:600]
        props["imageUrl"] = image_url[:2000]

    # Output locations: render to temp, then either upload or move to shared downloads.
    cfg = getattr(bot, "config", None) if bot else None
    base_temp = getattr(cfg, "temp_dir", None) or os.path.join(os.getcwd(), "data", "temp")
    os.makedirs(base_temp, exist_ok=True)

    default_name = f"ora_video_{uuid.uuid4().hex[:8]}.{output}"
    filename = _safe_filename(args.get("filename"), default_name)
    if not filename.lower().endswith(f".{output}"):
        filename = f"{filename}.{output}"

    with tempfile.TemporaryDirectory(prefix="remotion_", dir=base_temp) as tdir:
        props_path = os.path.join(tdir, "props.json")
        out_path = os.path.join(tdir, filename)

        with open(props_path, "w", encoding="utf-8") as f:
            json.dump(props, f, ensure_ascii=False, indent=2)

        # Remotion CLI (project-local)
        # npx remotion render <entry> <comp> <out> --props=<file> --codec=<codec> --width --height --overwrite
        cmd = [
            npx,
            "remotion",
            "render",
            entry,
            composition,
            out_path,
            f"--props={props_path}",
            f"--codec={codec}",
            f"--width={width}",
            f"--height={height}",
            "--overwrite",
        ]

        # Quality knobs (safe defaults)
        if codec == "h264":
            cmd += ["--crf=18", "--x264-preset=veryfast"]

        rc, out = await _run_cmd(cmd, cwd=project_dir, timeout_sec=timeout_sec)
        if rc != 0 or (not os.path.exists(out_path)):
            # Provide a short error (full logs are already in stdout).
            snippet = (out or "").strip().splitlines()[-25:]
            return "❌ Remotion render failed.\n" + "\n".join(snippet[-25:])

        size_bytes = int(os.path.getsize(out_path))
        label = "Video"
        limit_bytes = message.guild.filesize_limit if getattr(message, "guild", None) else 10 * 1024 * 1024
        safe_upload_limit = max(1, int(limit_bytes * 0.95))

        if size_bytes <= safe_upload_limit:
            lines = _build_result_lines(
                label=label,
                duration_sec=duration_sec,
                width=width,
                height=height,
                size_bytes=size_bytes,
                fmt=codec,
                filename=filename,
                link_url=None,
            )
            await message.reply(content="\n".join(lines), file=discord.File(out_path, filename=filename))
            return {
                "silent": True,
                "result": f"動画を生成してDiscordへ送信しました。{_fmt_duration_sec(duration_sec)} / {width}x{height} / {_fmt_size_mb(size_bytes)}",
                "video_meta": {
                    "duration_sec": duration_sec,
                    "width": width,
                    "height": height,
                    "size_bytes": size_bytes,
                    "codec": codec,
                    "filename": filename,
                },
            }

        # Too large -> temp download page (30 min) with auto cleanup.
        moved_path = os.path.join(tdir, filename)
        manifest = create_temporary_download(
            moved_path,
            download_name=filename,
            source_url="",
            metadata={
                "duration_sec": duration_sec,
                "width": width,
                "height": height,
                "codec": codec,
                "preset": preset,
            },
            ttl_seconds=1800,
        )
        base_url = await ensure_download_public_base_url(bot)
        dl_page_url = f"{base_url}/download/{manifest['token']}" if base_url else None

        lines = _build_result_lines(
            label=label,
            duration_sec=duration_sec,
            width=width,
            height=height,
            size_bytes=size_bytes,
            fmt=codec,
            filename=manifest.get("download_name") or filename,
            link_url=dl_page_url,
        )
        if not dl_page_url:
            lines.append("⚠️ DL公開URLを生成できませんでした。`cloudflared` と `logs/cf_download.log` を確認してください。")
        await message.reply(content="\n".join(lines))

        return {
            "silent": True,
            "result": f"動画を生成しましたがDiscord上限超過のため30分限定DLリンクを発行しました。{_fmt_size_mb(size_bytes)}",
            "video_meta": {
                "duration_sec": duration_sec,
                "width": width,
                "height": height,
                "size_bytes": size_bytes,
                "codec": codec,
                "download_page_url": dl_page_url or "",
                "filename": manifest.get("download_name") or filename,
            },
        }

