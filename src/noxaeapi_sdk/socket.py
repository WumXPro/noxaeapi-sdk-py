"""Realtime console/event socket.

Requires the optional ``websocket-client`` dependency:

    pip install noxaeapi-sdk[ws]

The import is lazy — importing :mod:`noxaeapi_sdk` itself never requires
``websocket-client`` to be installed; only calling
:meth:`~noxaeapi_sdk.client.NoxAeApiClient.connect` does.
"""

from __future__ import annotations

import json
import random
import threading
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

Listener = Callable[[Any], None]

WS_EVENTS = ("open", "close", "error", "console", "event", "message")


def _to_ws_url(base_url: str, route: str, api_key: Optional[str] = None) -> str:
    parsed = urllib.parse.urlsplit(f"{base_url.rstrip('/')}/v1/ws/{route.lstrip('/')}")
    scheme = "wss" if parsed.scheme == "https" else "ws"
    query = dict(urllib.parse.parse_qsl(parsed.query))
    if api_key:
        query["key"] = api_key
    new_query = urllib.parse.urlencode(query)
    return urllib.parse.urlunsplit((scheme, parsed.netloc, parsed.path, new_query, ""))


@dataclass
class NoxAeApiWsOptions:
    """Options for :class:`NoxAeApiSocket`."""

    base_url: str
    api_key: Optional[str] = None
    route: str = "events"
    """Route suffix under the websocket base, e.g. "console" or "events"."""
    auto_reconnect: bool = True
    max_reconnect_delay: float = 30.0
    """Max reconnect delay in seconds."""
    extra: Dict[str, Any] = field(default_factory=dict)
    """Extra kwargs forwarded to ``websocket.WebSocketApp``."""


class NoxAeApiSocket:
    """Thin wrapper around the server's WebSocket endpoints (console tail and event broadcasts).

    Runs the connection on a background thread and handles reconnection
    with exponential backoff, so consumers can just attach listeners and
    not think about the socket lifecycle.

    Usage::

        ws = client.connect(route="console")
        ws.on("console", lambda line: print(line))
        ws.on("close", lambda _: print("disconnected"))
    """

    def __init__(self, options: NoxAeApiWsOptions) -> None:
        try:
            import websocket  # type: ignore[import-untyped]
        except ImportError as exc:  # pragma: no cover - exercised only when dep missing
            raise ImportError(
                "NoxAeApiSocket requires the optional 'websocket-client' package. "
                "Install it with: pip install noxaeapi-sdk[ws]"
            ) from exc

        self._websocket_module = websocket
        self._options = options
        self._listeners: Dict[str, Set[Listener]] = {event: set() for event in WS_EVENTS}
        self._reconnect_attempt = 0
        self._closed_by_user = False
        self._app: Optional[Any] = None
        self._thread: Optional[threading.Thread] = None
        self._open()

    # -- connection lifecycle -------------------------------------------------

    def _open(self) -> None:
        url = _to_ws_url(self._options.base_url, self._options.route, self._options.api_key)

        def on_open(_ws: Any) -> None:
            self._reconnect_attempt = 0
            self._emit("open", None)

        def on_message(_ws: Any, message: Any) -> None:
            text = message if isinstance(message, str) else message.decode("utf-8", errors="replace")
            parsed = _safe_parse(text)
            self._emit("message", parsed)
            if isinstance(parsed, dict) and parsed.get("type") in ("console", "event"):
                self._emit(parsed["type"], parsed)

        def on_error(_ws: Any, error: Any) -> None:
            self._emit("error", error)

        def on_close(_ws: Any, _status_code: Any, _msg: Any) -> None:
            self._emit("close", None)
            if not self._closed_by_user and self._options.auto_reconnect:
                self._schedule_reconnect()

        self._app = self._websocket_module.WebSocketApp(
            url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            **self._options.extra,
        )
        self._thread = threading.Thread(target=self._app.run_forever, daemon=True)
        self._thread.start()

    def _schedule_reconnect(self) -> None:
        max_delay = self._options.max_reconnect_delay
        delay = min(max_delay, 0.5 * (2 ** self._reconnect_attempt))
        self._reconnect_attempt += 1

        def _reconnect() -> None:
            time.sleep(delay)
            if not self._closed_by_user:
                self._open()

        threading.Thread(target=_reconnect, daemon=True).start()

    # -- listeners --------------------------------------------------------

    def on(self, event: str, listener: Listener) -> Callable[[], None]:
        """Register a listener for ``event``. Returns an unsubscribe callable."""
        if event not in self._listeners:
            self._listeners[event] = set()
        self._listeners[event].add(listener)
        return lambda: self._listeners.get(event, set()).discard(listener)

    def off(self, event: str, listener: Listener) -> None:
        self._listeners.get(event, set()).discard(listener)

    def _emit(self, event: str, payload: Any) -> None:
        for listener in list(self._listeners.get(event, set())):
            listener(payload)

    # -- send/close ---------------------------------------------------------

    def send(self, payload: Any) -> None:
        """Send a raw payload over the socket, JSON-encoded if not already a string."""
        if self._app is None or self._app.sock is None or not self._app.sock.connected:
            raise RuntimeError("Cannot send: socket is not open")
        data = payload if isinstance(payload, str) else json.dumps(payload)
        self._app.send(data)

    def close(self) -> None:
        """Close the socket and stop reconnecting."""
        self._closed_by_user = True
        if self._app is not None:
            self._app.close()


def _safe_parse(text: str) -> Any:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text
