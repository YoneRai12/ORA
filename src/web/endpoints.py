from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as g_requests

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect, HTTPException
from typing import List
from datetime import datetime
import uuid

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

GOOGLE_CLIENT_SECRETS_FILE = "google_client_secrets.json"
GOOGLE_SCOPES = ["openid", "https://www.googleapis.com/auth/drive.file", "email", "profile"]
GOOGLE_REDIRECT_URI = "http://localhost:8000/api/auth/google/callback" # Update with actual domain in prod


def build_flow(state: str | None = None) -> Flow:
    return Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE,
        scopes=GOOGLE_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
        state=state,
    )

@router.get("/auth/discord")
async def auth_discord(request: Request, code: str | None = None, state: str | None = None):
    # If no code, redirect to Google
    if code is None:
        discord_user_id = request.query_params.get("discord_user_id")
        flow = build_flow(state=discord_user_id or "")
        auth_url, _ = flow.authorization_url(prompt="consent", include_granted_scopes="true")
        return RedirectResponse(auth_url)

    # If code exists, handle Discord auth (not implemented yet per instructions)
    return {"message": "Discord auth flow not fully implemented yet."}


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


@router.post("/auth/link-code")
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
        auth_url = f"{GOOGLE_REDIRECT_URI}?state={code}" # Wait, this is callback.
        # We need to point to the start of the flow
        # Actually, the user should visit /api/auth/discord?discord_user_id=...
        # But we want to use the code as state.
        
        # Let's construct the Google Auth URL directly or via our endpoint
        flow = build_flow(state=code)
        auth_url, _ = flow.authorization_url(prompt="consent", include_granted_scopes="true")
        
        return {"url": auth_url, "code": code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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

@router.get("/memory/graph")
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

@router.get("/dashboard/usage")
async def get_dashboard_usage():
    """Get global cost usage stats from CostManager state file (Aggregated)."""
    import json
    from pathlib import Path
    
    state_path = Path("L:/ORA_State/cost_state.json")
    
    # Default Structure
    response_data = {
        "total_usd": 0.0,
        "daily_tokens": {
            "high": 0,
            "stable": 0,
            "burn": 0
        },
        "last_reset": ""
    }
    
    if not state_path.exists():
         return {"ok": True, "data": response_data, "message": "No cost state found"}
         
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # Helper to Sum Usage
        def add_usage(bucket_key: str, bucket_data: dict, target_data: dict):
            # bucket_data structure: {"used": {"tokens_in": X, "tokens_out": Y, "usd": Z}, ...}
            # target_data: The specific dict in response_data (daily_tokens or lifetime_tokens)
            
            used = bucket_data.get("used", {})
            tokens = used.get("tokens_in", 0) + used.get("tokens_out", 0)
            usd = used.get("usd", 0.0)
            
            # Add to proper lane
            if bucket_key.startswith("high:"):
                target_data["high"] += tokens
            elif bucket_key.startswith("stable:"):
                target_data["stable"] += tokens
            elif bucket_key.startswith("burn:"):
                target_data["burn"] += tokens
            elif bucket_key.startswith("optimization:"):
                if "optimization" not in target_data:
                    target_data["optimization"] = 0
                target_data["optimization"] += tokens

            # Add to OpenAI Sum (for verifying against Dashboard)
            # RELAXED CHECK: If it contains 'openai' OR is an optimization lane (usually API)
            # We want to capture ALL API usage in this sum for the user.
            if ":openai" in bucket_key or "optimization" in bucket_key or "high" in bucket_key:
                # Exclude local manually if needed, but usually local doesn't use these lanes in CostManager
                if "openai_sum" in target_data:
                   target_data["openai_sum"] += tokens
                else:
                   target_data["openai_sum"] = tokens
            
            return usd

        # Default Structure
        response_data = {
            "total_usd": 0.0,
            "daily_tokens": {
                "high": 0, "stable": 0, "burn": 0
            },
            "lifetime_tokens": {
                "high": 0, "stable": 0, "burn": 0, "optimization": 0, "openai_sum": 0
            },
            "last_reset": datetime.now().isoformat()
        }

        # 1. Process Global Buckets (Current - Daily)
        for key, bucket in raw_data.get("global_buckets", {}).items():
            usd_gain = add_usage(key, bucket, response_data["daily_tokens"])
            # Daily OpenAI Sum isn't strictly needed unless we want "Today's OpenAI Tokens"
            # But let's keep it clean
            response_data["total_usd"] += usd_gain
            
        # 1b. Process Global History (Lifetime)
        # First, add Today's usage to Lifetime
        for key, bucket in raw_data.get("global_buckets", {}).items():
            add_usage(key, bucket, response_data["lifetime_tokens"])
        
        # Then, add History to Lifetime
        for key, history_list in raw_data.get("global_history", {}).items():
            for bucket in history_list:
                usd_gain = add_usage(key, bucket, response_data["lifetime_tokens"])
                response_data["total_usd"] += usd_gain # Accumulate lifetime USD? Or just daily USD?
                # Burn limit is cumulative, so let's track ALL usage USD here for "Lifetime USD".
                # But "Current Burn Limit" might need separate logic. 
                # For this dashboard view, "Total Spend" implies Lifetime.

        # 2. Process User Buckets (Main Source of Truth for Dashboard)
        # We assume User Buckets contain the breakdown.
        # To avoid double counting with Global (if it existed), we rely on Users here or use max.
        # Given Global seems empty/desynced, we add User usage to valid totals.
        
        for user_buckets in raw_data.get("user_buckets", {}).values():
            for key, bucket in user_buckets.items():
                usd_gain = add_usage(key, bucket, response_data["daily_tokens"])
                
                # Accumulate Total USD from Users
                response_data["total_usd"] += usd_gain
                
                # CRITICAL FIX: Also aggregate User Usage into Lifetime Tokens
                # This ensures that if Global History is missing/desynced, the Dashboard still shows the sum of known users.
                # add_usage adds to the target dict.
                add_usage(key, bucket, response_data["lifetime_tokens"])
                
        # 2b. User History Loop (to catch past usage not in current user_buckets)
        for user_hists in raw_data.get("user_history", {}).values():
             for key, hist_list in user_hists.items():
                 for bucket in hist_list:
                     add_usage(key, bucket, response_data["lifetime_tokens"])
                
                # Update Lifetime with User data too? 
                # If we trust user buckets, we should ensure they feed into lifetime view if needed.
                # But lifetime_tokens loop (1b) looked at Global History.
                # If Global History is empty, user history won't be seen.
                # For now, fixing "Current Estimated Cost" (total_usd) is the priority.

        # 2b. User History (Not needed for system total, but good for individual stats below)
        pass

        return {"ok": True, "data": response_data}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@router.get("/dashboard/history")
async def get_dashboard_history():
    """Get historical usage data (timeline) and model breakdown."""
    import json
    from pathlib import Path
    
    state_path = Path("L:/ORA_State/cost_state.json")
    if not state_path.exists():
        return {"ok": False, "error": "No cost state found"}

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            
        timeline = {} # "YYYY-MM-DD" -> {high, stable, optimization, usd}
        breakdown = {} # "high" -> {"openai": 100, "total": 100}

        def process_bucket(key, bucket, date_str):
            # 1. Update Timeline
            if date_str not in timeline:
                timeline[date_str] = {"date": date_str, "high": 0, "stable": 0, "optimization": 0, "burn": 0, "usd": 0.0}
            
            t_data = timeline[date_str]
            used = bucket.get("used", {})
            tokens = used.get("tokens_in", 0) + used.get("tokens_out", 0)
            usd = used.get("usd", 0.0)
            
            t_data["usd"] += usd
            
            key_lower = key.lower()
            lane = "unknown"
            if key_lower.startswith("high"):
                t_data["high"] += tokens
                lane = "high"
            elif key_lower.startswith("stable"):
                t_data["stable"] += tokens
                lane = "stable"
            elif key_lower.startswith("optimization"):
                t_data["optimization"] += tokens
                lane = "optimization"
            elif key_lower.startswith("burn"):
                t_data["burn"] += tokens
                lane = "burn"

            # 2. Update Breakdown (Total Lifetime)
            if lane not in breakdown:
                breakdown[lane] = {"total": 0}
            
            breakdown[lane]["total"] += tokens
            
            # Extract Provider/Model (Format: lane:provider:model)
            parts = key_lower.split(":")
            if len(parts) >= 2:
                provider = parts[1]
                # If model is present, maybe use it? For now just provider.
                model = parts[2] if len(parts) > 2 else "default"
                label = f"{provider} ({model})"
                
                if label not in breakdown[lane]:
                    breakdown[lane][label] = 0
                breakdown[lane][label] += tokens

        # Process History
        for key, hist_list in raw_data.get("global_history", {}).items():
            for bucket in hist_list:
                process_bucket(key, bucket, bucket["day"])

        # Process Current (Today)
        for key, bucket in raw_data.get("global_buckets", {}).items():
             process_bucket(key, bucket, bucket["day"])

        # Convert timeline to sorted list
        sorted_timeline = sorted(timeline.values(), key=lambda x: x["date"])

        return {"ok": True, "data": {"timeline": sorted_timeline, "breakdown": breakdown}}
        
    except Exception as e:
        return {"ok": False, "error": str(e)}

@router.get("/dashboard/users")
async def get_dashboard_users():
    """Get list of users with display names and stats from Memory JSONs."""
    import json
    import os
    import aiofiles
    from pathlib import Path
    
    MEMORY_DIR = Path("L:/ORA_Memory/users")
    users = []

    try:
        if MEMORY_DIR.exists():
            for method_file in MEMORY_DIR.glob("*.json"):
                try:
                    uid = method_file.stem # Filename without extension = User ID
                    
                    async with aiofiles.open(method_file, "r", encoding="utf-8") as f:
                        content = await f.read()
                        data = json.loads(content)
                        
                        # Optimization Points: Traits count or summary length?
                        # Let's show trait count as "Points" for now, or just return traits.
                        traits = data.get("traits", [])
                        
                        users.append({
                            "discord_user_id": uid,
                            "display_name": data.get("name", "Unknown"),
                            "created_at": data.get("last_updated", ""), # Use last update
                            "points": len(traits), # Mock points
                            # Status Priority: Explicit DB value -> Trait presence -> Pending
                            "status": data.get("status", "Optimized" if len(traits) > 0 else "Pending"),
                            "impression": data.get("impression", None)
                        })
                except Exception as e:
                    print(f"Error reading user file {method_file}: {e}")

        # 2. Merge with Cost Data (Aggregated) & Find Missing Users
        state_path = Path("L:/ORA_State/cost_state.json")
        cost_data = {}
        if state_path.exists():
             with open(state_path, "r", encoding="utf-8") as f:
                cost_data = json.load(f)

        existing_ids = {u["discord_user_id"] for u in users}
        
        # Check for users who have cost activity but NO memory file yet (Processing)
        all_user_buckets = cost_data.get("user_buckets", {})
        for uid in all_user_buckets:
            if uid not in existing_ids:
                users.append({
                    "discord_user_id": uid,
                    "display_name": f"User {uid}"[:12] + "...", # Placeholder until memory created
                    "created_at": "",
                    "points": 0,
                    "status": "Pending", # Force Pending for active users without profile
                    "impression": "Processing..."
                })
                existing_ids.add(uid) # Prevent dupes if logic changes
                
        # 3. Calculate Cost Usage for ALL Users
        for u in users:
            uid = u["discord_user_id"]
                    
            # Default Structure
            u["cost_usage"] = {"high": 0, "stable": 0, "burn": 0, "total_usd": 0.0}
            
            if uid in all_user_buckets:
                user_specific_buckets = all_user_buckets[uid]
                for key, bucket in user_specific_buckets.items():
                    used = bucket.get("used", {})
                    tokens = used.get("tokens_in", 0) + used.get("tokens_out", 0)
                    cost = used.get("usd", 0.0)
                    
                    u["cost_usage"]["total_usd"] += cost

                    bucket_key_lower = key.lower()
                    if bucket_key_lower.startswith("high"):
                        u["cost_usage"]["high"] += tokens
                    elif bucket_key_lower.startswith("stable"):
                        u["cost_usage"]["stable"] += tokens
                    elif bucket_key_lower.startswith("burn"):
                        u["cost_usage"]["burn"] += tokens
                    elif bucket_key_lower.startswith("optimization"):
                        if "optimization" not in u["cost_usage"]:
                            u["cost_usage"]["optimization"] = 0
                        u["cost_usage"]["optimization"] += tokens

                    
                    # Detect Provider
                    # key pattern: lane:provider:model or similar
                    parts = bucket_key_lower.split(":")
                    if len(parts) >= 2:
                        provider = parts[1]
                        if "providers" not in u:
                            u["providers"] = set()
                        u["providers"].add(provider)
                    
            # Determine Mode
            providers = u.get("providers", set())
            if "openai" in providers:
                u["mode"] = "API (Paid)"
            elif "local" in providers or "gemini_trial" in providers:
                u["mode"] = "Private (Local/Free)"
            else:
                u["mode"] = "Unknown"
            
            
            # Clean up set for JSON
            if "providers" in u:
                del u["providers"]
            
            # Force Pending status? NO. Only if they strictly lack a profile (handled above).
            # If they have usage but no profile: they were added as Pending.
            # If they have usage AND profile: status comes from profile (Optimized/Idle).
            pass
        
        return {"ok": True, "data": users}

    except Exception as e:
        return {"ok": False, "error": str(e)}

@router.get("/dashboard/users/{user_id}")
async def get_user_details(user_id: str):
    """Get full details for a specific user (traits, history, context)."""
    import aiofiles
    import json
    from pathlib import Path
    
    MEMORY_DIR = Path("L:/ORA_Memory/users")
    path = MEMORY_DIR / f"{user_id}.json"
    
    if not path.exists():
        return {"ok": False, "error": "User profile not found"}
        
    try:
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            content = await f.read()
            data = json.loads(content)
            return {"ok": True, "data": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}
