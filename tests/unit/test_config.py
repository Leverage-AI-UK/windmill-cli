from __future__ import annotations

from wmx.config import redact_secret, resolve_config


def test_flags_override_environment(monkeypatch) -> None:
    monkeypatch.setenv("WMX_BASE_URL", "https://env.example")
    resolved = resolve_config(
        base_url="https://flag.example",
        workspace="demo",
        token="token12345",
    )
    runtime = resolved.require_complete()
    assert runtime.base_url == "https://flag.example"
    assert resolved.base_url.source == "flag"


def test_alias_environment_variables_are_supported(monkeypatch) -> None:
    monkeypatch.setenv("WINDMILL_BASE_URL", "https://windmill.example")
    monkeypatch.setenv("WINDMILL_WORKSPACE", "demo")
    monkeypatch.setenv("WINDMILL_TOKEN", "secret-token")
    resolved = resolve_config(base_url=None, workspace=None, token=None)
    runtime = resolved.require_complete()
    assert runtime.workspace == "demo"
    assert runtime.token == "secret-token"
    assert resolved.base_url.source == "env:WINDMILL_BASE_URL"


def test_redact_secret_keeps_ends() -> None:
    assert redact_secret("abcdefgh12345678") == "abcd...5678"

