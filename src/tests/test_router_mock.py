import asyncio
import sys
from unittest.mock import MagicMock, AsyncMock, Mock

# Mock dependency setup
sys.modules["src.utils.llm_client"] = Mock()
sys.modules["src.config"] = Mock()
sys.modules["src.config"].OPENAI_API_KEY = "dummy_key"

# Now we can import the class under test
from src.cogs.handlers.tool_selector import ToolSelector

# Simulation Data
TOOLS = [
    {"name": "join_voice_channel", "description": "Join VC", "tags": ["voice"]},
    {"name": "music_play", "description": "Play Music", "tags": ["music", "play"]},
    {"name": "google_search", "description": "Search Google", "tags": ["search"]},
    {"name": "admin_ban", "description": "Ban User", "tags": ["admin"]},
]

async def test_router_voice_selection():
    print("Running test_router_voice_selection...")
    bot = MagicMock()
    selector = ToolSelector(bot)
    
    # Mock LLM Response
    # Scenario: User says "Join VC" -> Router should select 'join_voice_channel'
    selector.llm_client.chat = AsyncMock(return_value=('["join_voice_channel"]', None, {}))
    
    selected = await selector.select_tools("Join VC", TOOLS, platform="discord")
    
    # Verification
    if len(selected) == 1 and selected[0]["name"] == "join_voice_channel":
        print("✅ Voice Selection Verified")
    else:
        print(f"❌ Voice Selection Failed: got {selected}")

async def test_router_irrelevant_pruning():
    print("Running test_router_irrelevant_pruning...")
    bot = MagicMock()
    selector = ToolSelector(bot)
    
    # Scenario: User says "Hello" -> Router should return EMPTY (Chat only)
    selector.llm_client.chat = AsyncMock(return_value=('[]', None, {}))
    
    selected = await selector.select_tools("Hello", TOOLS, platform="discord")
    
    if len(selected) == 0:
        print("✅ Chat Pruning Verified")
    else:
        print(f"❌ Chat Pruning Failed: got {selected}")

async def test_router_fallback():
    print("Running test_router_fallback...")
    bot = MagicMock()
    selector = ToolSelector(bot)
    
    # Scenario: LLM fails -> Fallback to ALL tools
    selector.llm_client.chat = AsyncMock(side_effect=Exception("LLM Error"))
    
    selected = await selector.select_tools("Error Case", TOOLS, platform="discord")
    
    if len(selected) == len(TOOLS):
        print("✅ Fallback Safety Verified")
    else:
        print(f"❌ Fallback Safety Failed: got {len(selected)} tools")

if __name__ == "__main__":
    async def run_tests():
        await test_router_voice_selection()
        await test_router_irrelevant_pruning()
        await test_router_fallback()
    
    try:
        asyncio.run(run_tests())
        print("\nAll Tests Completed.")
    except Exception as e:
        print(f"Test Runner Failed: {e}")
