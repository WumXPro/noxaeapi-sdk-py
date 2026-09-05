from __future__ import annotations

import urllib.parse
from typing import List, Optional, Sequence

from ..http_engine import HttpEngine
from ..types import (
    LeaderboardEntry,
    LeaderboardSourceInfo,
    PlayerProfile,
    PlayerProfilesResponse,
)


def _q(value: str) -> str:
    return urllib.parse.quote(value, safe="")


class LeaderboardModule:
    """Wraps the generic, pluggable ``/v1/leaderboards/*`` routes.

    This is a unified view over every ranking source registered on the
    server — economy currencies, mcMMO power level, AuraSkills power
    level, etc — so you don't need to know ahead of time which plugins
    are installed.

    Use :meth:`list` to discover available source IDs, then pass one to
    :meth:`get_top`. Sources that are registered but currently
    unavailable (e.g. the backing plugin isn't loaded) raise
    ``NoxAeApiError`` with the source's own unavailable status (424 for
    economy currencies, 503 for mcMMO/AuraSkills) when you call
    :meth:`get_top`.

    This module also wraps the player-profile routes
    (``/v1/players/{uuid}/profile`` and ``/v1/players/profiles``), which live
    server-side alongside the leaderboard sources since they're built on top
    of them.
    """

    def __init__(self, http: HttpEngine) -> None:
        self._http = http

    def list(self) -> List[LeaderboardSourceInfo]:
        """List every registered leaderboard source and its availability."""
        return self._http.request("GET", "leaderboards")

    def get_top(self, id: str, limit: Optional[int] = None) -> List[LeaderboardEntry]:
        """Get ranked entries for one leaderboard source (see :meth:`list` for valid IDs)."""
        return self._http.request("GET", f"leaderboards/{_q(id)}/top", query={"limit": limit})

    def get_player_profile(self, uuid: str) -> PlayerProfile:
        """One-call player profile: identity, whitelist/ban status, Vault balance,
        and this player's entry in every registered leaderboard source. Built so
        clients never have to know how many leaderboard sources exist or scan
        top-N lists themselves.

        Raises ``NoxAeApiNotFoundError`` if no known player with that UUID has
        ever joined.
        """
        return self._http.request("GET", f"players/{_q(uuid)}/profile")

    def get_player_profiles(
        self,
        *,
        uuids: Optional[Sequence[str]] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        online_only: Optional[bool] = None,
    ) -> PlayerProfilesResponse:
        """Bulk player profiles — same shape as :meth:`get_player_profile`, for many
        players at once. Computes each leaderboard source's full ranking exactly
        once for the whole batch rather than once per player, so this is far
        cheaper than calling :meth:`get_player_profile` in a loop.

        Pass ``uuids`` to fetch an exact, specific set of players — unknown UUIDs
        are silently skipped rather than raising. Omit ``uuids`` to page through
        every known player instead, using ``page``/``limit``, optionally narrowed
        to only currently-online players via ``online_only``.
        """
        return self._http.request(
            "GET",
            "players/profiles",
            query={
                "uuids": ",".join(uuids) if uuids else None,
                "page": page,
                "limit": limit,
                "onlineOnly": online_only,
            },
        )
