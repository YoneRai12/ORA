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

    # 4. imagine (Proxy for Image Generation)
    tool_registry.register_tool(
        ToolDefinition(
            name="imagine",
            description="Generates an image using AI (Flux/ComfyUI). Output is displayed in Discord.",
            parameters={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Visual description of the image to generate."},
                    "aspect_ratio": {"type": "string", "enum": ["1:1", "16:9", "9:16"], "default": "1:1"}
                },
                "required": ["prompt"]
            },
            allowed_clients=["discord"]
        ),
        handler=discord_proxy_handler
    )

    # 5. layer (Proxy for Layer Decomposition)
    tool_registry.register_tool(
        ToolDefinition(
            name="layer",
            description="Processes the current vision/image and decomposes it into semantic layers.",
            parameters={
                "type": "object",
                "properties": {
                    "focus": {"type": "string", "description": "Optional focus area for decomposition."}
                }
            },
            allowed_clients=["discord"]
        ),
        handler=discord_proxy_handler
    )

    # 6. summarize (Proxy for Chat Summary)
    tool_registry.register_tool(
        ToolDefinition(
            name="summarize",
            description="Summarizes the recent chat history specifically for the current context.",
            parameters={
                "type": "object",
                "properties": {
                    "style": {"type": "string", "enum": ["brief", "detailed", "bullet"], "default": "brief"}
                }
            },
            allowed_clients=["discord"]
        ),
        handler=discord_proxy_handler
    )

    # 7. tts_speak (Proxy for High-Quality TTS)
    tool_registry.register_tool(
        ToolDefinition(
            name="tts_speak",
            description="Speaks the given text using high-quality neural voice synthesis in the voice channel.",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The text to speak."}
                },
                "required": ["text"]
            },
            allowed_clients=["discord"]
        ),
        handler=discord_proxy_handler
    )

    # 8. join_voice_channel
    tool_registry.register_tool(
        ToolDefinition(
            name="join_voice_channel",
            description="Joins the voice channel that the user is currently in.",
            parameters={"type": "object", "properties": {}, "required": []},
            allowed_clients=["discord"]
        ),
        handler=discord_proxy_handler
    )

    # 9. leave_voice_channel
    tool_registry.register_tool(
        ToolDefinition(
            name="leave_voice_channel",
            description="Leaves the currently connected voice channel.",
            parameters={"type": "object", "properties": {}, "required": []},
            allowed_clients=["discord"]
        ),
        handler=discord_proxy_handler
    )

    # 10. manage_user_role
    tool_registry.register_tool(
        ToolDefinition(
            name="manage_user_role",
            description="Adds or removes a role for a specific user.",
            parameters={
                "type": "object",
                "properties": {
                    "user_query": {"type": "string", "description": "The user ID, mention, or name."},
                    "role_query": {"type": "string", "description": "The role ID, mention, or name."},
                    "action": {"type": "string", "enum": ["add", "remove"], "description": "Action to perform."}
                },
                "required": ["user_query", "role_query", "action"]
            },
            allowed_clients=["discord"]
        ),
        handler=discord_proxy_handler
    )

    # 11. get_role_list
    tool_registry.register_tool(
        ToolDefinition(
            name="get_role_list",
            description="Returns a list of roles in the server, sorted by hierarchy (position). Useful for checking role priority.",
            parameters={"type": "object", "properties": {}, "required": []},
            allowed_clients=["discord"]
        ),
        handler=discord_proxy_handler
    )

    # 12. create_channel
    tool_registry.register_tool(
        ToolDefinition(
            name="create_channel",
            description="Creates a new channel (Text or Voice) in the server.",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the channel."},
                    "channel_type": {"type": "string", "enum": ["text", "voice"], "description": "Type of channel."},
                    "private": {"type": "boolean", "description": "If true, only allows the requester and mentioned users to view/connect."},
                    "users_to_add": {"type": "string", "description": "Optional space-separated list of users/roles to allow (mentions/IDs)."}
                },
                "required": ["name", "channel_type"]
            },
            allowed_clients=["discord"]
        ),
        handler=discord_proxy_handler
    )

    logger.info("Discord Proxy Tools registered in Core.")
