from collections.abc import Callable
from fastapi import Depends, HTTPException, status
from app.core.role_context import get_user_roles
from app.models.enums import UserRole
from app.utils.dependencies import get_current_user
from app.models.user import User


def require_roles(*allowed_roles: UserRole) -> Callable:
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        user_roles = get_user_roles(current_user)
        if not user_roles.intersection(set(allowed_roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have enough permissions",
            )
        return current_user

    return checker
