from __future__ import annotations

import urllib.parse
from typing import Any, Dict, Optional

from ..http_engine import HttpEngine, Method, QueryValue
from ..types import (
    NetworkBroadcastResponse,
    NetworkFindPlayerResponse,
    NetworkHealthResponse,
    NetworkPlayersResponse,
    NetworkServerStatus,
)


def _q(value: str) -> str:
    return urllib.parse.quote(value, safe="")


class NetworkModule:
    """Wraps the ``/v1/network/*`` routes.

    These only exist when ``network.enabled: true`` is set in the
    server's config with at least one backend server configured —
    calling any method here against a server without the network
    aggregator enabled will 404.

    The aggregator fans requests out to every configured backend server
    (each with its own base URL + key) and merges the results, so a
    single call here can reflect the state of an entire network rather
    than just the server you connected to.
    """

    def __init__(self, http: HttpEngine) -> None:
        self._http = http

    def status_all(self) -> Dict[str, list]:
        """Get status (server info + online players) for every configured network server."""
        return self._http.request("GET", "network/status")

    def status_by_id(self, id: str) -> NetworkServerStatus:
        """Get status for a single network server by its configured ID."""
        return self._http.request("GET", f"network/status/{_q(id)}")

    def players(self) -> NetworkPlayersResponse:
        """Aggregate online players across every network server."""
        return self._http.request("GET", "network/players")

    def find_player(self, uuid: str) -> NetworkFindPlayerResponse:
        """Find which network server a player is currently on by UUID."""
        return self._http.request("GET", f"network/players/{_q(uuid)}")

    def health(self) -> NetworkHealthResponse:
        """Get aggregate health (TPS/memory) from every network server."""
        return self._http.request("GET", "network/health")

    def broadcast(self, message: str) -> NetworkBroadcastResponse:
        """Broadcast a message to every server on the network.

        Returns a map of server ID -> "success" | "error" (per-server
        delivery result; a network-wide failure is only raised for a
        malformed request).
        """
        return self._http.request("POST", "network/broadcast", body={"message": message}, form=True)

    def forward(
        self,
        id: str,
        method: Method,
        path: str,
        *,
        body: Any = None,
        query: Optional[Dict[str, QueryValue]] = None,
        form: bool = False,
    ) -> Any:
        """Forward an arbitrary request to a specific network server's own REST API.

        E.g. ``network.forward("survival", "POST", "server/exec",
        body={"command": "say hi"}, form=True)`` reaches that server's
        ``POST /v1/server/exec`` directly. Useful for endpoints the
        aggregator doesn't have a dedicated method for (economy, worlds,
        etc) on a specific server without instantiating a second client
        pointed at it.

        Note the target server responds according to its own route's
        expected encoding (form vs JSON) — pass ``form=True`` the same
        way you would for a direct call to that endpoint.
        """
        return self._http.request(
            method, f"network/{_q(id)}/{path.lstrip('/')}", body=body, query=query, form=form
        )
