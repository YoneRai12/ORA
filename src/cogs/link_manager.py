import discord
from discord import app_commands
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class LinkManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sent_on_startup = False
        self._last_admin_dm_ts: float = 0.0

    async def _get_tunnel_url(self, service_name: str, fallback: str) -> str:
        """Extracts the latest Quick Tunnel URL from the service's log file with retries."""
        import os
        import re
        import asyncio
        
        cfg = self.bot.config
        log_dir = cfg.log_dir
        log_path = os.path.join(log_dir, f"cf_{service_name}.log")

        # Support both modern and older domains.
        url_re = re.compile(
            r"https://[a-zA-Z0-9-]+\.(?:trycloudflare\.com|cfargotunnel\.com)"
        )
        
        # Cloudflare might take a few seconds to write the URL
        for attempt in range(3):
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        # Find the most recent URL in the log
                        matches = url_re.findall(content)
                        if matches:
                            url = matches[-1]
                            logger.info(f"✅ Extracted Cloudflare URL for {service_name}: {url}")
                            return url
                except Exception as e:
                    logger.error(f"Failed to parse tunnel log for {service_name}: {e}")
            
            if attempt < 2:
                logger.info(f"⏳ Waiting for Cloudflare URL in {log_path} (Attempt {attempt+1}/3)...")
                await asyncio.sleep(5)
        
        return fallback

    async def _dm_admin_links(self, link_map: dict[int, dict], *, reason: str) -> None:
        """
        Best-effort: DM admin a stable place to find the latest external links.
        This avoids "URL didn't post to channel so I can't access from outside".
        """
        import time

        cfg = self.bot.config
        admin_id = getattr(cfg, "admin_user_id", None)
        if not admin_id:
            return

        # Avoid DM spam unless explicitly triggered.
        now = time.time()
        if reason == "startup" and (now - self._last_admin_dm_ts) < 600:
            return

        urls: list[str] = []
        for _, data in link_map.items():
            url = (data or {}).get("url")
            title = (data or {}).get("title")
            if url:
                urls.append(f"- {title}: {url}")

        if not urls:
            urls.append("- (no public URLs found yet)")

        text = (
            "**ORA Public Links**\n"
            f"reason={reason}\n"
            + "\n".join(urls)
            + "\n\nIf links are missing: check Cloudflare logs under `ORA_LOG_DIR` (cf_*.log) and tunnel settings."
        )

        try:
            user = self.bot.get_user(admin_id) or await self.bot.fetch_user(admin_id)
            await user.send(text)
            self._last_admin_dm_ts = now
        except Exception:
            # Some users block DMs; don't hard-fail startup.
            logger.warning("Failed to DM admin public links (admin_user_id=%s)", admin_id)

    async def _persist_links(self, link_map: dict[int, dict]) -> None:
        """Write latest link map to state dir for local recovery/debug."""
        import json
        import os

        cfg = self.bot.config
        state_dir = getattr(cfg, "state_dir", None) or os.path.join(os.getcwd(), "data", "state")
        try:
            os.makedirs(state_dir, exist_ok=True)
            out_path = os.path.join(state_dir, "public_links.json")
            # Keep only the URL-ish payload.
            payload = {
                str(ch_id): {"title": v.get("title"), "url": v.get("url"), "desc": v.get("desc")}
                for ch_id, v in (link_map or {}).items()
                if isinstance(v, dict)
            }
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.debug("Failed to persist public links: %s", e)

    async def get_link_map(self):
        """Dynamic link map using latest Cloudflare URLs and Config."""
        cfg = self.bot.config
        
        # 1. Cloudflare Dynamic Bases
        # Dashboard (3333) proxies docs, api, etc.
        dash_cf = await self._get_tunnel_url("dash", cfg.public_base_url or "http://localhost:3333")
        
        # Web Chat is on 3000 (now 'ora-chat') -> cf_chat.log
        # Note: 'ora-main' is Named Tunnel for 8000 (Web Control)
        chat_cf = await self._get_tunnel_url("chat", "http://localhost:3000")
        
        # ComfyUI is on 8188 -> cf_comfy.log
        comfy_cf = await self._get_tunnel_url("comfy", "http://localhost:8188")
        
        # 2. Meteor (Strictly for Web Control only)
        # This is served by 'ora-main' Named Tunnel
        if cfg.tunnel_hostname:
            meteor_base = f"https://{cfg.tunnel_hostname.strip()}"
        else:
            meteor_base = dash_cf

        mapping = {}
        
        # --- LINK CHANNELS (With URLs) ---
        
        # 1. ORA 管理ダッシュボード (1454335076048568401)
        if cfg.startup_notify_channel_id:
            mapping[cfg.startup_notify_channel_id] = {
                "title": "🚀 ORA 管理ダッシュボード",
                "url": f"{dash_cf}/dashboard",
                "desc": "コスト追跡、ユーザープロファイル、およびシステムステータスのリアルタイム表示。",
                "color": discord.Color.blue()
            }
            
        # 2. ORA API ダッシュボード (1467111844178169999)
        if cfg.config_ui_notify_id:
            mapping[cfg.config_ui_notify_id] = {
                "title": "🚀 ORA API ダッシュボード",
                "url": f"{dash_cf}/dashboard",
                "desc": "システム全体のAPI利用状況および管理インターフェース。",
                "color": discord.Color.green()
            }
            
        # 3. ORA WEB チャット (1463508481763180751)
        if cfg.web_chat_notify_id:
            mapping[cfg.web_chat_notify_id] = {
                "title": "🛡️ ORA WEB チャット",
                "url": f"{chat_cf}/", 
                "desc": "ORAとの対話用ダイレクトWebインターフェース。",
                "color": discord.Color.gold()
            }
            
        # 4. ORA WEB Control Sandbox (1467163318845440062)
        # METEOR DOMAIN STRICTLY HERE (Named Tunnel)
        if cfg.ora_web_notify_id:
            mapping[cfg.ora_web_notify_id] = {
                "title": "🛡️ ORA WEB Control Sandbox",
                "url": f"{meteor_base}/static/operator.html",
                "desc": "ブラウジングおよびリモート操作用のサンドボックス環境。",
                "color": discord.Color.purple()
            }
            
        # 5. ORA API 管理パネル (Swagger) (1463508972974903306)
        if cfg.ora_api_notify_id:
            mapping[cfg.ora_api_notify_id] = {
                "title": "🛡️ ORA API 管理パネル",
                "url": f"{dash_cf}/docs",
                "desc": "インタラクティブなAPIドキュメントおよびテストインターフェース (Swagger UI)。",
                "color": discord.Color.teal()
            }
            
        # 6. ORA ComfyUI (1467112543486214165)
        if cfg.config_page_notify_id:
            mapping[cfg.config_page_notify_id] = {
                "title": "🎨 ORA ComfyUI",
                "url": f"{comfy_cf}/",
                "desc": "画像・動画生成用のノードベースUI環境。",
                "color": discord.Color.orange()
            }

        # --- STATUS ONLY CHANNELS ---
        
        # 7. Self-Evolution System (1459561969261744270)
        if cfg.feature_proposal_channel_id:
            mapping[cfg.feature_proposal_channel_id] = {
                "title": "🛡️ Self-Evolution System",
                "url": None, # NO LINK
                "desc": "自己進化機能は正常に稼働中です。",
                "color": discord.Color.magenta()
            }
            
        # 8. System Activity Logs (1455097004433604860)
        if cfg.log_channel_id:
            mapping[cfg.log_channel_id] = {
                "title": "🛡️ System Activity Logs",
                "url": None, # NO LINK
                "desc": "システムログの監視を開始しました。",
                "color": discord.Color.dark_grey()
            }

        return mapping

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.sent_on_startup:
            # Wait longer for tunnels to stabilize and write logs
            import asyncio
            # Tunnels start with 5s gap x 4 = 20s minimum. Give 40s buffer.
            await asyncio.sleep(40)
            logger.info("🚀 Broadcasting dynamic system links and status to active channels...")
            await self._broadcast_links()
            self.sent_on_startup = True

    @app_commands.command(name="broadcast_system_links", description="Broadcasts system URLs to their respective channels.")
    @app_commands.checks.has_permissions(administrator=True)
    async def broadcast_system_links(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        results = await self._broadcast_links()
        await interaction.followup.send("Broadcast Complete:\n" + "\n".join(results))

    @app_commands.command(name="links", description="Show current system links (Quick Tunnel / Named Tunnel).")
    async def links(self, interaction: discord.Interaction):
        """Ephemeral: show the latest link map for quick copy/paste."""
        await interaction.response.defer(ephemeral=True)
        link_map = await self.get_link_map()
        lines = []
        for _, data in link_map.items():
            url = (data or {}).get("url")
            title = (data or {}).get("title")
            if url:
                lines.append(f"- {title}: {url}")
        if not lines:
            lines = ["- (no public URLs found yet)"]
        await interaction.followup.send("\n".join(lines), ephemeral=True)

    async def _broadcast_links(self):
        results = []
        # MUST AWAIT NOW
        link_map = await self.get_link_map()

        await self._persist_links(link_map)
        
        for channel_id, data in link_map.items():
            channel = self.bot.get_channel(channel_id)
            if not channel:
                try:
                    channel = await self.bot.fetch_channel(channel_id)
                except Exception as e:
                    results.append(f"❌ Channel {channel_id}: Error {e}")
                    continue

            if hasattr(channel, 'send'):
                try:
                    title = data["title"]
                    url = data["url"]
                    desc = data["desc"]
                    color = data["color"]
                    
                    embed = discord.Embed(
                        title=title,
                        description=desc,
                        color=color
                    )
                    
                    if url:
                        embed.url = url
                        embed.add_field(name="アクセスURL", value=f"[ここをクリックして開く]({url})", inline=False)
                    else:
                        embed.set_footer(text="System Online • Monitoring Active")

                    await channel.send(embed=embed)
                    results.append(f"✅ Sent to {channel.name} ({channel_id})")
                except Exception as e:
                    results.append(f"❌ Failed to send to {channel.name}: {e}")
            else:
                 results.append(f"⚠️ Channel {channel_id} is not a text channel")

        # Reliable out-of-band delivery: DM admin.
        try:
            await self._dm_admin_links(link_map, reason="startup" if not self.sent_on_startup else "manual")
        except Exception:
            pass
        return results

async def setup(bot: commands.Bot):
    await bot.add_cog(LinkManager(bot))
