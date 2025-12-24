import discord
from discord.ext import commands
import asyncio
import subprocess
import socket
import os
import time

class ResourceManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vllm_port = 8001
        self.host = "127.0.0.1"
        self.vllm_process = None
        self.is_starting_vllm = False
        self._lock = asyncio.Lock()

    def is_port_open(self, host, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                return s.connect_ex((host, port)) == 0
        except:
            return False

    async def ensure_vllm_started(self):
        """Checks if vLLM is running. If not, starts it."""
        async with self._lock:
            # 1. Fast Check
            if self.is_port_open(self.host, self.vllm_port):
                return True

            # 2. Prevent Double Start
            if self.is_starting_vllm:
                print("[ResourceManager] vLLM is already starting... waiting.")
                for _ in range(60):
                    if self.is_port_open(self.host, self.vllm_port):
                        return True
                    await asyncio.sleep(1)
                return False

            self.is_starting_vllm = True
            print("[ResourceManager] vLLM Server is DOWN. Igniting engines...")
            
            # 3. Notify Discord (Optional/Visual)
            # await self._notify_channel("🔥 AIサーバーを起動しています... (最大2分)")

            try:
                # 4. Launch Service (Gaming Mode by Default)
                # Use 'start' to detach properly on Windows
                bat_path = os.path.abspath("start_vllm_gaming.bat")
                if not os.path.exists(bat_path):
                    print(f"[ResourceManager] Critical: {bat_path} not found!")
                    self.is_starting_vllm = False
                    return False

                # Detached launch
                subprocess.Popen(["start", "cmd", "/c", bat_path], shell=True)

                # 5. Wait for Port
                print("[ResourceManager] Waiting for vLLM Port 8001...")
                for i in range(120): # 2 mins max
                    if i % 10 == 0:
                        print(f"[ResourceManager] ... {i}s")
                    
                    if self.is_port_open(self.host, self.vllm_port):
                        print("[ResourceManager] vLLM is READY! Connection established.")
                        self.is_starting_vllm = False
                        return True
                    
                    await asyncio.sleep(1)
                
                print("[ResourceManager] Timeout: vLLM failed to open port.")
                self.is_starting_vllm = False
                return False

            except Exception as e:
                print(f"[ResourceManager] Error starting vLLM: {e}")
                self.is_starting_vllm = False
                return False

    async def _notify_channel(self, message):
        # Notify the default debug channel if possible, or all active channels
        # This is tricky without context. For now, we rely on logs/status.
        pass

async def setup(bot):
    await bot.add_cog(ResourceManager(bot))
