
import discord
from discord.ext import commands, tasks
import logging
import json
import os
import aiofiles
import time
import psutil
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

MEMORY_DIR = r"L:\ORA_Memory\users"

class MemoryCog(commands.Cog):

    def __init__(self, bot: commands.Bot, llm_client):
        self.bot = bot
        self._llm = llm_client
        self._ensure_memory_dir()
        
        # Buffer: {user_id: [{"content": str, "timestamp": str}, ...]}
        self.message_buffer: Dict[int, list] = {}
        
        # Start background worker
        self.memory_worker.start()

    def _ensure_memory_dir(self):
        """Ensure memory directory exists."""
        if not os.path.exists(MEMORY_DIR):
            try:
                os.makedirs(MEMORY_DIR, exist_ok=True)
                logger.info(f"Created Memory Directory: {MEMORY_DIR}")
            except Exception as e:
                logger.error(f"Failed to create Memory Directory: {e}")

    def cog_unload(self):
        self.memory_worker.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Buffer user messages for analysis."""
        if message.author.bot:
            return
            
        # Initialize buffer for user if needed
        if message.author.id not in self.message_buffer:
            self.message_buffer[message.author.id] = []
            
        # Append message (max 50 to prevent memory bloat)
        self.message_buffer[message.author.id].append({
            "content": message.content,
            "timestamp": datetime.now().isoformat(),
            "channel": message.channel.name if hasattr(message.channel, "name") else "DM"
        })
        
        # Cap buffer size
        if len(self.message_buffer[message.author.id]) > 50:
             self.message_buffer[message.author.id].pop(0)

    async def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Load user profile from disk."""
        path = os.path.join(MEMORY_DIR, f"{user_id}.json")
        if not os.path.exists(path):
            return {}
        
        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to load profile for {user_id}: {e}")
            return {}

    async def update_user_profile(self, user_id: int, data: Dict[str, Any]):
        """Update user profile."""
        path = os.path.join(MEMORY_DIR, f"{user_id}.json")
        
        # Load existing
        current = await self.get_user_profile(user_id)
        
        # Merge Lists (Traits)
        if "traits" in data and "traits" in current:
            current["traits"] = list(set(current["traits"] + data["traits"]))
        elif "traits" in data:
            current["traits"] = data["traits"]
            
        # Update Summary (Overwrite or Append - Strategy: Append recent notes)
        if "history_summary" in data:
            current["history_summary"] = data["history_summary"]

        current["last_updated"] = datetime.now().isoformat()
        current["name"] = data.get("name", current.get("name", "Unknown"))
        
        try:
            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(current, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Failed to save profile for {user_id}: {e}")

    async def _analyze_batch(self, user_id: int, messages: list[Dict[str, Any]]):
        """Analyze a batch of messages and update the user profile."""
        if not messages: return

        chat_log = "\n".join([f"[{m['timestamp']}] {m['content']}" for m in messages])
        
        prompt = [
            {"role": "system", "content": "You are a Psychologist AI. Analyze the user's chat logs and update their profile."},
            {"role": "user", "content": (
                f"Analyze the following chat logs for a Discord user.\n"
                f"Extract:\n"
                f"1. **Traits**: Personality traits (e.g., Cheerful, sarcastic, technical).\n"
                f"2. **Interests**: Topics they like.\n"
                f"3. **Summary**: A brief 3-line summary of recent context/behavior.\n\n"
                f"Chat Log:\n{chat_log}\n\n"
                f"Output strictly in JSON format:\n"
                f"{{ \"traits\": [\"t1\", \"t2\"], \"interests\": [\"i1\", \"i2\"], \"history_summary\": \"...\" }}"
            )}
        ]
        
        try:
            response_text = await self._llm.chat(prompt, temperature=0.3)
            # Basic cleanup using regex
            import re
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                
                user_obj = self.bot.get_user(user_id)
                data["name"] = user_obj.name if user_obj else "Unknown"
                
                await self.update_user_profile(user_id, data)
                logger.info(f"Memory: Updated profile for {user_id} ({len(messages)} messages)")
            else:
                logger.warning(f"Memory: Failed to parse JSON for {user_id}")
        except Exception as e:
            logger.error(f"Memory: Analysis failed for {user_id}: {e}")

    @tasks.loop(minutes=5)
    async def memory_worker(self):
        """Background task to analyze buffered messages (Real-time)."""
        # 1. Check System Load (Low Priority)
        try:
            if psutil.cpu_percent() > 60:
                logger.debug("MemoryWorker: CPU load high, skipping analysis cycle.")
                return
        except Exception:
            pass

        # 2. Identify Users to Analyze (Buffer > 5 messages)
        users_to_process = [uid for uid, msgs in self.message_buffer.items() if len(msgs) >= 5]
        
        if not users_to_process:
            return

        logger.info(f"MemoryWorker: Analyzing profiles for {len(users_to_process)} users...")

        for user_id in users_to_process:
            # Pop messages for processing
            msgs = self.message_buffer[user_id]
            self.message_buffer[user_id] = [] # Clear buffer
            await self._analyze_batch(user_id, msgs)

    # --- Automatic History Scanning (Retroactive) ---
    async def scan_history_task(self):
        """Scans recent channel history on startup/demand to build initial memory."""
        await self.bot.wait_until_ready()
        logger.info("MemoryScan: Waiting 1 min before starting auto-scan...")
        await asyncio.sleep(60) # Wait for bot to settle

        logger.info("MemoryScan: Starting Automatic History Analysis...")
        
        total_processed = 0
        
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                # Permission check
                if not channel.permissions_for(guild.me).read_messages:
                    continue
                
                # Scan last 50 messages
                try:
                    history = [m async for m in channel.history(limit=50)]
                    # Group by User
                    user_msgs = {}
                    for m in history:
                        if m.author.bot: continue
                        if m.author.id not in user_msgs: user_msgs[m.author.id] = []
                        
                        user_msgs[m.author.id].append({
                            "content": m.content,
                            "timestamp": m.created_at.isoformat(),
                            "channel": channel.name
                        })
                    
                    # Analyze
                    for uid, msgs in user_msgs.items():
                        # Only analyze if we have substantial data (>5 msgs)
                        if len(msgs) > 5:
                            await self._analyze_batch(uid, msgs)
                            total_processed += 1
                            await asyncio.sleep(2) # Prevent rate limits
                            
                except Exception as e:
                    logger.warning(f"MemoryScan: Error in {channel.name}: {e}")
                    
                await asyncio.sleep(1) # Yield per channel
        
        logger.info(f"MemoryScan: Complete. Processed {total_processed} batches.")

    @commands.command(name="sync_memory", hidden=True)
    @commands.is_owner()
    async def sync_memory(self, ctx, target_user: discord.User = None, limit: int = 100):
        """Manually trigger history scan for current channel."""
        await ctx.send(f"🧠 Scanning last {limit} messages for memory analysis...")
        
        try:
            history = [m async for m in ctx.channel.history(limit=limit)]
            target_msgs = []
            
            for m in history:
                if m.author.bot: continue
                if target_user and m.author.id != target_user.id: continue
                
                target_msgs.append({
                    "content": m.content,
                    "timestamp": m.created_at.isoformat(),
                    "channel": ctx.channel.name
                })
            
            # If no specific user, group by user
            if not target_user:
                await ctx.send("Please specify a user for safely syncing: `/sync_memory @User`")
                return

            await self._analyze_batch(target_user.id, target_msgs)
            await ctx.send(f"✅ Analyzed {len(target_msgs)} messages for {target_user.name}.")
            
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    @memory_worker.before_loop
    async def before_worker(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    llm = getattr(bot, "llm_client", None)
    if not llm:
        logger.warning("MemoryCog: LLM Client not found on bot. Analysis disabled.")
    
    cog = MemoryCog(bot, llm)
    await bot.add_cog(cog)
    # Start the retroactive scan task
    bot.loop.create_task(cog.scan_history_task())
