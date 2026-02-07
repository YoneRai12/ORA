import argparse
import os
import sys
import time
from pathlib import Path


def _now() -> int:
    return int(time.time())


def _iter_files(root: Path):
    if not root.exists():
        return
    for p in root.rglob("*"):
        if p.is_file():
            yield p


def _safe_unlink(p: Path, *, apply: bool) -> int:
    try:
        sz = p.stat().st_size
    except Exception:
        sz = 0
    if apply:
        try:
            p.unlink(missing_ok=True)  # py>=3.8
        except TypeError:
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                return 0
        except Exception:
            return 0
    return int(sz)


def clean_repo_temp(*, repo_root: Path, apply: bool, older_than_sec: int = 0) -> int:
    """
    Cleans ./temp in the repo. Historically yt-dlp wrote here and could fill C:\\.
    """
    temp_dir = repo_root / "temp"
    if not temp_dir.exists():
        return 0
    freed = 0
    cutoff = _now() - max(0, int(older_than_sec))
    for f in _iter_files(temp_dir):
        try:
            if older_than_sec > 0 and int(f.stat().st_mtime) > cutoff:
                continue
        except Exception:
            pass
        freed += _safe_unlink(f, apply=apply)
    return freed


def clean_ora_ytdlp_temp(*, apply: bool, older_than_sec: int = 24 * 3600) -> int:
    """
    Cleans ORA temp yt-dlp artifacts: <ORA_TEMP_DIR>/yt_dlp.
    Only removes files older than a threshold (default 24h) to reduce risk.
    """
    try:
        from src.config import TEMP_DIR  # respects ORA_TEMP_DIR/ORA_DATA_ROOT
        base = Path(TEMP_DIR)
    except Exception:
        base = Path.cwd() / "data" / "temp"
    ytdlp = base / "yt_dlp"
    if not ytdlp.exists():
        return 0

    freed = 0
    cutoff = _now() - max(0, int(older_than_sec))
    for f in _iter_files(ytdlp):
        try:
            if int(f.stat().st_mtime) > cutoff:
                continue
        except Exception:
            pass
        freed += _safe_unlink(f, apply=apply)
    return freed


def clean_expired_shared_downloads(*, apply: bool) -> int:
    """
    Deletes expired token directories in shared_downloads (30min DL pages).
    """
    try:
        from src.utils.temp_downloads import cleanup_expired_downloads
    except Exception:
        return 0
    if not apply:
        # We can't easily compute bytes without scanning; just run logic-only dry-run is no-op.
        return 0
    try:
        return int(cleanup_expired_downloads())
    except Exception:
        return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Actually delete files (default: dry run)")
    ap.add_argument("--repo-root", default=str(Path.cwd()), help="Repo root")
    ap.add_argument("--repo-temp-older-sec", type=int, default=0, help="Only delete repo temp files older than N seconds (0=all)")
    ap.add_argument("--ytdlp-older-sec", type=int, default=24 * 3600, help="Only delete yt_dlp temp files older than N seconds")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    apply = bool(args.apply)

    freed_repo = clean_repo_temp(repo_root=repo_root, apply=apply, older_than_sec=int(args.repo_temp_older_sec))
    freed_ytdlp = clean_ora_ytdlp_temp(apply=apply, older_than_sec=int(args.ytdlp_older_sec))

    cleaned_tokens = clean_expired_shared_downloads(apply=apply)

    mb = lambda b: round(b / (1024 * 1024), 2)
    mode = "APPLY" if apply else "DRY_RUN"
    print(f"[{mode}] repo/temp freed ~{mb(freed_repo)} MB")
    print(f"[{mode}] ORA yt_dlp temp freed ~{mb(freed_ytdlp)} MB")
    if apply:
        print(f"[{mode}] expired shared_downloads entries removed: {cleaned_tokens}")
    else:
        print(f"[{mode}] expired shared_downloads: skipped (dry-run)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

