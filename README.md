# noxaeapi-sdk

Typed Python SDK for [NoxAeApi](https://github.com/WumXPro/noxaeapi-sdk), a REST + WebSocket API plugin/mod for Minecraft servers — ships for both Fabric and Bukkit/Spigot/PaperMC. The REST surface is identical across platforms, so this SDK works against either without any platform-specific configuration.

Zero required runtime dependencies — uses only the Python standard library (`urllib`) for HTTP. The realtime socket needs one optional extra.

📖 **Docs:** [noxapi.noxlydev.xyz](https://noxapi.noxlydev.xyz)

## Install

```bash
pip install noxaeapi-sdk

# with realtime console/event socket support:
pip install "noxaeapi-sdk[ws]"
```

## Usage

```python
from noxaeapi_sdk import NoxAeApiClient

client = NoxAeApiClient(base_url="http://localhost:8080", api_key="your-api-key")

players = client.players.list()
balance = client.economy.get_balance(players[0]["uuid"])
client.server.broadcast("Hello from the SDK!")

# Multi-currency (ExcellentEconomy), leaderboards, and network aggregator:
coins = client.economy.get_currency_balance("coins", players[0]["uuid"])
top = client.leaderboards.get_top("mcmmo-power", limit=10)
network = client.network.status_all()
```

### From environment variables

```python
# Reads NOXAEAPI_BASE_URL and NOXAEAPI_KEY from os.environ.
# If you keep those in a .env file, load it yourself first (e.g. with
# python-dotenv) — the SDK never reads .env files or os.environ implicitly
# outside this method.
client = NoxAeApiClient.from_env()
```

### Realtime (console tail / events)

Requires the `ws` extra (`pip install "noxaeapi-sdk[ws]"`).

```python
ws = client.connect(route="console")
ws.on("console", lambda line: print(line))
ws.on("close", lambda _: print("disconnected"))
```

The socket runs on a background thread and auto-reconnects with exponential backoff on unexpected disconnects.

## Error handling

All non-2xx responses raise a subclass of `NoxAeApiError`:

- `NoxAeApiUnauthorizedError` — 401, missing/invalid API key
- `NoxAeApiForbiddenError` — 403, key valid but not permitted for this endpoint
- `NoxAeApiNotFoundError` — 404
- `NoxAeApiRateLimitError` — 429 (SDK auto-retries these by default; raised only once retries are exhausted)
- `NoxAeApiServerError` — 5xx (also auto-retried by default)
- `NoxAeApiNetworkError` — request never completed (timeout, DNS, connection refused)

```python
from noxaeapi_sdk import NoxAeApiForbiddenError

try:
    client.server.restart()
except NoxAeApiForbiddenError:
    print("This API key isn't allowed to restart the server.")
```

## Request encoding

The server is a Javalin app, and most endpoints read their body with `ctx.formParam(...)` — i.e. `application/x-www-form-urlencoded` — rather than JSON. The SDK follows the same split:

- **Form-urlencoded**: everything in `economy` (including the `economy.get_currency_balance`/`.pay_currency`/etc ExcellentEconomy methods), `players`, `server` (except `luckperms`/`noxauth`), `worlds`, `plugins`, `placeholders`, and `network.broadcast`.
- **JSON**: `client.luckperms.*` and `client.noxauth.check_password` only — these are read server-side with `ctx.bodyAsClass(...)`.
- **N/A (GET only)**: `client.leaderboards.*` and most of `client.network.*` are read-only.

If you're extending the SDK, check which encoding the corresponding Javalin handler uses before wiring up a new method, and pass `form=True` to `http.request(...)` if it's form-urlencoded (this is also the more common case). Getting this wrong won't raise a type error — the request just silently sends the wrong content type and the server won't see the field.

## Optional modules

Some modules only work depending on the target server's setup:

- `client.luckperms.*` — requires the LuckPerms mod to be loaded on the server
- `client.noxauth.*` — requires `noxauth.enabled: true` in the server's `noxaeapi-config.yml`
- `client.economy.get_currency_balance()`/`.pay_currency()`/`.debit_currency()`/`.set_currency_balance()`/`.get_currency_top()`/`.list_currencies()` — requires ExcellentEconomy (raises a 424 error if it isn't installed)
- `client.network.*` — requires `network.enabled: true` with at least one backend server configured in the server's config

Calling these against a server without the corresponding feature enabled will fail (typically 404).

## NoxAeApi-Velocity network hub

If your network runs the **NoxAeApi-Velocity** proxy plugin, use `NoxAeApiNetworkHubClient` instead of (or alongside) `NoxAeApiClient` — point it at the hub's own REST port, not a backend server's port. Backend servers push register/heartbeat updates to the hub over WebSocket, so hub calls answer from its in-memory registry rather than fanning out live requests the way `client.network.*` above does — and the response shapes differ accordingly (e.g. `players()` is one flat proxy-wide list, not a per-backend breakdown, and there's no hub equivalent of `network/health` — see each node's `health` field in `status_all()`/`status_by_id()` instead).

```python
from noxaeapi_sdk import NoxAeApiNetworkHubClient

hub = NoxAeApiNetworkHubClient(base_url="http://localhost:9090", api_key="your-hub-key")  # the hub's api-port, not a backend's port

status = hub.network.status_all()
players = hub.network.players()
found = hub.network.find_player(players["players"][0]["uuid"]) if players["players"] else None
hub.network.broadcast("Hello from the hub!")

# Reach a specific backend's own REST routes through the hub:
hub.network.forward("survival", "POST", "server/exec", body={"command": "say hi"}, form=True)
```

Or from environment variables (`NOXAEAPI_HUB_BASE_URL` / `NOXAEAPI_HUB_KEY`, kept separate from `NoxAeApiClient.from_env()`'s `NOXAEAPI_*` vars so a process can hold both clients at once):

```python
hub = NoxAeApiNetworkHubClient.from_env()
```

## Configuration

```python
from noxaeapi_sdk import NoxAeApiClient, RetryOptions

client = NoxAeApiClient(
    base_url="https://mc.example.com",
    api_key="...",
    timeout=10.0,  # per-request timeout in seconds, default 10
    retry=RetryOptions(
        attempts=3,        # total attempts including the first, default 3
        base_delay_ms=300,
        max_delay_ms=5000,
    ),
    # retry=False,         # disable retries entirely
    headers={"X-Extra": "..."},
)
```

## License

MIT
