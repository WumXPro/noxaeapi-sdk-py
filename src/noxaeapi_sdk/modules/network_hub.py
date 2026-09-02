from __future__ import annotations

import urllib.parse
from typing import Any, Dict, Optional

from ..http_engine import HttpEngine, Method, QueryValue
from ..types import (
    NetworkHubBroadcastResponse,
    NetworkHubFindPlayerResponse,
    NetworkHubNode,
    NetworkHubPlayersResponse,
    NetworkHubStatusResponse,
)


def _q(value: str) -> str:
    return urllib.parse.quote(value, safe="")


class NetworkHubModule:
    """Wraps the ``/v1/network/*`` routes exposed by the **NoxAeApi-Velocity** network hub.

    This is a separate plugin/process from NoxAeApi-main, run on the
    Velocity proxy and listening on its own port (``NetworkHubConfig``'s
    ``api-port``, distinct from any individual backend's own REST port).

    Point a :class:`~noxaeapi_sdk.client.NoxAeApiNetworkHubClient` (not
    the regular :class:`~noxaeapi_sdk.client.NoxAeApiClient`) at that
    port to use this module. Backend Paper/Bukkit servers connect out to
    the hub over WebSocket (``/network/register``) and push register /
    heartbeat / player-join / player-quit events; the hub answers every
    method below from its own in-memory registry, so calls here are
    cheap and don't block on a live round trip to each backend the way
    the older :class:`~noxaeapi_sdk.modules.network.NetworkModule`
    (NoxAeApi-main's built-in aggregator) does.

    Response shapes differ from ``NetworkModule`` even where the route
    names match — e.g. :meth:`players` returns one flat proxy-wide
    player list here, not a per-server breakdown — so the two modules'
    types aren't interchangeable. There's also no hub equivalent of
    ``/v1/network/health``; each node's last-reported health is embedded
    in :meth:`status_all`/:meth:`status_by_id`'s ``health`` field
    instead.
    """

    def __init__(self, http: HttpEngine) -> None:
        self._http = http

    def status_all(self) -> NetworkHubStatusResponse:
        """Get last-known status (from the registry) for every backend node that has ever registered."""
        return self._http.request("GET", "network/status")

    def status_by_id(self, id: str) -> NetworkHubNode:
        """Get last-known status for a single node by its configured ID."""
        return self._http.request("GET", f"network/status/{_q(id)}")

    def players(self) -> NetworkHubPlayersResponse:
        """List every player currently connected to the proxy, straight from Velocity's own registry."""
        return self._http.request("GET", "network/players")

    def find_player(self, uuid: str) -> NetworkHubFindPlayerResponse:
        """Find which backend server a player is currently on by UUID (proxy-authoritative)."""
        return self._http.request("GET", f"network/players/{_q(uuid)}")

    def broadcast(self, message: str) -> NetworkHubBroadcastResponse:
        """Broadcast a message directly to every player connected to the proxy.

        Unlike ``NetworkModule.broadcast``, this doesn't forward to each
        backend's ``/v1/chat/broadcast`` — the proxy already has every
        player in hand — so it still delivers even to servers with no
        REST API of their own reachable from the hub.
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
        """Forward an arbitrary request to a specific backend node's own REST API.

        E.g. ``hub.forward("survival", "POST", "server/exec",
        body={"command": "say hi"}, form=True)`` reaches that backend's
        ``POST /v1/server/exec`` directly. Useful for endpoints the hub
        doesn't have a dedicated method for (economy, worlds, etc)
        without instantiating a second client pointed at that backend
        directly.

        The target backend responds according to its own route's
        expected encoding (form vs JSON) — pass ``form=True`` the same
        way you would for a direct call to that endpoint.
        """
        return self._http.request(
            method, f"network/{_q(id)}/{path.lstrip('/')}", body=body, query=query, form=form
        )
