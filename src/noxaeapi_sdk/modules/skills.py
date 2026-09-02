from __future__ import annotations

import urllib.parse

from ..http_engine import HttpEngine
from ..types import SkillInfo


def _q(value: str) -> str:
    return urllib.parse.quote(value, safe="")


class SkillsModule:
    """Wraps the ``/v1/skills/*`` routes (mcMMO / AuraSkills)."""

    def __init__(self, http: HttpEngine) -> None:
        self._http = http

    def get_mcmmo_skills(self, uuid: str) -> SkillInfo:
        """Get mcMMO skill levels and power level for a player.

        Only works for **online** players — mcMMO's public ExperienceAPI
        has no offline lookup, so this raises ``NoxAeApiNotFoundError`` if
        the player isn't currently connected, and ``NoxAeApiServerError``
        (503) if mcMMO isn't loaded on the target server.
        """
        return self._http.request("GET", f"skills/mcmmo/player/{_q(uuid)}")

    def get_aura_skills(self, uuid: str) -> SkillInfo:
        """Get AuraSkills skill levels and power level for a player.

        Works for offline players. Raises ``NoxAeApiServerError`` (503)
        if AuraSkills isn't loaded on the target server.
        """
        return self._http.request("GET", f"skills/auraskills/player/{_q(uuid)}")
