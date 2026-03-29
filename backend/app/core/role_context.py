from app.models.enums import UserRole
from app.models.user import User


def get_user_roles(user: User) -> set[UserRole]:
    roles: set[UserRole] = set()

    for raw in user.roles or []:
        try:
            roles.add(UserRole(raw))
        except ValueError:
            continue

    roles.add(user.role)
    if UserRole.manager in roles:
        roles.add(UserRole.employee)

    return roles


def get_default_mode(user: User) -> UserRole:
    roles = get_user_roles(user)
    if UserRole.manager in roles and user.role == UserRole.manager:
        return UserRole.manager
    if UserRole.employee in roles:
        return UserRole.employee
    return user.role