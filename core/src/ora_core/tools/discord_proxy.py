import logging
from typing import Dict, Any
from ..mcp.registry import tool_registry, ToolDefinition

logger = logging.getLogger(__name__)

async def discord_proxy_handler(args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generic handler that just wraps args into a client_action payload.
    The tool_name is retrieved from the registry when calling execute_handler eventually,
    but here we might need to know which tool it is.
    Actually, the ToolRunner knows the tool_name.
    """
    # Note: We don't have tool_name here easily unless we pass it in context.
    # But we can just use a specific handler per tool for clarity.
    return {
        "ok": True,
        "content": [{"type": "text", "text": "Dispatching action to Discord client..."}],
        "client_action": args # In this simple case, args ARE the action parameters
    }

def register_discord_proxies():
    # 1. music_play
    tool_registry.register_tool(
        ToolDefinition(
            name="music_play",
            description="Plays music from a URL or search query in the Discord voice channel.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "YouTube URL or search keywords"}
                },
                "required": ["query"]
            },
            allowed_clients=["discord"] # Restricted to Discord
        ),
        handler=discord_proxy_handler
    )

    # 2. music_control
    tool_registry.register_tool(
        ToolDefinition(
            name="music_control",
            description="Controls music playback (stop, skip, pause, resume).",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["stop", "skip", "pause", "resume", "queue"]}
                },
                "required": ["action"]
            },
            allowed_clients=["discord"]
        ),
        handler=discord_proxy_handler
    )
    
    # 3. manage_user_voice
    tool_registry.register_tool(
        ToolDefinition(
            name="manage_user_voice",
            description="Toggles voice output (TTS) for the user.",
            parameters={
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean"}
                },
                "required": ["enabled"]
            },
            allowed_clients=["discord"]
        ),
        handler=discord_proxy_handler
    )

    logger.info("Discord Proxy Tools registered in Core.")
