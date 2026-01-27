
import asyncio
import logging
from datetime import datetime

import pytz
from discord.ext import commands, tasks

logger = logging.getLogger(__name__)

class ProactiveCog(commands.Cog):
    """
    [Clawdbot Feature] Proactive Agent
    Initiates conversations based on schedule or inactivity.
    """
    def __init__(self, bot):
        self.bot = bot
        self.daily_briefing_task.start()
        # self.inactivity_check.start() # Disabled by default to avoid annoyance
        logger.info("ProactiveCog Initialized")

    def cog_unload(self):
        self.daily_briefing_task.cancel()
        # self.inactivity_check.cancel()

    @tasks.loop(minutes=1)
    async def daily_briefing_task(self):
        """Sends daily briefing at 08:00 AM JST."""
        now = datetime.now(pytz.timezone("Asia/Tokyo"))
        
        # Check if it's exactly 08:00
        if now.hour == 8 and now.minute == 0:
            logger.info("⏰ Triggering Daily Briefing...")
            
            # Target Channel: 1386994311400521768 (General/News)
            target_channel_id = 1386994311400521768
            channel = self.bot.get_channel(target_channel_id)
            
            if channel:
                try:
                    # 1. Search for News (if SearchClient available)
                    news_context = ""
                    if hasattr(self.bot, "search_client") and self.bot.search_client:
                        # Search for harmless tech news
                        results = await self.bot.search_client.search("latest technology news x.com twitter.com -R18 -nsfw", safe_search=True)
                        if results:
                            # Format top 3
                            links = [f"- {r['title']}: {r['link']}" for r in results[:3]]
                            news_context = "\n".join(links)
                    
                    # 2. Generate Briefing
                    if hasattr(self.bot, "llm_client"):
                        system_prompt = (
                            "You are ORA, a helpful community assistant. "
                            "Provide a cheerful morning briefing for the server.\n"
                            "Requirements:\n"
                            "1. Include Tokyo Weather.\n"
                            "2. Summarize 1-2 interesting Tech News headlines.\n"
                            "3. Include relevant X (Twitter) links if available in context.\n"
                            "4. STRICT SAFETY: NO R18/NSFW content allowed.\n"
                            "5. Tone: Friendly, engaging, safe for work."
                        )
                        
                        user_prompt = f"Context from Search:\n{news_context}\n\nStart the briefing."

                        response = await self.bot.llm_client.chat(
                            model=self.bot.config.LLM_MODEL,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            stream=False
                        )
                        
                        if response:
                            await channel.send(f"🌅 **Good Morning!**\n{response}")
                            logger.info(f"Sent daily briefing to {channel.name}")

                except Exception as e:
                    logger.error(f"Failed to send briefing: {e}")
            
            # Sleep to avoid double triggering (loop is 1 min)
            await asyncio.sleep(61)

    @daily_briefing_task.before_loop
    async def before_briefing(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(ProactiveCog(bot))
