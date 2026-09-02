"""Low-level HTTP engine shared by every module.

Zero third-party runtime dependencies — built on ``urllib`` from the
standard library, mirroring the zero-dependency ethos of the original
JS/TS SDK (which uses native ``fetch``).
"""

from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Union

from .errors import (
    NoxAeApiError,
    NoxAeApiForbiddenError,
    NoxAeApiNetworkError,
    NoxAeApiNotFoundError,
    NoxAeApiRateLimitError,
    NoxAeApiServerError,
    NoxAeApiUnauthorizedError,
)

Method = str  # "GET" | "POST" | "PUT" | "DELETE" | "PATCH"
QueryValue = Union[str, int, float, bool, None]


@dataclass
class RetryOptions:
    """Retry behavior for network errors, 429s, and 5xx responses."""

    attempts: int = 3
    """Max number of attempts including the first one. Default 3."""

    base_delay_ms: int = 300
    """Base delay in ms used for exponential backoff."""

    max_delay_ms: int = 5000
    """Upper bound for any single backoff delay."""


@dataclass
class NoxAeApiClientOptions:
    """Options accepted by :class:`NoxAeApiClient` / :class:`NoxAeApiNetworkHubClient`."""

    base_url: str
    """Base URL of the server, e.g. ``"http://localhost:8080"``."""

    api_key: Optional[str] = None
    """The API key configured on the server (sent as the ``key`` header)."""

    timeout: float = 10.0
    """Request timeout in seconds. Default 10."""

    retry: Union[RetryOptions, bool, None] = True
    """Retry options, ``True`` for defaults, or ``False`` to disable retries."""

    headers: Dict[str, str] = field(default_factory=dict)
    """Extra headers sent on every request."""

    opener: Optional[Callable[[urllib.request.Request, float], Any]] = None
    """Override the low-level opener, mainly for testing.

    Must be a callable ``(request, timeout) -> http.client.HTTPResponse``
    (or a context-manager-compatible object with the same interface as
    what ``urllib.request.urlopen`` returns). Defaults to
    ``urllib.request.urlopen``.
    """


def _resolve_retry(retry: Union[RetryOptions, bool, None]) -> Union[RetryOptions, None]:
    if retry is False or retry is None:
        return None
    if retry is True:
        return RetryOptions()
    return retry


def _sleep(seconds: float) -> None:
    if seconds > 0:
        time.sleep(seconds)


def _backoff_delay_seconds(attempt: int, opts: RetryOptions) -> float:
    exp = min(opts.max_delay_ms, opts.base_delay_ms * (2 ** attempt))
    # full jitter
    return (random.random() * exp) / 1000.0


def _encode_form_body(body: Any) -> bytes:
    """Encode a plain dict as ``application/x-www-form-urlencoded``.

    Matches what Javalin's ``ctx.formParam(name)`` reads server-side.
    ``None`` values are omitted so optional fields can be left out
    entirely rather than sent as the literal string "None".
    """
    params: list[tuple[str, str]] = []
    if isinstance(body, dict):
        for key, value in body.items():
            if value is None:
                continue
            if isinstance(value, bool):
                params.append((key, "true" if value else "false"))
            elif isinstance(value, (str, int, float)):
                params.append((key, str(value)))
            else:
                params.append((key, json.dumps(value)))
    return urllib.parse.urlencode(params).encode("utf-8")


def _safe_json_parse(text: Optional[str]) -> Any:
    if not text:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text


def _parse_retry_after(header_value: str) -> Optional[int]:
    try:
        return int(float(header_value) * 1000)
    except ValueError:
        pass
    try:
        from email.utils import parsedate_to_datetime

        dt = parsedate_to_datetime(header_value)
        if dt is None:
            return None
        delta_ms = (dt.timestamp() - time.time()) * 1000
        return max(0, int(delta_ms))
    except (TypeError, ValueError):
        return None


