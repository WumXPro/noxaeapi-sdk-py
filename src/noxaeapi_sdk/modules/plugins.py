from __future__ import annotations

import urllib.parse
from typing import List

from ..http_engine import HttpEngine
from ..types import Plugin


def _q(value: str) -> str:
    return urllib.parse.quote(value, safe="")


class PluginsModule:
    def __init__(self, http: HttpEngine) -> None:
        self._http = http

    def list(self) -> List[Plugin]:
        """List all installed plugins/mods."""
        return self._http.request("GET", "plugins")

    def install(self, download_url: str) -> None:
        """Install a plugin by downloading it from a direct URL.

        This is a privileged endpoint — requires a write-enabled API key.
        Server-side (``PluginApi.installPlugin``) reads the form field
        ``downloadUrl``, not ``source``.
        """
        return self._http.request("POST", "plugins", body={"downloadUrl": download_url}, form=True)

    def enable(self, name: str) -> None:
        """Enable a plugin by name."""
        return self._http.request("POST", f"plugins/{_q(name)}/enable")

    def disable(self, name: str) -> None:
        """Disable a plugin by name."""
        return self._http.request("POST", f"plugins/{_q(name)}/disable")
