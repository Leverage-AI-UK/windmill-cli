from __future__ import annotations

from pathlib import Path

from wmx.cli import app


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "help"


def _normalize(value: str) -> str:
    return value.replace("\r\n", "\n")


def test_root_help_matches_fixture(runner) -> None:
    result = runner.invoke(app, ["--help"], terminal_width=100, env={"NO_COLOR": "1"})
    assert result.exit_code == 0
    expected = (FIXTURES / "root.txt").read_text(encoding="utf-8")
    assert _normalize(result.stdout) == _normalize(expected)


def test_scripts_help_matches_fixture(runner) -> None:
    result = runner.invoke(app, ["scripts", "--help"], terminal_width=100, env={"NO_COLOR": "1"})
    assert result.exit_code == 0
    expected = (FIXTURES / "scripts.txt").read_text(encoding="utf-8")
    assert _normalize(result.stdout) == _normalize(expected)

