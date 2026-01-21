import asyncio
import datetime
import json
import logging
import re
import secrets
from datetime import datetime as dt_class  # Avoid conflict
from typing import Any, Dict, List, Optional

import discord

from src.config import ROUTER_CONFIG
from src.utils.core_client import core_client
from src.utils.cost_manager import Usage

logger = logging.getLogger(__name__)


class ChatHandler:
    def __init__(self, cog):
        self.cog = cog
        self.bot = cog.bot
        logger.info("ChatHandler v3.9.1 (HOTFIXED) Initialized")

    async def handle_prompt(
        self,
        message: discord.Message,
        prompt: str,
        existing_status_msg: Optional[discord.Message] = None,
        is_voice: bool = False,
        force_dm: bool = False,
    ) -> None:
        """
        [Thin Client] Process a user message by delegating to ORA Core.
        Discord handles UI (Status, Voice, Embeds) while Core handles Brain.
        """
        from src.utils.ui import StatusManager, EmbedFactory

        # 1. Initialize StatusManager
        status_manager = StatusManager(message.channel, existing_message=existing_status_msg)
        await status_manager.start("📡 ORA Core Brain へ接続中...")

        # 2. Determine Context Binding
        kind = "channel"
        ext_id = f"{message.guild.id}:{message.channel.id}" if message.guild else f"dm:{message.author.id}"
        
        if not message.guild:
            kind = "dm"
        elif hasattr(message.channel, "parent_id") and message.channel.parent_id:
            kind = "thread"
            ext_id = f"{message.guild.id}:{message.channel.parent_id}:{message.channel.id}"

        context_binding = {
            "provider": "discord",
            "kind": kind,
            "external_id": ext_id
        }

        # 3. Call Core API
        try:
            # Prepare attachments
            attachments = []
            for att in message.attachments:
                attachments.append({"type": "image_url", "url": att.url})
            
            # Send Request (Initial Handshake)
            response = await core_client.send_message(
                content=prompt,
                provider_id=str(message.author.id),
                display_name=message.author.display_name,
                conversation_id=None, 
                idempotency_key=f"discord:{message.id}",
                context_binding=context_binding,
                attachments=attachments,
                stream=True # Use SSE stream
            )

            if "error" in response:
                await status_manager.finish()
                await message.reply(f"❌ Core API 接続エラー: {response['error']}")
                return

            run_id = response.get("run_id")
            await status_manager.update_current(f"🧠 Brain 思考中... (Run: {run_id[:8]})")

            # 4. SSE Event Loop (Reactive UI)
            full_content = ""
            last_status_update = 0
            
            async for event in core_client.stream_events(run_id):
                e_type = event.get("event")
                data = event.get("data", {})

                if e_type == "delta":
                    token = data.get("text", "")
                    full_content += token
                    # We don't edit Discord messages for every token (too many requests)
                
                elif e_type == "tool_start":
                    t_name = data.get("tool")
                    await status_manager.update_current(f"🛠️ ツール実行中: {t_name}...")
                
                elif e_type == "tool_result":
                    t_name = data.get("tool")
                    latency = data.get("latency_ms", 0)
                    logger.info(f"Tool {t_name} finished in {latency}ms")
                    await status_manager.update_current(f"✅ {t_name} 完了 ({latency}ms)")

                elif e_type == "dispatch":
                    # Brain requested an action from the Skin
                    action = data.get("action", {})
                    t_name = data.get("tool")
                    logger.info(f"🚀 Dispatching Skin Action: {t_name}")
                    
                    # Map to local executor
                    # We reuse _execute_tool for legacy compatibility, or call cogs directly.
                    # Since we want it 'thin', calling the legacy _execute_tool is the easiest bridge.
                    await self.cog._execute_tool(t_name, action, message, status_manager=status_manager)

                elif e_type == "final":
                    full_content = data.get("text", full_content)
                    break
                
                elif e_type == "error":
                    err = data.get("text", "Unknown Error")
                    await status_manager.finish()
                    await message.reply(f"❌ Brain 実行エラー: {err}")
                    return

            # 5. Final Output Handover
            await status_manager.finish()
            
            if not full_content:
                await message.reply("❌ 応答を生成できませんでした。")
                return

            # Send as Embed Cards
            # Split if > 4000 chars
            remaining = full_content
            while remaining:
                chunk = remaining[:4000]
                remaining = remaining[4000:]
                embed = EmbedFactory.create_chat_embed(chunk)
                await message.reply(embed=embed)
            
            # 6. Post-Process Actions (Voice, etc.)
            # Check if user is in VC and if we should speak
            if is_voice:
                await self.cog._voice_manager.play_tts(message.author, full_content)

        except Exception as e:
            logger.error(f"Core API Delegation Failed: {e}", exc_info=True)
            await status_manager.finish()
            await message.reply(f"システムエラー: {e}")

    # --- END OF THIN CLIENT ---
