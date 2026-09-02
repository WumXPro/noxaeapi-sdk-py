from __future__ import annotations

import os
from typing import Any, Optional

from .http_engine import HttpEngine, NoxAeApiClientOptions
from .modules.economy import EconomyModule
from .modules.leaderboard import LeaderboardModule
from .modules.luckperms import LuckPermsModule
from .modules.misc import AdvancementsModule, PlaceholdersModule
from .modules.network import NetworkModule
from .modules.network_hub import NetworkHubModule
from .modules.noxauth import NoxAuthModule
from .modules.players import PlayersModule
from .modules.plugins import PluginsModule
from .modules.server import ServerModule
from .modules.skills import SkillsModule
from .modules.worlds import WorldsModule


class NoxAeApiClient:
    """Client for a NoxAeApi server (Fabric mod or Bukkit/Spigot/Paper plugin).

    Example::

        client = NoxAeApiClient(base_url="http://localhost:8080", api_key="your-api-key")
        players = client.players.list()
        balance = client.economy.get_balance(players[0]["uuid"])
        client.server.broadcast("Hello from the SDK!")
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        *,
        options: Optional[NoxAeApiClientOptions] = None,
        **kwargs: Any,
    ) -> None:
        """Create a client.

        Either pass ``base_url`` (and optionally ``api_key``,
        ``timeout``, ``retry``, ``headers``, ...) directly, or build a
        :class:`~noxaeapi_sdk.http_engine.NoxAeApiClientOptions` yourself
        and pass it as ``options=``.
        """
        if options is None:
            if not base_url:
                raise ValueError("NoxAeApiClient requires base_url (or options=NoxAeApiClientOptions(...))")
            options = NoxAeApiClientOptions(base_url=base_url, api_key=api_key, **kwargs)

        self._options = options
        self._http = HttpEngine(options)

        self.players = PlayersModule(self._http)
        self.economy = EconomyModule(self._http)
        self.server = ServerModule(self._http)
        self.worlds = WorldsModule(self._http)
        self.plugins = PluginsModule(self._http)
        self.advancements = AdvancementsModule(self._http)
        self.placeholders = PlaceholdersModule(self._http)
        self.luckperms = LuckPermsModule(self._http)
        """Only works if LuckPerms is loaded on the target server."""
        self.noxauth = NoxAuthModule(self._http)
        """Only works if ``noxauth.enabled: true`` is set in the server config."""
        self.skills = SkillsModule(self._http)
        """Requires mcMMO and/or AuraSkills to be loaded on the target server."""
        self.leaderboards = LeaderboardModule(self._http)
        """Generic ranked leaderboards (economy currencies, mcMMO, AuraSkills, ...)."""
        self.network = NetworkModule(self._http)
        """Only works if ``network.enabled: true`` is set in the server config.

        This is NoxAeApi-main's built-in polling aggregator — it lives on
        the *same* backend server you're already connected to and fans
        requests out to the other backends listed in that server's own
        config. If the network is running NoxAeApi-Velocity instead, use
        :class:`NoxAeApiNetworkHubClient` (pointed at the proxy's hub
        port) rather than this module — the hub replaces this aggregator
        with a push model and its response shapes differ.
        """

    @classmethod
    def from_env(cls, **overrides: Any) -> "NoxAeApiClient":
        """Build a client from environment variables: ``NOXAEAPI_BASE_URL`` and ``NOXAEAPI_KEY``.

        Convenience for scripts. The SDK never reads ``.env`` files or
        ``os.environ`` implicitly outside of this method — use a library
        like ``python-dotenv`` in your own app if you want that, then
        call ``NoxAeApiClient.from_env()`` after it's loaded.
        """
        base_url = overrides.pop("base_url", None) or os.environ.get("NOXAEAPI_BASE_URL")
        api_key = overrides.pop("api_key", None) or os.environ.get("NOXAEAPI_KEY")

        if not base_url:
            raise ValueError(
                "NoxAeApiClient.from_env(): NOXAEAPI_BASE_URL is not set and no base_url override was given."
            )

        return cls(base_url=base_url, api_key=api_key, **overrides)

    def connect(self, route: str = "events", **kwargs: Any) -> Any:
        """Open a WebSocket connection to the server (console tail or event stream).

        Requires the optional ``websocket-client`` package
        (``pip install noxaeapi-sdk[ws]``).
        """
        from .socket import NoxAeApiSocket, NoxAeApiWsOptions

        return NoxAeApiSocket(
            NoxAeApiWsOptions(
                base_url=self._options.base_url,
                api_key=self._options.api_key,
                route=route,
                **kwargs,
            )
        )


class NoxAeApiNetworkHubClient:
    """Client for the **NoxAeApi-Velocity** network hub.

    This is a separate plugin that runs on the Velocity proxy, not on any
    individual backend server. Point ``base_url`` at the hub's own REST
    port (``NetworkHubConfig``'s ``api-port``), not a backend's port, and
    use ``NOXAEAPI_HUB_*`` env vars (via :meth:`from_env`) if you keep
    that separate from a regular backend's ``NOXAEAPI_*`` vars.

    Only exposes ``.network`` — the hub doesn't run any of the other REST
    modules (players, economy, worlds, ...) that a backend
    :class:`NoxAeApiClient` does. To reach a specific backend's own
    routes through the hub, use ``hub.network.forward(id, ...)``.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        *,
        options: Optional[NoxAeApiClientOptions] = None,
        **kwargs: Any,
    ) -> None:
        if options is None:
            if not base_url:
                raise ValueError(
                    "NoxAeApiNetworkHubClient requires base_url (or options=NoxAeApiClientOptions(...))"
                )
            options = NoxAeApiClientOptions(base_url=base_url, api_key=api_key, **kwargs)

        http = HttpEngine(options)
        self.network = NetworkHubModule(http)
        """The network hub's aggregated view of every registered backend node."""

    @classmethod
    def from_env(cls, **overrides: Any) -> "NoxAeApiNetworkHubClient":
        """Build a hub client from environment variables: ``NOXAEAPI_HUB_BASE_URL`` / ``NOXAEAPI_HUB_KEY``.

        Same convenience as ``NoxAeApiClient.from_env()``, under separate
        env var names so a process can hold both a backend client and a
        hub client at once without the two colliding.
        """
        base_url = overrides.pop("base_url", None) or os.environ.get("NOXAEAPI_HUB_BASE_URL")
        api_key = overrides.pop("api_key", None) or os.environ.get("NOXAEAPI_HUB_KEY")

        if not base_url:
            raise ValueError(
                "NoxAeApiNetworkHubClient.from_env(): NOXAEAPI_HUB_BASE_URL is not set "
                "and no base_url override was given."
            )

        return cls(base_url=base_url, api_key=api_key, **overrides)
