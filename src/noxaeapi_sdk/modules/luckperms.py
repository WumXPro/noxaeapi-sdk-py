from __future__ import annotations

import urllib.parse
from typing import Dict, List

from ..http_engine import HttpEngine
from ..types import GroupInfo, PermissionNode


def _q(value: str) -> str:
    return urllib.parse.quote(value, safe="")


class LuckPermsModule:
    """Wraps the ``/v1/luckperms/*`` routes.

    These only exist on the server when the LuckPerms mod is loaded —
    calling any method here against a server without it will fail
    (typically a 404). There's no separate "is this available" flag from
    the SDK's side; check ``client.plugins.list()`` for LuckPerms if you
    need to branch on it ahead of time.

    Unlike most other modules, these POST/DELETE bodies are sent as real
    JSON (the server reads them with ``ctx.bodyAsClass(...)``, not
    ``ctx.formParam(...)``) — none of these calls pass ``form=True``.
    """

    def __init__(self, http: HttpEngine) -> None:
        self._http = http

    def get_player_groups(self, uuid: str) -> List[str]:
        """Get the groups a player belongs to."""
        return self._http.request("GET", f"luckperms/player/{_q(uuid)}/groups")

    def get_player_permissions(self, uuid: str) -> List[PermissionNode]:
        """Get a player's effective permission nodes."""
        return self._http.request("GET", f"luckperms/player/{_q(uuid)}/permissions")

    def add_player_permission(self, uuid: str, permission: str, value: bool = True) -> None:
        """Add a permission node to a player."""
        return self._http.request(
            "POST", f"luckperms/player/{_q(uuid)}/permission", body={"permission": permission, "value": value}
        )

    def check_player_permission(self, uuid: str, permission: str) -> Dict[str, object]:
        """Check whether a player has a given permission."""
        return self._http.request(
            "POST", f"luckperms/player/{_q(uuid)}/check-permission", body={"permission": permission}
        )

    def remove_player_permission(self, uuid: str, permission: str) -> None:
        """Remove a permission node from a player."""
        return self._http.request(
            "DELETE", f"luckperms/player/{_q(uuid)}/permission", body={"permission": permission}
        )

    def set_player_group(self, uuid: str, group: str) -> None:
        """Set a player's primary group."""
        return self._http.request("POST", f"luckperms/player/{_q(uuid)}/group", body={"group": group})

    def remove_player_group(self, uuid: str, group_name: str) -> None:
        """Remove a group from a player."""
        return self._http.request("DELETE", f"luckperms/player/{_q(uuid)}/group/{_q(group_name)}")

    def get_groups(self) -> List[str]:
        """List all known groups."""
        return self._http.request("GET", "luckperms/groups")

    def create_group(self, name: str) -> Dict[str, str]:
        """Create a new LuckPerms group. The name is lowercased server-side.

        Raises ``NoxAeApiError`` with a 409 status if the group already exists.
        """
        return self._http.request("POST", "luckperms/groups", body={"name": name})

    def delete_group(self, name: str) -> None:
        """Delete a LuckPerms group by name.

        The ``default`` group can't be deleted (400 — every user without
        an explicit group inherits from it) and a 404 is raised if it
        doesn't exist.
        """
        return self._http.request("DELETE", f"luckperms/group/{_q(name)}")

    def get_group_permissions(self, name: str) -> GroupInfo:
        """Get the permissions attached to a specific group."""
        return self._http.request("GET", f"luckperms/group/{_q(name)}/permissions")
