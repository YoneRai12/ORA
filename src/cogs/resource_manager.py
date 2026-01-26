import asyncio
import os
import socket
import subprocess
import time

from discord.ext import commands, tasks


class ResourceManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vllm_port = 8008
        self.host = "127.0.0.1"
        self.vllm_process = None
        self.is_starting_vllm = False
        self._lock = asyncio.Lock()

        self.last_activity = time.time()
        self.idle_timeout = 300  # 5 minutes idle
        self.idle_monitor.start()

    def is_port_open(self, host, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                return s.connect_ex((host, port)) == 0
        except Exception:
            return False

    def update_activity(self):
        """Call this when vLLM is used to reset the idle timer."""
        self.last_activity = time.time()

    async def ensure_vllm_started(self):
        """Checks if vLLM is running. If not, starts it."""
        self.update_activity()  # Reset timer on request

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
            print("[ResourceManager] vLLM Server is DOWN (Idle Mode). Waking up Ministral 14B...")

            try:
                # 4. Launch Service (Ministral 14B - Instruct)
                # Use 'start' to detach properly on Windows
                bat_path = os.path.abspath("start_vllm_instruct.bat")
                if not os.path.exists(bat_path):
                    print(f"[ResourceManager] Critical: {bat_path} not found!")
                    self.is_starting_vllm = False
                    return False

                # Detached launch
                subprocess.Popen(["start", "cmd", "/c", bat_path], shell=True)

                # 5. Wait for Port
                print("[ResourceManager] Waiting for vLLM Port 8001...")
                for i in range(120):  # 2 mins max
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

    async def stop_vllm(self):
        """Stops the vLLM process to save resources (VRAM/VLAM)."""
        if not self.is_port_open(self.host, self.vllm_port):
            return  # Already stopped

        print(f"[ResourceManager] 💤 idle timeout (5m) reached. Stopping vLLM to free VRAM for VLAM...")
        try:
            # 1. Kill by Window Title (Windows)
            subprocess.run(
                ["taskkill", "/F", "/FI", "WINDOWTITLE eq ORA-vLLM-Server"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=False,
            )
            # 2. Kill by Python module pattern
            subprocess.run(
                ["powershell", "-Command", "Get-Process | Where-Object { $_.CommandLine -like '*vllm.entrypoints.openai.api_server*' } | Stop-Process -Force"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=False,
            )

            print("[ResourceManager] ✅ vLLM stopped. VRAM is now free.")
        except Exception as e:
            print(f"[ResourceManager] ❌ Error stopping vLLM: {e}")

    @tasks.loop(seconds=60)
    async def idle_monitor(self):
        """Checks for idle state and stops vLLM if needed."""
        # Check if vLLM is actually running on 8008
        if self.is_port_open(self.host, self.vllm_port):
            if time.time() - self.last_activity > self.idle_timeout:
                await self.stop_vllm()

    @idle_monitor.before_loop
    async def before_idle_monitor(self):
        await self.bot.wait_until_ready()

    def cog_unload(self):
        self.idle_monitor.cancel()


async def setup(bot):
    await bot.add_cog(ResourceManager(bot))
