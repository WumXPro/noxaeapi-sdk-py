from __future__ import annotations

import urllib.parse
from typing import Any, Dict, List, Optional, Union

from ..http_engine import HttpEngine
from ..types import (
    Gamemode,
    InventoryItem,
    OfflinePlayer,
    OnlinePlayer,
    PlayerResolveResult,
    PlayerStats,
)


def _q(value: str) -> str:
    return urllib.parse.quote(value, safe="")


class PlayersModule:
    def __init__(self, http: HttpEngine) -> None:
        self._http = http

    def list(self) -> List[OnlinePlayer]:
        """List currently online players."""
        return self._http.request("GET", "players")

    def list_all(self) -> List[OfflinePlayer]:
        """List all players the server has ever seen (online + offline)."""
        return self._http.request("GET", "players/all")

    def get(self, uuid: str) -> Union[OnlinePlayer, OfflinePlayer]:
        """Get a single player by UUID (works for online or offline players)."""
        return self._http.request("GET", f"players/{_q(uuid)}")

    def resolve(self, name: str) -> PlayerResolveResult:
        """Resolve a player name to their UUID using the server's own local player cache.

        Works on both online-mode and offline-mode servers, unlike Mojang's public
        API - the UUID returned matches whatever this server actually uses for that
        player's stats/economy/etc. Checks currently online players first, then
        falls back to the server's offline player cache. Raises
        ``NoxAeApiNotFoundError`` if no known player with that name has ever joined.
        """
        return self._http.request("GET", f"players/resolve/{_q(name)}")

    def get_inventory(self, player_uuid: str, world_uuid: str) -> List[InventoryItem]:
        """Get a player's inventory in a specific world."""
        return self._http.request("GET", f"players/{_q(player_uuid)}/{_q(world_uuid)}/inventory")

    def kick(self, uuid: str, reason: Optional[str] = None) -> None:
        """Kick an online player, optionally with a reason."""
        body: Optional[Dict[str, Any]] = {"reason": reason} if reason else None
        return self._http.request("POST", f"players/{_q(uuid)}/kick", body=body, form=True)

    def ban(self, uuid: str, reason: Optional[str] = None, expiry: Optional[str] = None) -> None:
        """Ban a player, optionally with a reason and an ISO-8601 expiry (e.g. "2030-01-01T00:00:00Z").

        Omit ``expiry`` for a permanent ban.
        """
        body: Optional[Dict[str, Any]] = {"reason": reason, "expiry": expiry} if (reason or expiry) else None
        return self._http.request("POST", f"players/{_q(uuid)}/ban", body=body, form=True)

    def unban(self, uuid: str) -> None:
        """Remove a player's ban."""
        return self._http.request("DELETE", f"players/{_q(uuid)}/ban")

    def teleport(self, uuid: str, location: Dict[str, Any]) -> None:
        """Teleport a player to a location, e.g. ``{"x": 0, "y": 64, "z": 0, "world": "world"}``."""
        return self._http.request("POST", f"players/{_q(uuid)}/teleport", body=location, form=True)

    def set_gamemode(self, uuid: str, gamemode: Gamemode) -> None:
        """Change a player's gamemode."""
        return self._http.request(
            "PUT", f"players/{_q(uuid)}/gamemode", body={"gamemode": gamemode}, form=True
        )

    def get_stats(self, uuid: str) -> PlayerStats:
        """Get kill/death/playtime/block stats for a player."""
        return self._http.request("GET", f"players/{_q(uuid)}/stats")
