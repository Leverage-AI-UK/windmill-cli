from __future__ import annotations

from collections import deque

from wmx.client.jobs import JobsAPI


class _FakeHttp:
    workspace = "demo"

    def __init__(self) -> None:
        self.updates = deque(
            [
                {"new_logs": "hello\n", "log_offset": 6, "stream_offset": 0},
                {"new_logs": "", "log_offset": 6, "stream_offset": 0},
            ]
        )
        self.results = deque(
            [
                {"completed": False, "started": False, "success": False, "result": None},
                {"completed": True, "started": True, "success": True, "result": {"ok": True}},
            ]
        )

    def get_json(self, path: str, *, params=None):
        if "getupdate" in path:
            return self.updates.popleft()
        if "get_result_maybe" in path:
            return self.results.popleft()
        raise AssertionError(path)


def test_wait_polls_until_completed() -> None:
    api = JobsAPI(_FakeHttp())
    seen_logs: list[str] = []
    result = api.wait(
        "job-123",
        follow_logs=True,
        poll_interval=0.001,
        log_handler=seen_logs.append,
    )
    assert result.success is True
    assert result.result == {"ok": True}
    assert seen_logs == ["hello\n"]

