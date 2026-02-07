from __future__ import annotations

from src.utils.cloudflare_tunnel import (
    extract_latest_public_tunnel_url,
    extract_public_tunnel_urls,
)


def test_extract_ignores_api_endpoint() -> None:
    content = (
        'failed to request quick Tunnel: Post "https://api.trycloudflare.com/tunnel": '
        "context deadline exceeded"
    )
    assert extract_latest_public_tunnel_url(content) is None
    assert extract_public_tunnel_urls(content) == []


def test_extract_picks_public_url_over_api() -> None:
    content = "\n".join(
        [
            "Requesting new quick Tunnel on trycloudflare.com...",
            'failed to request quick Tunnel: Post "https://api.trycloudflare.com/tunnel": timeout',
            "Your quick Tunnel has been created! Visit it at:",
            "https://bunny-themes-produces-biol.trycloudflare.com",
        ]
    )
    assert (
        extract_latest_public_tunnel_url(content)
        == "https://bunny-themes-produces-biol.trycloudflare.com"
    )


def test_extract_cfargotunnel_public_url() -> None:
    url = "https://123e4567-e89b-12d3-a456-426614174000.cfargotunnel.com"
    content = f"public url: {url}\n"
    assert extract_latest_public_tunnel_url(content) == url

