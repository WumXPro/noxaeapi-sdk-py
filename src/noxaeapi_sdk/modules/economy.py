from __future__ import annotations

import urllib.parse
from typing import List, Literal, Optional

from ..http_engine import HttpEngine
from ..types import CurrencyBalance, CurrencyTopEntry, EconomyInfo, PlayerBalance, TopBalanceEntry


def _q(value: str) -> str:
    return urllib.parse.quote(value, safe="")


class EconomyModule:
    def __init__(self, http: HttpEngine) -> None:
        self._http = http

    def info(self) -> EconomyInfo:
        """Get info about the connected economy provider (Impactor on Fabric, Vault on Bukkit/Spigot/Paper)."""
        return self._http.request("GET", "economy")

    def get_balance(self, uuid: str) -> PlayerBalance:
        """Get a player's balance."""
        return self._http.request("GET", f"economy/balance/{_q(uuid)}")

    def get_top_balance(self, limit: Optional[int] = None) -> List[TopBalanceEntry]:
        """Get the top balances leaderboard."""
        return self._http.request("GET", "economy/top", query={"limit": limit})

    def pay(self, uuid: str, amount: float) -> None:
        """Pay an amount to a player (adds to their balance)."""
        return self._http.request("POST", "economy/pay", body={"uuid": uuid, "amount": amount}, form=True)

    def debit(self, uuid: str, amount: float) -> None:
        """Debit an amount from a player (subtracts from their balance)."""
        return self._http.request("POST", "economy/debit", body={"uuid": uuid, "amount": amount}, form=True)

    # --- ExcellentEconomy multi-currency (native API, not Vault) ----------
    #
    # These endpoints talk directly to ExcellentEconomy's Developer API
    # rather than Vault, so they work with any currency configured on the
    # server (coins, gems, tokens, ...) instead of only the single
    # Vault-linked "primary" currency exposed above. They raise
    # `NoxAeApiError` with a 424 status if ExcellentEconomy isn't installed
    # on the target server, and a 404 if the given currency ID doesn't exist.

    def list_currencies(self) -> List[str]:
        """List all currency IDs configured on ExcellentEconomy."""
        return self._http.request("GET", "economy/currencies")

    def get_currency_balance(self, currency: str, uuid: str) -> CurrencyBalance:
        """Get a player's balance for a specific ExcellentEconomy currency."""
        return self._http.request("GET", f"economy/currency/{_q(currency)}/balance/{_q(uuid)}")

    def pay_currency(self, currency: str, uuid: str, amount: float) -> Literal["success", "failure"]:
        """Pay a player in a specific currency (adds ``amount``). ``amount`` must be > 0."""
        return self._http.request(
            "POST", f"economy/currency/{_q(currency)}/pay", body={"uuid": uuid, "amount": amount}, form=True
        )

    def debit_currency(self, currency: str, uuid: str, amount: float) -> Literal["success", "failure"]:
        """Debit a player in a specific currency (subtracts ``amount``). ``amount`` must be > 0."""
        return self._http.request(
            "POST", f"economy/currency/{_q(currency)}/debit", body={"uuid": uuid, "amount": amount}, form=True
        )

    def set_currency_balance(self, currency: str, uuid: str, amount: float) -> Literal["success", "failure"]:
        """Set a player's balance for a specific currency to an exact amount (``amount`` must be >= 0)."""
        return self._http.request(
            "POST", f"economy/currency/{_q(currency)}/set", body={"uuid": uuid, "amount": amount}, form=True
        )

    def get_currency_top(self, currency: str, limit: Optional[int] = None) -> List[CurrencyTopEntry]:
        """Get the top balances leaderboard for a specific currency."""
        return self._http.request("GET", f"economy/currency/{_q(currency)}/top", query={"limit": limit})
