from __future__ import annotations

import urllib.parse
from typing import Any, Dict, List

from ..http_engine import HttpEngine
from ..types import Weather, World


def _q(value: str) -> str:
    return urllib.parse.quote(value, safe="")


class WorldsModule:
    def __init__(self, http: HttpEngine) -> None:
        self._http = http

    def list(self) -> List[World]:
        """List all worlds."""
        return self._http.request("GET", "worlds")

    def save_all(self) -> None:
        """Save all worlds to disk."""
        return self._http.request("POST", "worlds/save")

    def download_all(self) -> Dict[str, str]:
        """Get a download link/stream reference for all worlds."""
        return self._http.request("GET", "worlds/download")

    def get(self, uuid: str) -> World:
        """Get a single world by UUID."""
        return self._http.request("GET", f"worlds/{_q(uuid)}")

    def save(self, uuid: str) -> None:
        """Save a specific world to disk."""
        return self._http.request("POST", f"worlds/{_q(uuid)}/save")

    def download(self, uuid: str) -> Dict[str, str]:
        """Get a download link/stream reference for a specific world."""
        return self._http.request("GET", f"worlds/{_q(uuid)}/download")

    def set_time(self, uuid: str, time: int) -> None:
        """Set the in-game time for a world (0-24000)."""
        return self._http.request("POST", f"worlds/{_q(uuid)}/time", body={"time": time}, form=True)

    def set_weather(self, uuid: str, weather: Weather) -> None:
        """Set the weather for a world.

        Server-side (``WorldApi.setWorldWeather``) reads a single
        ``weather`` enum string — "clear" | "rain" | "thunder" — not
        separate storm/thundering booleans.
        """
        return self._http.request("POST", f"worlds/{_q(uuid)}/weather", body={"weather": weather}, form=True)

    def get_entities(self, uuid: str) -> Dict[str, Any]:
        """Get entity counts within a specific world."""
        return self._http.request("GET", f"worlds/{_q(uuid)}/entities")
