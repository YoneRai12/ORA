import asyncio
import aiohttp
import json
import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def debug_stream():
    url = "http://localhost:8001/v1/messages"
    payload = {
        "user_identity": {"provider": "discord", "id": "DEBUG_USER", "display_name": "LocalDebug"},
        "content": "Hello via Debug Script",
        "attachments": [],
        "idempotency_key": "debug-stream-001"
    }
    
    print(f" sending to {url}...")
    async with aiohttp.ClientSession() as session:
        # 1. Start Run
        async with session.post(url, json=payload) as resp:
            data = await resp.json()
            print(f"Start Response: {data}")
            if "run_id" not in data:
                return
            run_id = data["run_id"]
            
        # 2. Listen to Events
        event_url = f"http://localhost:8001/v1/runs/{run_id}/events"
        print(f"Listening to {event_url}...")
        async with session.get(event_url) as resp:
            async for line in resp.content:
                if line:
                    decoded = line.decode("utf-8").strip()
                    if decoded.startswith("data: "):
                        print(f"EVENT: {decoded[6:]}")

if __name__ == "__main__":
    asyncio.run(debug_stream())
