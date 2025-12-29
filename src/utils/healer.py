import logging
import traceback
import discord
import io
from typing import Optional
from .llm_client import LLMClient

logger = logging.getLogger(__name__)

class Healer:
    def __init__(self, bot, llm: LLMClient):
        self.bot = bot
        self.llm = llm

    async def handle_error(self, ctx, error: Exception):
        """
        Analyzes the error, sends report to Owner via DM, and proposes a fix.
        """
        # Target Owner ID (YoneRai12)
        OWNER_ID = 1069941291661672498
        
        # Get traceback
        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        logger.error(f"Healer caught error: {error}")

        # Context Info
        if hasattr(ctx, 'author'):
            invoker = f"{ctx.author} ({ctx.author.id})"
            command = str(ctx.command) if ctx.command else "Unknown"
        else:
            invoker = "System/Event"
            command = str(ctx) # ctx might be event name string

        # Ask LLM for analysis and patch
        try:
            prompt = f"""
            You are an expert Python debugger. The user wants you to AUTOMATICALLY FIX the error.
            
            Error: {str(error)}
            Traceback:
            {tb[-1500:]}
            
            Context: {invoker} invoked '{command}'.
            
            Task:
            1. Analyze the root cause.
            2. Determine the file closest to the error source (from the list below or traceback).
            3. Provide the CORRECTED full content of that file (or a specific function). 
               *Currently, stick to FULL FILE content for safety unless excessively large.*
            4. Verify the fix (explain logic).
            5. Output STRICT JSON format.
            
            Project Root: {os.getcwd()}
            
            Output JSON Schema:
            {{
                "analysis": "Cause explanation in Japanese",
                "verification": "Why it works in Japanese",
                "filepath": "Relative path to file (e.g., src/cogs/ora.py)",
                "new_content": "COMPLETE content of the file with fix applied"
            }}
            """
            
            # Use 'gpt-5.1-codex' formatted for JSON
            import json
            import os
            import shutil
            
            analysis_json = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}], 
                temperature=0.0,
                model="gpt-5.1-codex"
            )
            
            # Parse JSON
            # Codex might wrap in ```json ... ```
            cleaned_json = analysis_json.strip()
            if cleaned_json.startswith("```json"):
                cleaned_json = cleaned_json.replace("```json", "").replace("```", "")
            elif cleaned_json.startswith("```"):
                cleaned_json = cleaned_json.replace("```", "")
            
            data = json.loads(cleaned_json)
            
            # Actions
            filepath = data.get("filepath", "")
            new_content = data.get("new_content", "")
            verification_msg = data.get("verification", "")
            
            status_msg = "⚠️ Fix Not Applied (Parse/Path Error)"
            
            if filepath and os.path.exists(filepath) and new_content:
                # 1. Backup
                timestamp = int(time.time())
                backup_path = f"{filepath}.{timestamp}.bak"
                shutil.copy2(filepath, backup_path)
                
                # 2. Syntax Check
                try:
                    compile(new_content, filepath, 'exec')
                    
                    # 3. Apply
                    async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                        await f.write(new_content)
                    
                    status_msg = f"✅ Fix Applied! (Backup: `{os.path.basename(backup_path)}`)"
                    
                    # 4. Attempt Reload (if Cog)
                    # Simple heuristic: if in src/cogs/, reload extension
                    if "src/cogs/" in filepath.replace("\\", "/"):
                        ext_name = filepath.replace("\\", "/").replace("/", ".").replace(".py", "")
                        if ext_name.startswith("src."):
                            try:
                                await self.bot.reload_extension(ext_name)
                                status_msg += "\n🔄 Extension Reloaded."
                            except Exception as reload_err:
                                status_msg += f"\n⚠️ Reload Failed: {reload_err}"

                except SyntaxError as syn_err:
                    status_msg = f"⛔ Syntax Check Failed: {syn_err}"
            
            # Send Report
            # ... (Loop over targets) ...
            TARGET_IDS = [1069941291661672498, 1455097004433604860]
            for target_id in TARGET_IDS:
                try:
                    user = await self.bot.fetch_user(target_id)
                    if user:
                        embed = discord.Embed(title="🚑 Auto-Healer Action", color=discord.Color.green())
                        embed.add_field(name="Status", value=status_msg, inline=False)
                        embed.add_field(name="Cause", value=data.get("analysis", "N/A")[:1000], inline=False)
                        embed.add_field(name="Verification", value=verification_msg[:1000], inline=False)
                        embed.set_footer(text=f"Origin: {invoker}")
                        
                        await user.send(embed=embed)
                except Exception:
                    pass
            
            # Returning to avoid falling into old code block
            return

        except Exception as e:
            logger.error(f"Healer failed to Auto-Patch: {e}")
            
            # Send to Owners (DM)
            TARGET_IDS = [1069941291661672498, 1455097004433604860]
            
            for target_id in TARGET_IDS:
                try:
                    user = await self.bot.fetch_user(target_id)
                    if user:
                        embed = discord.Embed(title="🚑 Auto-Healer Report", color=discord.Color.red())
                        embed.description = f"**Error Event Detected**\n`{str(error)}`\n\n{analysis[:3500]}"
                        embed.set_footer(text=f"Source: {invoker}")
                        
                        await user.send(embed=embed)
                        logger.info(f"Sent Healer report to Target ({target_id})")
                except Exception as notify_err:
                    logger.error(f"Healer failed to DM target {target_id}: {notify_err}")

        except Exception as e:
            logger.error(f"Healer failed to analyze: {e}")

        except Exception as e:
            logger.error(f"Healer failed to analyze: {e}")

    async def propose_feature(self, feature: str, context: str, requester: discord.User):
        """
        AI Self-Evolution: Proposes code for a missing feature.
        """
        try:
            prompt = f"""
            You are an expert Discord Bot Architect.
            The user requested a feature that does not exist.
            
            Feature: {feature}
            Context: {context}
            Requester: {requester}
            
            Task:
            1. Design a new Discord Cog (Python) to implement this feature.
            2. The Cog should be standalone if possible, or simple modification instructions.
            3. Output STRICT JSON format.
            
            Output JSON Schema:
            {{
                "analysis": "Plan implementation in Japanese",
                "verification": "Logic verification in Japanese",
                "filename": "suggested_filename.py",
                "code": "COMPLETE Python code for the new Cog"
            }}
            """
            
            import json
            analysis_json = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}], 
                temperature=0.2,
                model="gpt-5.1-codex"
            )
            
            # Parse
            cleaned_json = analysis_json.strip()
            if cleaned_json.startswith("```json"):
                cleaned_json = cleaned_json.replace("```json", "").replace("```", "")
            elif cleaned_json.startswith("```"):
                cleaned_json = cleaned_json.replace("```", "")
                
            data = json.loads(cleaned_json)
            
            # Send Proposal to Admins
            TARGET_IDS = [1069941291661672498, 1455097004433604860]
            
            for target_id in TARGET_IDS:
                try:
                    user = await self.bot.fetch_user(target_id)
                    if user:
                        embed = discord.Embed(title="🧬 Auto-Evolution Proposal", color=discord.Color.blue())
                        embed.description = f"**Feature**: {feature}\n**Context**: {context}\n\n**Analysis**:\n{data.get('analysis')}\n\n**Verification**:\n{data.get('verification')}"
                        
                        # Attach code as file (too long for embed)
                        code = data.get("code", "# No code generated")
                        filename = data.get("filename", "feature.py")
                        file = discord.File(io.StringIO(code), filename=filename)
                        
                        embed.set_footer(text="Review the attached code. To apply, manually add to src/cogs/.")
                        await user.send(embed=embed, file=file)
                        
                except Exception as e:
                    logger.error(f"Failed to send Evolution Proposal to {target_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Self-Evolution failed: {e}")
