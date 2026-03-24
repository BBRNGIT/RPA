"""
User Roles and Permissions System.

Implements role-based access control (RBAC) for RPA.
Ensures consistent authorization across Web UI and Terminal UI.

Roles (hierarchical):
- SUPERADMIN: Full system control, manages admins, access to raw data
- ADMIN: User management, reports, curriculum editing
- USER: Personal learning, progress tracking
- GUEST: Limited demo access
"""

from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """System permissions."""
    # Read permissions
    READ = "read"
    READ_OWN = "read_own"
    READ_ALL = "read_all"

    # Write permissions
    WRITE = "write"
    WRITE_OWN = "write_own"
    WRITE_ALL = "write_all"

    # Delete permissions
    DELETE = "delete"
    DELETE_OWN = "delete_own"

    # User management
    MANAGE_USERS = "manage_users"
    CREATE_USERS = "create_users"
    DELETE_USERS = "delete_users"

    # Learning permissions
    PRACTICE_LEARNING = "practice_learning"
    VIEW_OWN_PROGRESS = "view_own_progress"
    VIEW_ALL_PROGRESS = "view_all_progress"

    # Content permissions
    EDIT_CURRICULUM = "edit_curriculum"
    CREATE_CONTENT = "create_content"

    # System permissions
    MANAGE_SYSTEM = "manage_system"
    CONFIGURE_WORKFLOWS = "configure_workflows"
    VIEW_REPORTS = "view_reports"
    EXPORT_DATA = "export_data"
    ACCESS_RAW_DATA = "access_raw_data"
    TRIGGER_LEARNING = "trigger_learning"

    # Admin permissions
    MANAGE_ADMINS = "manage_admins"
    VIEW_SYSTEM_LOGS = "view_system_logs"

    # Demo permissions
    DEMO_ACCESS = "demo_access"


@dataclass
class RolePermissions:
    """Permissions configuration for a role."""

    role: str
    permissions: Set[Permission] = field(default_factory=set)
    description: str = ""
    ui_theme: Dict[str, str] = field(default_factory=dict)
    max_items_per_session: int = 100
    can_export_data: bool = False
    can_access_admin_panel: bool = False

    def has_permission(self, permission: Permission) -> bool:
        """Check if role has a specific permission."""
        return permission in self.permissions

    def has_any_permission(self, *permissions: Permission) -> bool:
        """Check if role has any of the specified permissions."""
        return any(p in self.permissions for p in permissions)

    def has_all_permissions(self, *permissions: Permission) -> bool:
        """Check if role has all specified permissions."""
        return all(p in self.permissions for p in permissions)


# Role definitions
ROLE_DEFINITIONS: Dict[str, RolePermissions] = {
    "superadmin": RolePermissions(
        role="superadmin",
        permissions={
            # All permissions
            Permission.READ, Permission.READ_ALL,
            Permission.WRITE, Permission.WRITE_ALL,
            Permission.DELETE, Permission.DELETE_OWN,
            Permission.MANAGE_USERS, Permission.CREATE_USERS, Permission.DELETE_USERS,
            Permission.MANAGE_ADMINS,
            Permission.PRACTICE_LEARNING,
            Permission.VIEW_OWN_PROGRESS, Permission.VIEW_ALL_PROGRESS,
            Permission.EDIT_CURRICULUM, Permission.CREATE_CONTENT,
            Permission.MANAGE_SYSTEM, Permission.CONFIGURE_WORKFLOWS,
            Permission.VIEW_REPORTS, Permission.EXPORT_DATA,
            Permission.ACCESS_RAW_DATA, Permission.TRIGGER_LEARNING,
            Permission.VIEW_SYSTEM_LOGS,
        },
        description="Full system control. Can manage all users including admins.",
        ui_theme={
            "primary_color": "#1a1a2e",
            "accent_color": "#ffd700",
            "border_color": "#dc2626",
            "badge": "👑 Superadmin",
            "theme_name": "dark-gold",
        },
        max_items_per_session=1000,
        can_export_data=True,
        can_access_admin_panel=True,
    ),

    "admin": RolePermissions(
        role="admin",
        permissions={
            Permission.READ, Permission.READ_ALL,
            Permission.WRITE, Permission.WRITE_OWN,
            Permission.DELETE_OWN,
            Permission.MANAGE_USERS, Permission.CREATE_USERS,
            Permission.PRACTICE_LEARNING,
            Permission.VIEW_OWN_PROGRESS, Permission.VIEW_ALL_PROGRESS,
            Permission.EDIT_CURRICULUM, Permission.CREATE_CONTENT,
            Permission.VIEW_REPORTS, Permission.EXPORT_DATA,
            Permission.TRIGGER_LEARNING,
        },
        description="User management, reports, and curriculum editing.",
        ui_theme={
            "primary_color": "#1e40af",
            "accent_color": "#3b82f6",
            "border_color": "#2563eb",
            "badge": "🛡️ Admin",
            "theme_name": "blue-professional",
        },
        max_items_per_session=500,
        can_export_data=True,
        can_access_admin_panel=True,
    ),

    "user": RolePermissions(
        role="user",
        permissions={
            Permission.READ, Permission.READ_OWN,
            Permission.WRITE, Permission.WRITE_OWN,
            Permission.DELETE_OWN,
            Permission.PRACTICE_LEARNING,
            Permission.VIEW_OWN_PROGRESS,
        },
        description="Personal learning dashboard and progress tracking.",
        ui_theme={
            "primary_color": "#f8fafc",
            "accent_color": "#22c55e",
            "border_color": "#e2e8f0",
            "badge": "👤 User",
            "theme_name": "light-friendly",
        },
        max_items_per_session=100,
        can_export_data=False,
        can_access_admin_panel=False,
    ),

    "guest": RolePermissions(
        role="guest",
        permissions={
            Permission.READ,
            Permission.DEMO_ACCESS,
        },
        description="Limited demo access with registration prompts.",
        ui_theme={
            "primary_color": "#f1f5f9",
            "accent_color": "#94a3b8",
            "border_color": "#cbd5e1",
            "badge": "👥 Guest",
            "theme_name": "minimal",
        },
        max_items_per_session=20,
        can_export_data=False,
        can_access_admin_panel=False,
    ),
}


