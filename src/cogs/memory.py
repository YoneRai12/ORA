
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
import ast # For robust JSON parsing fallback

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
            "id": message.id,
            "content": message.content,
            "timestamp": datetime.now().isoformat(),
            "channel": message.channel.name if hasattr(message.channel, "name") else "DM",
            "guild": message.guild.name if message.guild else "DM"
        })
        
        # Cap buffer size
        if len(self.message_buffer[message.author.id]) > 50:
             self.message_buffer[message.author.id].pop(0)

        # ---------------------------------------------------------
        # INSTANT NAME UPDATE (Fix for Dashboard "Unknown" Issue)
        # ---------------------------------------------------------
        # Check if we should update the name on disk immediately
        # (Only do this if profile is missing OR name is stale/unknown)
        # To avoid IO spam, checking in memory or checking file existence is needed.
        # Simple approach: If msg count is 1 (new session), ensure profile has name.
        if len(self.message_buffer[message.author.id]) == 1:
            try:
                # We do this asynchronously to not block
                asyncio.create_task(self._ensure_user_name(message.author))
            except Exception as e:
                logger.error(f"Failed to ensure username: {e}")

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

            return {}

    async def _ensure_user_name(self, user: discord.User | discord.Member):
        """Quickly ensure the user has a name in their profile (before optimization)."""
        uid = user.id
        path = os.path.join(MEMORY_DIR, f"{uid}.json")
        
        display_name = user.display_name
        
        # Check if exists
        try:
            if os.path.exists(path):
                async with aiofiles.open(path, "r", encoding="utf-8") as f:
                    data = json.loads(await f.read())
                
                # If name is missing or Unknown, update it
                if data.get("name") in [None, "Unknown", ""]:
                    data["name"] = display_name
                    # Save back
                    async with aiofiles.open(path, "w", encoding="utf-8") as f:
                        await f.write(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                # Create skeleton
                data = {
                    "discord_user_id": str(uid),
                    "name": display_name,
                    "created_at": time.time(),
                    "points": 0,
                    "traits": [],
                    "history_summary": "New user.",
                    "impression": "Newcomer", # Temporary Impression
                    "last_updated": datetime.now().isoformat()
                }
                async with aiofiles.open(path, "w", encoding="utf-8") as f:
                    await f.write(json.dumps(data, indent=2, ensure_ascii=False))
                    
        except Exception as e:
            logger.error(f"Error checking name for {uid}: {e}")

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

        if "impression" in data:
            current["impression"] = data["impression"]
            
        if "last_context" in data:
            current["last_context"] = data["last_context"]

        if "last_message_id" in data:
            # Ensure we don't regress if multiple batches run
            old_id = current.get("last_message_id", 0)
            new_id = data["last_message_id"]
            if new_id > old_id:
                current["last_message_id"] = new_id

        # Merge Status (Critical for Dashboard)
        if "status" in data:
            current["status"] = data["status"]

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
        
        last_msg_id = max([m.get("id", 0) for m in messages]) if messages else 0

        prompt = [
            {"role": "system", "content": "You are a Psychologist AI. Analyze the user's chat logs and update their profile. Output MUST be in Japanese."},
            {"role": "user", "content": (
                f"Analyze the following chat logs for a Discord user.\n"
                f"Extract:\n"
                f"1. **Traits**: Personality traits (e.g., 明るい, 皮肉屋, 技術オタク).\n"
                f"2. **Interests**: Topics they like.\n"
                f"3. **Summary**: A brief 3-line summary of recent context/behavior.\n"
                f"4. **Impression**: A single punchy phrase or word describing the user (e.g. '深夜のコーディング戦士', 'マイクラ中毒').\n\n"
                f"Chat Log:\n{chat_log}\n\n"
                f"Output strictly in JSON format (All values in Japanese):\n"
                f"{{ \"traits\": [\"t1\", \"t2\"], \"interests\": [\"i1\", \"i2\"], \"history_summary\": \"...\", \"impression\": \"...\" }}"
            )}
        ]
        
        # COST TRACKING PREP
        from src.utils.cost_manager import Usage
        import secrets
        
        cost_manager = None
        ora_cog = self.bot.get_cog("ORACog")
        if ora_cog:
            cost_manager = ora_cog.cost_manager

        est_usage = Usage(tokens_in=len(chat_log)//4 + 500, tokens_out=200, usd=0.0)
        rid = secrets.token_hex(4)

        try:
            response_text = ""
            actual_usage = None

            # Try APi (OpenAI) first as requested for optimization
            try:
                # MARK AS PENDING (Visual Feedback for Dashboard)
                # We update the profile to "Pending" so the user card turns Purple/Loading
                # and moves to the top of the list.
                try:
                    logger.info(f"Memory: Setting status to Pending for {user_id}...")
                    current_profile = await self.get_user_profile(user_id)
                    current_profile["status"] = "Pending"
                    await self.update_user_profile(user_id, current_profile)
                    logger.info(f"Memory: Successfully set Pending for {user_id}")
                except Exception as e_profile:
                    logger.warning(f"Memory: Failed to set Pending status: {e_profile}")

                # Assuming _llm is UnifiedClient
                if hasattr(self._llm, "openai_client") and self._llm.openai_client:
                     # Reserve
                     if cost_manager:
                         cost_manager.reserve("optimization", "openai", user_id, rid, est_usage)

                     # O1/GPT-5 models often don't support temperature or require default (1.0)
                     # Explicitly pass None to omit it from payload
                     response_text, _, usage_dict = await self._llm.chat("openai", prompt, temperature=None)
                     
                     if usage_dict:
                         u_in = usage_dict.get("prompt_tokens") or usage_dict.get("input_tokens", 0)
                         u_out = usage_dict.get("completion_tokens") or usage_dict.get("output_tokens", 0)
                         # Pricing (GPT-4o-mini approx): $0.15/1M in, $0.60/1M out
                         c_usd = (u_in * 0.00000015) + (u_out * 0.00000060)
                         
                         actual_usage = Usage(
                             tokens_in=u_in,
                             tokens_out=u_out,
                             usd=c_usd
                         )
                         logger.info(f"Memory: DEBUG OpenAI Usage -> In:{u_in} Out:{u_out} USD:{c_usd:.6f}")
                     else:
                         logger.warning("Memory: DEBUG OpenAI returned NO usage_dict")

                else:
                     raise RuntimeError("OpenAI disabled")
            except Exception as e:
                 logger.error(f"Memory: DEBUG OpenAI Failed: {e}")
                 # Fallback to Local
                 # Fallback to Local
                 # Ensure vLLM is running (Wake-on-Demand)
                 rm = self.bot.get_cog("ResourceManager")
                 if rm: await rm.ensure_vllm_started()

                 if hasattr(self._llm, "chat"):
                     # Check if UnifiedClient (requires provider arg) or LLMClient
                     # UnifiedClient.chat(provider, messages)
                     if hasattr(self._llm, "google_client"): # Fingerprint for UnifiedClient
                         # Local Tracking? (Lane=Private) - Maybe separate optimization usage for local too?
                         # For now, stick to openai tracking request.
                         response_text, _ = await self._llm.chat("local", prompt, temperature=0.3)
                     else:
                         response_text, _ = await self._llm.chat(prompt, temperature=0.3)

            # Commit Cost if OpenAI
            if cost_manager and actual_usage:
                res = cost_manager.commit("optimization", "openai", user_id, rid, actual_usage)
                logger.info(f"Memory: DEBUG Cost Committed. Total USD for this batch: {res}")
            elif not cost_manager:
                logger.warning("Memory: DEBUG CostManager NOT FOUND")
            elif not actual_usage:
                logger.warning("Memory: DEBUG Actual Usage NOT SET (OpenAI failed or fallback used)")


            # Basic cleanup using regex
            import re
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                # strict=False allows control characters like newlines in strings
                try:
                    data = json.loads(json_match.group(0), strict=False)
                except json.JSONDecodeError:
                    # Fallback for single quotes or loose JSON
                    try:
                        data = ast.literal_eval(json_match.group(0))
                    except Exception as e:
                        logger.error(f"Memory: JSON Parsing completely failed: {e}")
                        return
                
                user_obj = self.bot.get_user(user_id)
                data["name"] = user_obj.name if user_obj else "Unknown"
                
                # Attach Source Context
                data["last_context"] = messages
                data["last_message_id"] = last_msg_id
                
                # MARK AS OPTIMIZED (Important for Dashboard)
                data["status"] = "Optimized"

                await self.update_user_profile(user_id, data)
                logger.info(f"Memory: Updated profile for {user_id} ({len(messages)} messages)")
            else:
                logger.warning(f"Memory: Failed to parse JSON for {user_id}")
        except Exception as e:
            logger.error(f"Memory: Analysis failed for {user_id}: {e}")
            if cost_manager and actual_usage is None: # Rollback if reserve passed but execution failed
                 cost_manager.rollback("optimization", "openai", user_id, rid)

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
                            "id": m.id,
                            "content": m.content,
                            "timestamp": m.created_at.isoformat(),
                            "channel": channel.name,
                            "guild": channel.guild.name
                        })
                    
                    # Analyze
                    for uid, msgs in user_msgs.items():
                        # Check last_message_id from profile
                        profile = await self.get_user_profile(uid)
                        last_id = profile.get("last_message_id", 0)
                        
                        # Filter new messages
                        new_msgs = [msg for msg in msgs if msg["id"] > last_id]

                        # Only analyze if we have substantial data (>5 msgs)
                        if len(new_msgs) > 5:
                            await self._analyze_batch(uid, new_msgs)
                            total_processed += 1
                            await asyncio.sleep(2) # Prevent rate limits
                        else:
                            logger.debug(f"MemoryScan: {uid} - No new messages (Last: {last_id}, Newest: {msgs[-1]['id'] if msgs else 0})")
                            
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
                
                if target_user and m.author.id != target_user.id: continue
                
                target_msgs.append({
                    "id": m.id,
                    "content": m.content,
                    "timestamp": m.created_at.isoformat(),
                    "channel": ctx.channel.name,
                    "guild": ctx.guild.name if ctx.guild else "DM"
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
    # Try getting UnifiedClient first, then fallback to llm_client
    llm = getattr(bot, "unified_client", None) or getattr(bot, "llm_client", None)
    if not llm:
        logger.warning("MemoryCog: LLM Client not found on bot. Analysis disabled.")
    
    cog = MemoryCog(bot, llm)
    await bot.add_cog(cog)
    # Start the retroactive scan task
    bot.loop.create_task(cog.scan_history_task())
