import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from noxaeapi_sdk import NoxAeApiClient, NoxAeApiNotFoundError, NoxAeApiUnauthorizedError
from noxaeapi_sdk.http_engine import NoxAeApiClientOptions


class FakeResponse:
    def __init__(self, status, body):
        self.status = status
        self._body = json.dumps(body).encode("utf-8") if body is not None else b""

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeHTTPError(Exception):
    def __init__(self, code, body):
        self.code = code
        self.fp = io.BytesIO(json.dumps(body).encode("utf-8"))
        self.headers = {}

    def read(self):
        return self.fp.read()


import urllib.error


def make_opener(responses):
    calls = []

    def opener(req, timeout):
        calls.append(req)
        status, body = responses.pop(0)
        if status >= 400:
            err = urllib.error.HTTPError(req.full_url, status, "err", {}, io.BytesIO(json.dumps(body).encode()))
            raise err
        return FakeResponse(status, body)

    return opener, calls


def test_players_list_ok():
    opener, calls = make_opener([(200, [{"uuid": "abc", "displayName": "Steve"}])])
    client = NoxAeApiClient(
        options=NoxAeApiClientOptions(base_url="http://localhost:8080", api_key="k", opener=opener, retry=False)
    )
    players = client.players.list()
    assert players[0]["uuid"] == "abc"
    assert calls[0].get_method() == "GET"
    assert calls[0].full_url == "http://localhost:8080/v1/players"
    assert calls[0].headers["Key"] == "k"


def test_404_raises_not_found():
    opener, _ = make_opener([(404, {"error": "not found"})])
    client = NoxAeApiClient(
        options=NoxAeApiClientOptions(base_url="http://localhost:8080", opener=opener, retry=False)
    )
    try:
        client.players.get("nope")
        assert False, "expected NoxAeApiNotFoundError"
    except NoxAeApiNotFoundError as e:
        assert e.status == 404


def test_401_raises_unauthorized():
    opener, _ = make_opener([(401, {"error": "unauthorized"})])
    client = NoxAeApiClient(
        options=NoxAeApiClientOptions(base_url="http://localhost:8080", opener=opener, retry=False)
    )
    try:
        client.server.info()
        assert False, "expected NoxAeApiUnauthorizedError"
    except NoxAeApiUnauthorizedError:
        pass


def test_form_encoding_for_pay():
    opener, calls = make_opener([(200, None)])
    client = NoxAeApiClient(
        options=NoxAeApiClientOptions(base_url="http://localhost:8080", opener=opener, retry=False)
    )
    client.economy.pay("uuid-1", 100)
    req = calls[0]
    assert req.headers["Content-type"] == "application/x-www-form-urlencoded"
    assert req.data == b"uuid=uuid-1&amount=100"


if __name__ == "__main__":
    test_players_list_ok()
    test_404_raises_not_found()
    test_401_raises_unauthorized()
    test_form_encoding_for_pay()
    print("All tests passed.")
