from __future__ import annotations

import urllib.parse

from ..http_engine import HttpEngine
from ..types import NoxAuthPlayerInfo, PasswordCheckResult


def _q(value: str) -> str:
    return urllib.parse.quote(value, safe="")


class NoxAuthModule:
    """Wraps the ``/v1/noxauth/*`` routes.

    These only work when ``noxauth.enabled`` is set to ``true`` in the
    server's ``noxaeapi-config.yml`` and the NoxAuth plugin is installed.

    ``check_password``'s body is sent as real JSON (the server parses it
    with ``Gson...fromJson(ctx.body(), PasswordCheckRequest.class)``, not
    ``ctx.formParam(...)``) — it does not pass ``form=True``.
    """

    def __init__(self, http: HttpEngine) -> None:
        self._http = http

    def get_player_auth(self, name: str) -> NoxAuthPlayerInfo:
        """Get NoxAuth registration/auth info for a player by name."""
        return self._http.request("GET", f"noxauth/player/{_q(name)}")

    def check_password(self, name: str, password: str) -> PasswordCheckResult:
        """Check whether a password matches a player's stored NoxAuth password."""
        return self._http.request(
            "POST", f"noxauth/player/{_q(name)}/check-password", body={"password": password}
        )
