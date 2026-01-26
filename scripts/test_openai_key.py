import os
import asyncio
from openai import AsyncOpenAI

# Load key from .env manually to be sure
from dotenv import load_dotenv
load_dotenv(override=True)

async def test_key():
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"Loaded Key: {api_key[:10]}...{api_key[-5:] if api_key else 'None'}")
    
    client = AsyncOpenAI(api_key=api_key)
    
    try:
        print(f"Sending request to gpt-4o-mini with endpoint: {client.base_url}")
        resp = await asyncio.wait_for(client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        ), timeout=15.0)
        print(f"Success! Response: {resp.choices[0].message.content}")
    except asyncio.TimeoutError:
        print("Error: Request timed out (15s)")
    except Exception as e:
        print(f"Error Type: {type(e)}")
        print(f"Error Details: {e}")

if __name__ == "__main__":
    asyncio.run(test_key())
