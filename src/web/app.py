import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.web import endpoints
from src.storage import Store

store: Store | None = None

def get_store() -> Store:
    assert store is not None, "Store is not initialized"
    return store

app = FastAPI(
    title="ORA Web API",
    version="0.1.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount router
app.include_router(endpoints.router, prefix="/api")


@app.get("/auth/discord")
async def auth_discord_passthrough(request: Request, code: str | None = None, state: str | None = None):
    """Expose the auth flow without the /api prefix for compatibility."""
    return await endpoints.auth_discord(request, code=code, state=state)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "ORA Discord Bot API is running"}


@app.on_event("startup")
async def on_startup() -> None:
    global store
    store = Store(os.getenv("DB_PATH", "data/ora.db"))
    await store.init()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    global store
    # Store might not need explicit disconnect if using aiofiles/sqlite3 directly per request, 
    # but good to have the hook.
    store = None
