from typing import Optional

from fastapi import Depends, Request
from ora_core.database.models import User
from ora_core.database.repo import Repository
from ora_core.database.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession


async def get_repo(db: AsyncSession = Depends(get_db)) -> Repository:
    return Repository(db)

async def get_current_user(
    request: Request,
    repo: Repository = Depends(get_repo)
) -> Optional[User]:
    """
    Default Auth Dependency.
    
    In 'local' mode: returns None (letting the route logic handle manual identity from body).
    In 'cloudflare' mode: Checks headers (via overridden logic or direct check).
    """
    # This function is intended to be OVERRIDDEN in main.py if Cloudflare is active.
    # Or we can put the logic here dynamically.
    
    if hasattr(request.app.state, "config"):
        config = request.app.state.config
        if config.auth_strategy == "cloudflare":
            from ora_core.api.middleware.cloudflare_auth import get_current_user_from_header
            return await get_current_user_from_header(request, repo)
            
    return None