def get_role_permissions(role: str) -> List[str]:
    """
    Get list of permission strings for a role.

    Args:
        role: Role name (superadmin, admin, user, guest)

    Returns:
        List of permission strings
    """
    role_config = ROLE_DEFINITIONS.get(role.lower())
    if role_config:
        return [p.value for p in role_config.permissions]
    return []


def check_permission(role: str, permission: Permission) -> bool:
    """
    Check if a role has a specific permission.

    Args:
        role: Role name
        permission: Permission to check

    Returns:
        True if role has permission
    """
    role_config = ROLE_DEFINITIONS.get(role.lower())
    if role_config:
        return role_config.has_permission(permission)
    return False


def get_role_config(role: str) -> Optional[RolePermissions]:
    """
    Get the full configuration for a role.

    Args:
        role: Role name

    Returns:
        RolePermissions or None if role not found
    """
    return ROLE_DEFINITIONS.get(role.lower())


def get_role_theme(role: str) -> Dict[str, str]:
    """
    Get UI theme settings for a role.

    Args:
        role: Role name

    Returns:
        Dictionary of theme settings
    """
    role_config = ROLE_DEFINITIONS.get(role.lower())
    if role_config:
        return role_config.ui_theme
    return ROLE_DEFINITIONS["user"].ui_theme


def get_role_badge(role: str) -> str:
    """
    Get badge emoji and text for a role.

    Args:
        role: Role name

    Returns:
        Badge string (e.g., "👑 Superadmin")
    """
    theme = get_role_theme(role)
    return theme.get("badge", "👤 User")


def validate_role_transition(current_role: str, target_role: str) -> bool:
    """
    Check if a role transition is allowed.

    Only superadmin can create admins.
    Only superadmin can create superadmins.

    Args:
        current_role: Role of user making the change
        target_role: Role to assign

    Returns:
        True if transition is allowed
    """
    if current_role.lower() == "superadmin":
        return True

    if current_role.lower() == "admin":
        # Admins can create users, but not admins or superadmins
        return target_role.lower() in ("user", "guest")

    return False


def get_highest_role(roles: List[str]) -> str:
    """
    Get the highest privilege role from a list.

    Args:
        roles: List of role names

    Returns:
        Highest privilege role
    """
    hierarchy = ["superadmin", "admin", "user", "guest"]

    for role in hierarchy:
        if role in [r.lower() for r in roles]:
            return role

    return "guest"


def get_users_manageable_by(role: str) -> List[str]:
    """
    Get list of roles that can be managed by a given role.

    Args:
        role: Role name

    Returns:
        List of manageable role names
    """
    if role.lower() == "superadmin":
        return ["admin", "user", "guest"]
    elif role.lower() == "admin":
        return ["user", "guest"]
    return []


class PermissionDeniedError(Exception):
    """Raised when a permission check fails."""

    def __init__(self, permission: Permission, role: str):
        self.permission = permission
        self.role = role
        super().__init__(
            f"Permission '{permission.value}' denied for role '{role}'"
        )


def require_permission(role: str, permission: Permission) -> None:
    """
    Require a permission, raising exception if not granted.

    Args:
        role: User's role
        permission: Required permission

    Raises:
        PermissionDeniedError: If permission not granted
    """
    if not check_permission(role, permission):
        raise PermissionDeniedError(permission, role)


# Permission checking utilities for endpoints

def can_read_all(role: str) -> bool:
    """Check if role can read all data (not just own)."""
    return check_permission(role, Permission.READ_ALL)


def can_manage_users(role: str) -> bool:
    """Check if role can manage users."""
    return check_permission(role, Permission.MANAGE_USERS)


def can_export_data(role: str) -> bool:
    """Check if role can export data."""
    return check_permission(role, Permission.EXPORT_DATA)


def can_access_admin_panel(role: str) -> bool:
    """Check if role can access admin panel."""
    role_config = get_role_config(role)
    return role_config.can_access_admin_panel if role_config else False


def can_trigger_learning(role: str) -> bool:
    """Check if role can trigger learning jobs."""
    return check_permission(role, Permission.TRIGGER_LEARNING)


def can_edit_curriculum(role: str) -> bool:
    """Check if role can edit curriculum."""
    return check_permission(role, Permission.EDIT_CURRICULUM)
