from __future__ import annotations

import urllib.parse
from typing import List, Optional

from ..http_engine import HttpEngine
from ..types import LeaderboardEntry, LeaderboardSourceInfo


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
    """

    def __init__(self, http: HttpEngine) -> None:
        self._http = http

    def list(self) -> List[LeaderboardSourceInfo]:
        """List every registered leaderboard source and its availability."""
        return self._http.request("GET", "leaderboards")

    def get_top(self, id: str, limit: Optional[int] = None) -> List[LeaderboardEntry]:
        """Get ranked entries for one leaderboard source (see :meth:`list` for valid IDs)."""
        return self._http.request("GET", f"leaderboards/{_q(id)}/top", query={"limit": limit})
