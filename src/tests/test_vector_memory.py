
import asyncio
import os
import shutil
from src.services.vector_memory import VectorMemory

# Clean test env
TEST_DB_PATH = os.path.join(os.getcwd(), "data", "vector_store")

async def test_vector_memory():
    print("🧠 Testing Vector Memory (ChromaDB)...")
    
    vm = VectorMemory("test_memory")
    user_id = "test_user_123"

    # 1. Add Memories
    print("  Adding memories...")
    await vm.add_memory("I love eating sushi on Fridays.", user_id, {"topic": "food"})
    await vm.add_memory("My favorite anime is Naruto.", user_id, {"topic": "anime"})
    await vm.add_memory("I hate Mondays.", user_id, {"topic": "mood"})
    
    # 2. Search (Exact Topic)
    print("  Searching for 'sushi'...")
    results = await vm.search_memory("What do I like to eat?", user_id)
    print(f"  Result: {results}")
    
    if any("sushi" in r for r in results):
        print("  ✅ Recall Successful (Sushi found)")
    else:
        print("  ❌ Recall Failed")

    # 3. Search (Different Topic)
    print("  Searching for 'anime'...")
    results = await vm.search_memory("Recommend me a show based on my taste", user_id)
    print(f"  Result: {results}")
    
    if any("Naruto" in r for r in results):
        print("  ✅ Recall Successful (Naruto found)")
    else:
        print("  ❌ Recall Failed")

    # Cleanup (Optional, keep for debugging)
    # await vm.wipe_user_memory(user_id)

if __name__ == "__main__":
    asyncio.run(test_vector_memory())
