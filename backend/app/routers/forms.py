from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.models.user import User
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/forms", tags=["Forms"])


class PrefillRequest(BaseModel):
    form_type: str
    context: dict[str, str] = {}


@router.post("/prefill")
async def get_prefill_data(
    payload: PrefillRequest,
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    # Keep API contract stable even when no prefill rules are configured yet.
    _ = (payload, current_user)
    return []
