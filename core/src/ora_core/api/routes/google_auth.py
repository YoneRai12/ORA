import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from ora_core.database.repo import Repository
from ora_core.database.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()

# Web UI の Client ID / Secret は環境変数から取得
def get_google_client_config():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8001/v1/auth/google/callback")
    
    if not client_id or not client_secret:
        return None

    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email"
]

@router.get("/google/login")
async def google_login(request: Request):
    """Google の認証画面へリダイレクトするための URL を生成します。"""
    config = get_google_client_config()
    if not config:
        logger.error("GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not configured in .env")
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    flow = Flow.from_client_config(
        config,
        scopes=SCOPES,
        redirect_uri=config["web"]["redirect_uris"][0]
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent' # Ensure we get refresh token
    )
    
    return {"url": authorization_url, "state": state}

@router.get("/google/callback")
async def google_callback(request: Request, code: str, state: str, db: AsyncSession = Depends(get_db)):
    """Google からのリダイレクトを受け取り、ユーザー情報を取得します。"""
    config = get_google_client_config()
    if not config:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    flow = Flow.from_client_config(
        config,
        scopes=SCOPES,
        redirect_uri=config["web"]["redirect_uris"][0]
    )
    
    try:
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # ユーザー情報の取得
        from googleapiclient.discovery import build
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        
        google_id = user_info.get("id")
        # email = user_info.get("email")
        
        # ユーザーの取得または作成
        repo = Repository(db)
        user = await repo.get_or_create_user("google", google_id)
        # Update metadata if needed
        await db.commit()
        
        # フロントエンドへリダイレクト（成功時）
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        # Pass internal user UUID to frontend
        return RedirectResponse(url=f"{frontend_url}/dashboard?auth_success=true&user_id={user.id}")

    except Exception as e:
        logger.exception("Google Callback Error")
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(url=f"{frontend_url}/login?error={str(e)}")
