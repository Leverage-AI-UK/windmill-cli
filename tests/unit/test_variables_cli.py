from __future__ import annotations

import json

from wmx.cli import app
from wmx.state import AppState


class _FakeVariablesAPI:
    def get(self, path: str, *, decrypt_secret: bool = False, include_encrypted: bool = False):
        assert path == "u/me/secret"
        if decrypt_secret:
            return {"path": path, "is_secret": True, "value": "plaintext"}
        if include_encrypted:
            return {"path": path, "is_secret": True, "value": "encrypted-value"}
        return {"path": path, "is_secret": True, "value": "plaintext"}

    def list(self, *, path_start=None, page=1, per_page=50):
        return [{"path": "u/me/secret", "is_secret": True, "value": "secret"}]


class _FakeAPI:
    def __init__(self) -> None:
        self.variables = _FakeVariablesAPI()


def test_secret_variable_is_redacted_by_default(runner, monkeypatch) -> None:
    monkeypatch.setattr(AppState, "client", lambda self: _FakeAPI())
    result = runner.invoke(app, ["--json", "variables", "get", "u/me/secret"], terminal_width=100)
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["path"] == "u/me/secret"
    assert payload["value_redacted"] is True
    assert "value" not in payload


def test_secret_variable_can_be_revealed_explicitly(runner, monkeypatch) -> None:
    monkeypatch.setattr(AppState, "client", lambda self: _FakeAPI())
    result = runner.invoke(
        app,
        ["--json", "variables", "get", "u/me/secret", "--reveal", "--value-only"],
        terminal_width=100,
    )
    assert result.exit_code == 0
    assert json.loads(result.stdout) == "plaintext"