class HttpEngine:
    """Handles request building, encoding, retries, and error mapping."""

    def __init__(self, options: NoxAeApiClientOptions) -> None:
        if not options.base_url:
            raise ValueError("NoxAeApiClient requires a non-empty base_url")
        self._base_url = options.base_url.rstrip("/")
        self._api_key = options.api_key
        self._timeout = options.timeout
        self._retry = _resolve_retry(options.retry)
        self._extra_headers = dict(options.headers or {})
        self._opener = options.opener or (
            lambda req, timeout: urllib.request.urlopen(req, timeout=timeout)
        )

    def _build_url(self, path: str, query: Optional[Dict[str, QueryValue]] = None) -> str:
        url = f"{self._base_url}/v1/{path.lstrip('/')}"
        if query:
            filtered = {k: v for k, v in query.items() if v is not None}
            if filtered:
                url += "?" + urllib.parse.urlencode(filtered)
        return url

    def request(
        self,
        method: Method,
        path: str,
        *,
        body: Any = None,
        query: Optional[Dict[str, QueryValue]] = None,
        form: bool = False,
    ) -> Any:
        """Perform a request and return the parsed JSON body (or ``None`` for empty/204 responses)."""
        url = self._build_url(path, query)
        max_attempts = self._retry.attempts if self._retry else 1

        last_error: Optional[BaseException] = None

        for attempt in range(max_attempts):
            headers: Dict[str, str] = {"Accept": "application/json", **self._extra_headers}
            if self._api_key:
                headers["key"] = self._api_key

            data: Optional[bytes] = None
            if body is not None:
                if form:
                    headers["Content-Type"] = "application/x-www-form-urlencoded"
                    data = _encode_form_body(body)
                else:
                    headers["Content-Type"] = "application/json"
                    data = json.dumps(body).encode("utf-8")

            req = urllib.request.Request(url, data=data, headers=headers, method=method)

            try:
                with self._opener(req, self._timeout) as response:
                    status = response.status
                    raw = response.read()
                    text = raw.decode("utf-8") if raw else ""
                    if status == 204 or not text:
                        return None
                    return json.loads(text)

            except urllib.error.HTTPError as http_err:
                error_text = http_err.read().decode("utf-8", errors="replace") if http_err.fp else None
                parsed_body = _safe_json_parse(error_text)
                status = http_err.code
                info = dict(status=status, method=method, path=path, body=parsed_body)

                if status == 401:
                    raise NoxAeApiUnauthorizedError(**info) from None
                if status == 403:
                    raise NoxAeApiForbiddenError(**info) from None
                if status == 404:
                    raise NoxAeApiNotFoundError(**info) from None

                if status == 429:
                    retry_after_header = http_err.headers.get("Retry-After") if http_err.headers else None
                    retry_after_ms = _parse_retry_after(retry_after_header) if retry_after_header else None
                    err = NoxAeApiRateLimitError(retry_after_ms=retry_after_ms, **info)
                    if self._retry and attempt < max_attempts - 1:
                        last_error = err
                        _sleep((retry_after_ms / 1000.0) if retry_after_ms else _backoff_delay_seconds(attempt, self._retry))
                        continue
                    raise err from None

                if status >= 500:
                    err = NoxAeApiServerError(**info)
                    if self._retry and attempt < max_attempts - 1:
                        last_error = err
                        _sleep(_backoff_delay_seconds(attempt, self._retry))
                        continue
                    raise err from None

                raise NoxAeApiError(f"Unexpected status {status} on {method} {path}", **info) from None

            except NoxAeApiError:
                raise

            except Exception as err:  # noqa: BLE001 - network/timeout/DNS errors of many types
                is_timeout = isinstance(err, TimeoutError) or "timed out" in str(err).lower()
                message = (
                    f"Request timed out after {self._timeout}s: {method} {path}"
                    if is_timeout
                    else f"Network error on {method} {path}: {err}"
                )
                network_err = NoxAeApiNetworkError(message, method=method, path=path, cause=err)

                if self._retry and attempt < max_attempts - 1:
                    last_error = network_err
                    _sleep(_backoff_delay_seconds(attempt, self._retry))
                    continue
                raise network_err from err

        # Unreachable in practice.
        if isinstance(last_error, BaseException):
            raise last_error
        raise RuntimeError("Request failed after retries")
