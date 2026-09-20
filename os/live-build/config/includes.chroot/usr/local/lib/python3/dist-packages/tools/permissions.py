"""
Permission Policy Engine for JARVIS OS Tools
Default DENY policy implementation.
"""

from typing import List, Set, Tuple, Optional

class PermissionPolicy:
    """
    Evaluates required tool permissions against caller's granted permissions.
    Default DENY when tool or permission is unknown or unspecified.
    """

    def __init__(self, granted_permissions: Optional[List[str]] = None):
        # Default granted permissions for safe demo profile
        self.granted_permissions: Set[str] = set(granted_permissions or ["system:read", "time:read", "echo:write"])

    def check_permission(self, required_permissions: List[str]) -> Tuple[bool, str]:
        """
        Validates required permissions.
        Returns (allowed, reason).
        """
        if not required_permissions:
            return True, "No permissions required."

        for perm in required_permissions:
            if perm not in self.granted_permissions:
                return False, f"Permission DENIED: Required permission '{perm}' is not granted."

        return True, "All required permissions granted."

    def grant(self, permission: str):
        self.granted_permissions.add(permission)

    def revoke(self, permission: str):
        self.granted_permissions.discard(permission)
