"""Exception hierarchy for the NoxAeApi SDK.

Every non-2xx HTTP response from a NoxAeApi server raises a subclass of
:class:`NoxAeApiError`. Network-level failures (DNS, connection refused,
timeouts) raise :class:`NoxAeApiNetworkError` instead, which is *not* a
subclass of :class:`NoxAeApiError` since no response was ever received.
"""

from __future__ import annotations

from typing import Any, Optional


class NoxAeApiError(Exception):
    """Base error for any non-2xx response from a NoxAeApi server.

    Prefer catching one of the more specific subclasses below when you
    need to branch on the failure reason.
    """

    def __init__(
        self,
        message: str,
        *,
        status: int,
        method: str,
        path: str,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.method = method
        self.path = path
        self.body = body

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"{type(self).__name__}(status={self.status}, method={self.method!r}, path={self.path!r})"


class NoxAeApiUnauthorizedError(NoxAeApiError):
    """401 — the API key is missing or not recognized by the server."""

    def __init__(self, *, status: int, method: str, path: str, body: Any = None) -> None:
        super().__init__(
            f"Unauthorized: the API key was missing or invalid for {method} {path}",
            status=status,
            method=method,
            path=path,
            body=body,
        )


class NoxAeApiForbiddenError(NoxAeApiError):
    """403 — the key is valid but isn't allowed to call this endpoint.

    This is a server-side permission decision (e.g. a read-only key
    hitting a write route); the SDK does not try to predict or enforce
    it client-side.
    """

    def __init__(self, *, status: int, method: str, path: str, body: Any = None) -> None:
        super().__init__(
            f"Forbidden: this API key does not have permission to call {method} {path}",
            status=status,
            method=method,
            path=path,
            body=body,
        )


class NoxAeApiNotFoundError(NoxAeApiError):
    """404 — the target resource (player, world, plugin, etc.) wasn't found."""

    def __init__(self, *, status: int, method: str, path: str, body: Any = None) -> None:
        super().__init__(
            f"Not found: {method} {path}",
            status=status,
            method=method,
            path=path,
            body=body,
        )


class NoxAeApiRateLimitError(NoxAeApiError):
    """429 — rate limited.

    ``retry_after_ms`` is populated when the server sends a
    ``Retry-After`` header. The SDK auto-retries these by default; this
    is only raised once retries are exhausted (or retries are disabled).
    """

    def __init__(
        self,
        *,
        status: int,
        method: str,
        path: str,
        body: Any = None,
        retry_after_ms: Optional[int] = None,
    ) -> None:
        suffix = f" — retry after {retry_after_ms}ms" if retry_after_ms else ""
        super().__init__(
            f"Rate limited on {method} {path}{suffix}",
            status=status,
            method=method,
            path=path,
            body=body,
        )
        self.retry_after_ms = retry_after_ms


class NoxAeApiServerError(NoxAeApiError):
    """5xx — the server errored out. Usually safe to retry, and auto-retried by default."""

    def __init__(self, *, status: int, method: str, path: str, body: Any = None) -> None:
        super().__init__(
            f"Server error ({status}) on {method} {path}",
            status=status,
            method=method,
            path=path,
            body=body,
        )


class NoxAeApiNetworkError(Exception):
    """The request could not complete at all (DNS, connection refused, timeout)."""

    def __init__(self, message: str, *, method: str, path: str, cause: Optional[BaseException] = None) -> None:
        super().__init__(message)
        self.method = method
        self.path = path
        self.__cause__ = cause
