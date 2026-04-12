from fastapi import APIRouter

router = APIRouter(prefix="/goal-cascade", tags=["Goal Cascade"])


@router.get("/")
async def list_goal_cascades():
    """List all goal cascades"""
    return {"cascades": [], "total": 0}
