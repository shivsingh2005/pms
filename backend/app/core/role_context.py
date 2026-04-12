"""User role context utilities."""

from app.models.enums import UserRole
from app.models.user import User


def get_user_roles(user: User) -> set[UserRole]:
    """Get all roles for a user.
    
    Combines the primary role with any additional roles from the roles array.
    
    Args:
        user: The user object
        
    Returns:
        A set of UserRole enums
    """
    # Ensure role is a UserRole enum
    primary_role = user.role if isinstance(user.role, UserRole) else UserRole(user.role)
    roles = {primary_role}
    
    # Convert string roles to UserRole enums
    if user.roles:
        for role_str in user.roles:
            try:
                if isinstance(role_str, UserRole):
                    roles.add(role_str)
                else:
                    roles.add(UserRole(role_str))
            except (ValueError, KeyError):
                # Skip invalid roles
                pass
    
    return roles


def get_default_mode(user: User) -> str | None:
    """Get the default mode for a user based on their role.
    
    Args:
        user: The user object
        
    Returns:
        The default mode string, or None if the role doesn't map to a mode
    """
    user_roles = get_user_roles(user)
    role_values = {role.value for role in user_roles}
    
    # Managers can have both employee and manager mode
    if "manager" in role_values:
        return "manager"
    
    # Employees can only use employee mode
    if "employee" in role_values:
        return "employee"
    
    # HR and leadership roles don't have a specific mode in this context
    # but they might use manager-like functionality
    if "hr" in role_values or "leadership" in role_values:
        return None
    
    return None
