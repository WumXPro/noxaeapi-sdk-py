from __future__ import annotations

import urllib.parse
from typing import Any, Dict, List, Optional

from ..http_engine import HttpEngine
from ..types import ServerInfo, WhitelistEntry


def _q(value: str) -> str:
    return urllib.parse.quote(value, safe="")


class ServerModule:
    def __init__(self, http: HttpEngine) -> None:
        self._http = http

    def ping(self) -> Dict[str, str]:
        """Basic liveness check."""
        return self._http.request("GET", "ping")

    def info(self) -> ServerInfo:
        """Get server info: version, MOTD, TPS, health, player counts, etc."""
        return self._http.request("GET", "server")

    def exec(self, command: str, wait_ms: Optional[int] = None) -> str:
        """Run a console command on the server, returning its console output.

        This is a privileged endpoint — requires a write-enabled API key.
        ``wait_ms`` is how long to wait for output before returning
        (server default 500ms if omitted). The server returns the joined
        output as a plain JSON string, not ``{"lines": [...]}``.
        """
        return self._http.request("POST", "server/exec", body={"command": command, "time": wait_ms}, form=True)

    def get_ops(self) -> List[WhitelistEntry]:
        """List server operators."""
        return self._http.request("GET", "server/ops")

    def op_player(self, uuid: str) -> None:
        """Grant operator status to a player.

        Server-side (``ServerApi.opPlayer``) reads the form field
        ``playerUuid``, not ``uuid`` — the field name matters here.
        """
        return self._http.request("POST", "server/ops", body={"playerUuid": uuid}, form=True)

    def deop_player(self, uuid: str) -> None:
        """Revoke operator status from a player.

        Server-side (``ServerApi.deopPlayer``) reads this from the query
        string (``playerUuid``), not the request body.
        """
        return self._http.request("DELETE", "server/ops", query={"playerUuid": uuid})

    def get_whitelist(self) -> List[WhitelistEntry]:
        """Get the current whitelist."""
        return self._http.request("GET", "server/whitelist")

    def add_to_whitelist(self, uuid: str, name: Optional[str] = None) -> None:
        """Add a player to the whitelist."""
        return self._http.request("POST", "server/whitelist", body={"uuid": uuid, "name": name}, form=True)

    def remove_from_whitelist(self, uuid: str) -> None:
        """Remove a player from the whitelist.

        Server-side (``ServerApi.whitelistDelete``) reads ``uuid``/``name``
        from the query string, not the request body.
        """
        return self._http.request("DELETE", "server/whitelist", query={"uuid": uuid})

    def restart(self) -> None:
        """Restart the server. This is a privileged endpoint — requires a write-enabled API key."""
        return self._http.request("POST", "server/restart")

    def get_logs(self, lines: Optional[int] = None) -> Dict[str, List[str]]:
        """Tail the server console log."""
        return self._http.request("GET", "server/logs", query={"lines": lines})

    def get_entities(self, world: Optional[str] = None) -> Dict[str, Any]:
        """Get entity counts on the server, optionally scoped to a world."""
        return self._http.request("GET", "server/entities", query={"world": world})

    def get_chunks(self, world: Optional[str] = None) -> Dict[str, Any]:
        """Get loaded chunk counts, optionally scoped to a world."""
        return self._http.request("GET", "server/chunks", query={"world": world})

    def ban_ip(self, ip: str, reason: Optional[str] = None) -> None:
        """Ban an IP address."""
        return self._http.request("POST", "server/ban-ip", body={"ip": ip, "reason": reason}, form=True)

    def get_objective(self, name: str) -> Any:
        """Get a scoreboard objective's scores by objective name."""
        return self._http.request("GET", f"scoreboard/{_q(name)}")

    def get_scoreboard(self) -> Any:
        """List all scoreboard objectives and tracked entries."""
        return self._http.request("GET", "scoreboard")

    def set_score(self, objective: str, entry: str, value: int) -> None:
        """Set a score for an entry on an objective."""
        return self._http.request(
            "POST", f"scoreboard/{_q(objective)}/score", body={"entry": entry, "value": value}, form=True
        )

    def reset_score(self, objective: str, entry: str) -> None:
        """Reset (remove) a score for an entry on an objective.

        Server-side (``ServerApi.resetScore``) reads ``entry`` from the
        query string, not the request body.
        """
        return self._http.request("DELETE", f"scoreboard/{_q(objective)}/score", query={"entry": entry})

    def broadcast(self, message: str) -> None:
        """Broadcast a message to every player on the server."""
        return self._http.request("POST", "chat/broadcast", body={"message": message}, form=True)

    def tell(self, uuid: str, message: str) -> None:
        """Send a private message to a specific player.

        Server-side (``ServerApi.tellPost``) reads the form field
        ``playerUuid``, not ``uuid``.
        """
        return self._http.request(
            "POST", "chat/tell", body={"playerUuid": uuid, "message": message}, form=True
        )
