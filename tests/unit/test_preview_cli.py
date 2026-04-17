from __future__ import annotations

import json

from wmx.cli import app
from wmx.client.jobs import WaitResult
from wmx.state import AppState


class _FakeScriptsAPI:
    def preview(self, payload):
        assert payload["args"] == {"customer_id": "123"}
        assert payload["language"] == "python3"
        return "job-123"


class _FakeJobsAPI:
    def wait(self, job_id, *, follow_logs=False, poll_interval=1.0, timeout=None, log_handler=None):
        assert job_id == "job-123"
        return WaitResult(job_id=job_id, success=True, started=True, result={"ok": True})


class _FakeAPI:
    def __init__(self) -> None:
        self.scripts = _FakeScriptsAPI()
        self.jobs = _FakeJobsAPI()


def test_preview_wait_returns_result_json(runner, monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(AppState, "client", lambda self: _FakeAPI())
    script = tmp_path / "preview.py"
    script.write_text("def main(customer_id: str):\n    return {'ok': True}\n", encoding="utf-8")
    result = runner.invoke(
        app,
        ["--json", "scripts", "preview", str(script), "--data", '{"customer_id":"123"}'],
        terminal_width=100,
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["job_id"] == "job-123"
    assert payload["result"] == {"ok": True}

