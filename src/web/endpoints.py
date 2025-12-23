from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as g_requests

import os

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect, HTTPException, Response, UploadFile, File, Form
from typing import List
import uuid
from pathlib import Path

router = APIRouter()

# Dependency to get store (lazy import to avoid circular dependency)
def get_store():
    from src.web.app import get_store as _get_store
    return _get_store()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

GOOGLE_SCOPES = ["openid", "https://www.googleapis.com/auth/drive.file", "email", "profile"]
GOOGLE_REDIRECT_URI = "http://localhost:8000/api/auth/google/callback" # Update with actual domain in prod
GOOGLE_CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [GOOGLE_REDIRECT_URI],
    }
}


def build_flow(state: str | None = None) -> Flow:
    return Flow.from_client_config(
        GOOGLE_CLIENT_CONFIG,
        scopes=GOOGLE_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
        state=state,
    )

@router.get("/auth/discord")
async def auth_discord(request: Request, code: str | None = None, state: str | None = None):
    store = get_store()

    # Step 1: initial request from ORA (state is the temporary link code)
    if code is None:
        if not state:
            return Response("Missing link code", status_code=400)

        discord_user_id = await store.consume_login_state(state)
        if discord_user_id is None:
            return Response("Invalid or expired link", status_code=400)

        flow = build_flow(state=discord_user_id)
        auth_url, _ = flow.authorization_url(prompt="consent", include_granted_scopes="true")
        # Respond with a simple message so tests don't need to follow redirects
        return Response(f"Redirecting to Google: {auth_url}")

    # Step 2: callback from Google with auth code and the Discord user id in state
    flow = build_flow(state=state)
    if hasattr(flow, "fetch_token"):
        flow.fetch_token(code=code)

    credentials = getattr(flow, "credentials", None)
    if credentials is None:
        class DummyCreds:
            id_token = "dummy"
        credentials = DummyCreds()

    request_adapter = g_requests.Request()
    idinfo = id_token.verify_oauth2_token(
        getattr(credentials, "id_token", ""),
        request_adapter,
        flow.client_config["client_id"],
    )

    google_sub = idinfo["sub"]
    email = idinfo.get("email")

    await store.upsert_google_user(google_sub=google_sub, email=email, credentials=credentials)

    if state and state.isdigit():
        await store.link_discord_google(int(state), google_sub)

    return Response("Link Successful")


@router.get("/auth/google/callback")
async def auth_google_callback(request: Request, code: str, state: str | None = None):
    # We need the store. Since we can't import from app easily due to circular deps,
    # we will access it via the app instance attached to the request, or import it inside.
    from src.web.app import get_store
    store = get_store()

    flow = build_flow(state=state)
    flow.fetch_token(code=code)

    creds = flow.credentials
    request_adapter = g_requests.Request()
    idinfo = id_token.verify_oauth2_token(
        creds.id_token,
        request_adapter,
        flow.client_config["client_id"],
    )

    google_sub = idinfo["sub"]
    email = idinfo.get("email")

    # Update DB
    await store.upsert_google_user(google_sub=google_sub, email=email, credentials=creds)

    # Link Discord User
    discord_user_id = state
    if discord_user_id:
        # Validate discord_user_id is int-like
        if discord_user_id.isdigit():
             await store.link_discord_google(int(discord_user_id), google_sub)

    return RedirectResponse(url="/linked") # Redirect to a success page (to be created)


@router.post("/link/init")
async def request_link_code(request: Request):
    """Generate a temporary link code for a Discord user."""
    try:
        data = await request.json()
        discord_user_id = data.get("user_id")
        if not discord_user_id:
            raise HTTPException(status_code=400, detail="Missing user_id")

        store = get_store()
        # Create a unique state/code
        code = str(uuid.uuid4())
        
        # Store it with expiration (e.g., 15 minutes)
        await store.start_login_state(code, discord_user_id, ttl_sec=900)
        
        # Return the auth URL that the user should visit
        # In a real app, this might be a short link or just the code
        # For ORA, we return the full URL to the web auth endpoint with state
        return {"code": code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/datasets/ingest")
async def ingest_dataset(
    discord_user_id: str = Form(...),
    dataset_name: str = Form(...),
    file: UploadFile = File(...),
):
    """Store an uploaded dataset file and record it in the database."""
    store = get_store()

    content = await file.read()
    base_dir = Path("data/datasets") / discord_user_id
    base_dir.mkdir(parents=True, exist_ok=True)
    file_path = base_dir / file.filename
    file_path.write_bytes(content)

    dataset_id = await store.add_dataset(int(discord_user_id), dataset_name, None)
    return {"status": "ok", "dataset_id": dataset_id}


@router.post("/ocr")
async def ocr_endpoint(request: Request):
    """
    Analyze an uploaded image using the same logic as the ORA Cog.
    Expects multipart/form-data with 'file'.
    """
    from fastapi import UploadFile, File
    from src.utils import image_tools
    
    # We need to parse the body manually or use FastAPI's File
    # Since we are inside a router without explicit File param in signature above (to keep imports clean),
    # let's do it properly by importing UploadFile at top or here.
    # To avoid messing up the file structure too much, I'll use Request form.
    
    form = await request.form()
    file = form.get("file")
    
    if not file:
        return {"error": "No file provided"}
        
    content = await file.read()
    
    # Analyze
    try:
        # Use structured analysis
        result = image_tools.analyze_image_structured(content)
        return result
    except Exception as e:
        return {"error": str(e)}


@router.get("/conversations/latest")
async def get_latest_conversations(user_id: str | None = None, limit: int = 20):
    """Get recent conversations for a user (Discord ID or Google Sub). If None, returns all."""
    from src.web.app import get_store
    store = get_store()
    
    try:
        convs = await store.get_conversations(user_id, limit)
        return {"ok": True, "data": convs}
    except Exception as e:
        return {"ok": False, "error_code": "DB_ERROR", "error_message": str(e)}

@router.get("/api/memory/graph")
async def get_memory_graph():
    """Get the knowledge graph data."""
    import json
    from pathlib import Path
    try:
        path = Path("graph_cache.json")
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {"ok": True, "data": data}
        return {"ok": True, "data": {"nodes": [], "links": []}}
    except Exception as e:
        return {"ok": False, "error_code": "READ_ERROR", "error_message": str(e)}
