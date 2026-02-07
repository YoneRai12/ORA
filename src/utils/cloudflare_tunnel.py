import os
import re
from typing import Optional

# Cloudflared quick tunnels write both:
# - Public URL: https://<random>.trycloudflare.com
# - API endpoint in error paths: https://api.trycloudflare.com/tunnel
# We must not treat the API endpoint as a public URL.
_PUBLIC_TUNNEL_URL_RE = re.compile(
    r"https://(?!api\.)[a-zA-Z0-9-]+\.(?:trycloudflare\.com|cfargotunnel\.com)"
)


def extract_public_tunnel_urls(text: str) -> list[str]:
    if not text:
        return []
    return _PUBLIC_TUNNEL_URL_RE.findall(text)


def extract_latest_public_tunnel_url(text: str) -> Optional[str]:
    urls = extract_public_tunnel_urls(text)
    if not urls:
        return None
    return urls[-1].rstrip("/")


def extract_latest_public_tunnel_url_from_log(log_path: str) -> Optional[str]:
    if not log_path or not os.path.exists(log_path):
        return None
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            return extract_latest_public_tunnel_url(f.read())
    except Exception:
        return None

