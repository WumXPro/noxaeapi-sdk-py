"""Response shape hints for the NoxAeApi REST API.

These are :class:`typing.TypedDict` definitions, not runtime-validated
models — every SDK method still just returns whatever JSON the server
sent, parsed into plain ``dict``/``list``/scalar values. The TypedDicts
exist purely so editors and type checkers (mypy/pyright) can give you
autocomplete and structural checks against the documented shapes.
"""

from __future__ import annotations

from typing import Any, List, Literal, Optional, Tuple, TypedDict, Union


class OnlinePlayer(TypedDict):
    uuid: str
    displayName: str
    address: Optional[str]
    port: Optional[int]
    exhaustion: float
    exp: float
    expLevel: int
    whitelisted: bool
    banned: bool
    op: bool
    balance: Optional[float]
    location: Optional[Tuple[float, float, float]]
    dimension: Optional[str]
    health: float
    hunger: int
    saturation: float
    gamemode: str
    lastPlayed: int
    authenticated: Optional[bool]
    registered: Optional[bool]


class OfflinePlayer(TypedDict):
    uuid: str
    displayName: str
    whitelisted: bool
    banned: bool
    op: bool
    balance: Optional[float]
    lastPlayed: int


class ServerHealth(TypedDict):
    cpus: int
    uptime: int
    totalMemory: int
    maxMemory: int
    freeMemory: int


class ServerBan(TypedDict):
    target: str
    source: Optional[str]
    reason: Optional[str]
    expiration: Optional[str]


class WhitelistEntry(TypedDict):
    uuid: str
    name: str


class ServerInfo(TypedDict):
    name: str
    motd: str
    version: str
    bukkitVersion: str
    tps: str
    health: ServerHealth
    bannedIps: List[ServerBan]
    bannedPlayers: List[ServerBan]
    whitelistedPlayers: List[WhitelistEntry]
    maxPlayers: int
    onlinePlayers: int


class World(TypedDict):
    name: str
    uuid: str
    time: int
    storm: bool
    thundering: bool
    generateStructures: bool
    allowAnimals: bool
    allowMonsters: bool
    difficulty: str
    environment: str
    seed: str


class Score(TypedDict):
    entry: str
    value: int


class Objective(TypedDict):
    name: str
    displayName: str
    criterion: str
    scores: List[Score]
    displaySlot: Optional[str]


class Scoreboard(TypedDict):
    objectives: List[str]
    entries: List[str]


class InventoryItem(TypedDict):
    id: str
    count: int
    slot: int


class Plugin(TypedDict):
    name: str
    enabled: bool
    version: str
    website: Optional[str]
    authors: List[str]
    depends: List[str]
    softDepends: List[str]
    apiVersion: Optional[str]
    description: Optional[str]


class EconomyInfo(TypedDict, total=False):
    available: bool


class PlayerBalance(TypedDict):
    uuid: str
    balance: float


class TopBalanceEntry(TypedDict):
    uuid: str
    balance: float


class GroupInfo(TypedDict):
    name: str
    permissions: List[str]


class PermissionNode(TypedDict):
    permission: str
    value: bool
    expiry: int
    server: Optional[str]
    world: Optional[str]


class Advancement(TypedDict):
    key: str
    criteria: List[str]


class NoxAuthPlayerInfo(TypedDict):
    uuid: str
    name: str
    registered: bool
    authenticated: bool
    lastIp: Optional[str]
    lastLoginTime: Optional[int]
    countryCode: Optional[str]
    countryName: Optional[str]


class PasswordCheckResult(TypedDict):
    name: str
    valid: bool


class PlayerStats(TypedDict):
    uuid: str
    name: str
    kills: int
    deaths: int
    playtime: int
    blocksPlaced: int
    blocksBroken: int


class SkillInfo(TypedDict):
    uuid: str
    skills: dict
    """Skill name -> level."""
    powerLevel: int


class CurrencyBalance(TypedDict):
    uuid: str
    name: Optional[str]
    currency: str
    balance: float


class CurrencyTopEntry(TypedDict):
    uuid: str
    name: str
    balance: float


class LeaderboardSourceInfo(TypedDict):
    id: str
    displayName: str
    available: bool
    onlineOnly: bool
    """True if this source can only rank currently-online players (e.g. mcMMO)."""


class LeaderboardEntry(TypedDict):
    uuid: str
    name: str
    value: float


class NetworkServerStatus(TypedDict):
    id: str
    label: str
    online: bool
    server: Optional[ServerInfo]
    players: List[OnlinePlayer]


class NetworkPlayersServerEntry(TypedDict):
    id: str
    label: str
    online: bool
    players: List[OnlinePlayer]


class NetworkPlayersResponse(TypedDict):
    total: int
    servers: List[NetworkPlayersServerEntry]


class NetworkFindPlayerResponse(TypedDict, total=False):
    found: bool
    server: str
    player: OnlinePlayer


class NetworkHealthServerEntry(TypedDict, total=False):
    id: str
    label: str
    online: bool
    tps: Any
    health: Any


class NetworkHealthResponse(TypedDict):
    servers: List[NetworkHealthServerEntry]


NetworkBroadcastResponse = dict
"""Per-server "success" | "error" result, keyed by network server ID."""


class NetworkHubNode(TypedDict):
    id: str
    label: str
    online: bool
    tps: str
    onlinePlayers: int
    maxPlayers: int
    health: Any
    """Opaque payload the backend reported in its last heartbeat."""
    lastHeartbeatAt: int
    """Unix epoch ms of the last heartbeat received, or 0 if never."""


class NetworkHubStatusResponse(TypedDict):
    network: List[NetworkHubNode]


class NetworkHubPlayer(TypedDict, total=False):
    uuid: str
    name: str
    server: str
    """Backend server ID the player is currently connected to, if known."""


class NetworkHubPlayersResponse(TypedDict):
    total: int
    players: List[NetworkHubPlayer]


class NetworkHubFindPlayerResponse(TypedDict, total=False):
    found: bool
    player: NetworkHubPlayer


class NetworkHubBroadcastResponse(TypedDict):
    delivered: int


Gamemode = Literal["survival", "creative", "adventure", "spectator"]
Weather = Literal["clear", "rain", "thunder"]
