"""Typed Python SDK for the NoxAeApi REST + WebSocket API.

(Fabric, Bukkit/Spigot/Paper) and the NoxAeApi-Velocity network hub.

Example::

    from noxaeapi_sdk import NoxAeApiClient

    client = NoxAeApiClient(base_url="http://localhost:8080", api_key="your-api-key")
    players = client.players.list()
    balance = client.economy.get_balance(players[0]["uuid"])
    client.server.broadcast("Hello from the SDK!")
"""

from .client import NoxAeApiClient, NoxAeApiNetworkHubClient
from .errors import (
    NoxAeApiError,
    NoxAeApiForbiddenError,
    NoxAeApiNetworkError,
    NoxAeApiNotFoundError,
    NoxAeApiRateLimitError,
    NoxAeApiServerError,
    NoxAeApiUnauthorizedError,
)
from .http_engine import NoxAeApiClientOptions, RetryOptions

__version__ = "0.4.0"

__all__ = [
    "NoxAeApiClient",
    "NoxAeApiNetworkHubClient",
    "NoxAeApiClientOptions",
    "RetryOptions",
    "NoxAeApiError",
    "NoxAeApiUnauthorizedError",
    "NoxAeApiForbiddenError",
    "NoxAeApiNotFoundError",
    "NoxAeApiRateLimitError",
    "NoxAeApiServerError",
    "NoxAeApiNetworkError",
]
