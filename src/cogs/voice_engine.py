import io
import logging

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger("VoiceEngineCog")


class VoiceEngine(commands.GroupCog, name="voice"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.speak_url = "http://127.0.0.1:8002/speak"
        self.clone_url = "http://127.0.0.1:8002/clone_speaker"
        super().__init__()

    @app_commands.command(name="status", description="[DEBUG] Check Voice Engine (Aratako TTS) Status")
    async def voice_status(self, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            try:
                # Assuming /docs exists on FastAPI
                async with session.get("http://127.0.0.1:8002/docs") as resp:
                    if resp.status == 200:
                        await interaction.response.send_message("✅ Voice Engine (Aratako TTS) is ONLINE.")
                    else:
                        await interaction.response.send_message(f"⚠️ Voice Engine returned {resp.status}.")
            except Exception as e:
                await interaction.response.send_message(f"❌ Voice Engine Offline: {e}")

    @app_commands.command(name="clone", description="Register your voice for Doppelganger Mode.")
    @app_commands.describe(sample="Upload a clear audio sample (10s+) of your voice.")
    async def voice_clone(self, interaction: discord.Interaction, sample: discord.Attachment):
        if not sample.content_type.startswith("audio/"):
            await interaction.response.send_message("❌ Audio file required.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        async with aiohttp.ClientSession() as session:
            audio_data = await sample.read()
            data = aiohttp.FormData()
            data.add_field("user_id", str(interaction.user.id))
            data.add_field("audio", audio_data, filename=sample.filename)

            async with session.post(self.clone_url, data=data) as resp:
                if resp.status == 200:
                    await interaction.followup.send(
                        f"✅ Voice Registered! ORA can now speak as {interaction.user.display_name}."
                    )
                else:
                    await interaction.followup.send(f"❌ Registration Failed: {resp.status}")

    async def generate_speech(self, text: str, user_id: str = None) -> io.BytesIO:
        """
        Internal API for ORA Brain to speak.
        If user_id is provided, it attempts to use the cloned voice.
        """
        async with aiohttp.ClientSession() as session:
            data = {"text": text}
            if user_id:
                data["speaker_id"] = str(user_id)

            async with session.post(self.speak_url, data=data) as resp:
                if resp.status == 200:
                    audio_bytes = await resp.read()
                    return io.BytesIO(audio_bytes)
                else:
                    logger.error(f"TTS Failed: {resp.status}")
                    return io.BytesIO(b"")
        return io.BytesIO(b"")

    @app_commands.command(name="list", description="List available VoiceVox speakers.")
    async def voice_list(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        # Access VoiceManager from bot
        vm = getattr(self.bot, "voice_manager", None)
        if not vm:
            await interaction.followup.send("❌ VoiceManager not initialized.")
            return

        speakers = await vm.get_speakers()
        if not speakers:
            await interaction.followup.send("❌ No speakers found or VoiceVox is offline.")
            return

        # Format output
        # VoiceVox structure: [{'name': '四国めたん', 'styles': [{'id': 2, 'name': 'ノーマル'}, ...], 'speaker_uuid': '...'}]
        embed = discord.Embed(title="🎙️ Available Voices (VoiceVox)", color=discord.Color.blue())

        # Group by name to keep it clean
        description = ""
        for sp in speakers:
            name = sp.get("name", "Unknown")
            styles = sp.get("styles", [])
            style_str = " / ".join([f"{s['name']}(**{s['id']}**)" for s in styles])
            
            line = f"**{name}**: {style_str}\n"
            if len(description) + len(line) > 4000:
                description += "...(truncated)"
                break
            description += line

        # Add T5Gemma info
        description = "**Virtual (High Quality)**:\nExample: T5Gemma (ID: **-1**)\n\n" + description

        embed.description = description
        embed.set_footer(text="Use /voice set <id> to change your voice.")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="set", description="Set your TTS voice (Speaker ID).")
    @app_commands.describe(speaker_id="The ID of the speaker style (e.g., 3 for Zundamon Normal, -1 for T5Gemma)")
    async def voice_set(self, interaction: discord.Interaction, speaker_id: int):
        vm = getattr(self.bot, "voice_manager", None)
        if not vm:
            await interaction.response.send_message("❌ VoiceManager not initialized.", ephemeral=True)
            return

        # If ID is -1, it's T5Gemma (Virtual)
        name = "Unknown"
        if speaker_id == -1:
            name = "T5Gemma (High Quality)"
        else:
            # Verify ID exists (optional but good UX)
            speakers = await vm.get_speakers()
            found = False
            for sp in speakers:
                for s in sp.get("styles", []):
                    if s["id"] == speaker_id:
                        name = f"{sp['name']} ({s['name']})"
                        found = True
                        break
                if found:
                    break
            
            if not found:
                await interaction.response.send_message(f"⚠️ Warning: Speaker ID {speaker_id} not found in current list, but setting anyway.", ephemeral=True)

        vm.set_user_speaker(interaction.user.id, speaker_id)
        await interaction.response.send_message(f"✅ Voice set to **{name}** (ID: {speaker_id})", ephemeral=True)

    @app_commands.command(name="me", description="Check your current TTS voice.")
    async def voice_me(self, interaction: discord.Interaction):
        vm = getattr(self.bot, "voice_manager", None)
        if not vm:
            await interaction.response.send_message("❌ VoiceManager not initialized.", ephemeral=True)
            return

        speaker_id = vm._user_speakers.get(interaction.user.id)
        if speaker_id is None:
             # Check guild default or system default
             guild_speaker = vm._guild_speakers.get(interaction.guild.id) if interaction.guild else None
             if guild_speaker is not None:
                 speaker_id = guild_speaker
                 source = "Guild Default"
             else:
                 speaker_id = "(Default)"
                 source = "System Default"
        else:
            source = "User Preference"

        # Resolve Name
        name_str = str(speaker_id)
        if speaker_id == -1:
            name_str = "T5Gemma (High Quality)"
        elif isinstance(speaker_id, int):
             speakers = await vm.get_speakers()
             for sp in speakers:
                for s in sp.get("styles", []):
                    if s["id"] == speaker_id:
                        name_str = f"{sp['name']} ({s['name']}) [ID: {speaker_id}]"
                        break
        
        await interaction.response.send_message(f"👤 **Current Voice**: {name_str}\nrunning on: **{source}**", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceEngine(bot))
