import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Set PYTHONPATH
sys.path.append(os.path.join(os.getcwd(), "core", "src"))

import asyncio

from ora_core.database.models import Base
from ora_core.database.session import engine


async def init_db():
    print("Initializing Database...")
    async with engine.begin() as conn:
        # Import all models to ensure they are registered with Base
        await conn.run_sync(Base.metadata.create_all)
    print("Database Initialized Successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
