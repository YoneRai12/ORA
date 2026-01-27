from fastapi import APIRouter, Depends
from ora_core.database.repo import Repository
from ora_core.database.session import AsyncSessionLocal

router = APIRouter()

async def get_repo():
    async with AsyncSessionLocal() as session:
        yield Repository(session)

@router.get("/dashboard")
async def get_dashboard_summary(repo: Repository = Depends(get_repo)):
    """
    Get summary stats for the dashboard.
    """
    stats = await repo.get_dashboard_stats()
    return stats
