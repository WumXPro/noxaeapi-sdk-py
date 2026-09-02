from __future__ import annotations

from typing import List

from ..http_engine import HttpEngine
from ..types import Advancement


class AdvancementsModule:
    def __init__(self, http: HttpEngine) -> None:
        self._http = http

    def list(self) -> List[Advancement]:
        """List all advancements known to the server."""
        return self._http.request("GET", "advancements")


class PlaceholdersModule:
    def __init__(self, http: HttpEngine) -> None:
        self._http = http

    def replace(self, uuid: str, message: str) -> str:
        """Replace PlaceholderAPI-style placeholders (e.g. "%player_name%") in ``message`` for a player.

        Server-side this is ``PAPIApi.replacePlaceholders``, which reads
        form fields ``message`` and ``uuid`` — the field is literally
        named ``message``, not ``text``.
        """
        return self._http.request("POST", "placeholders/replace", body={"uuid": uuid, "message": message}, form=True)
