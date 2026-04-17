from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Callable

from wmx.client.http import HttpClient
from wmx.errors import UsageError


LogHandler = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class WaitResult:
    job_id: str
    success: bool
    started: bool
    result: Any


class JobsAPI:
    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def list_completed(self, *, page: int = 1, per_page: int = 50, success: bool | None = None) -> list[dict[str, Any]]:
        return self.http.get_json(
            f"/w/{self.http.workspace}/jobs/completed/list",
            params={"page": page, "per_page": per_page, "success": success},
        )

    def list_queue(self, *, page: int = 1, per_page: int = 50, running: bool | None = None) -> list[dict[str, Any]]:
        return self.http.get_json(
            f"/w/{self.http.workspace}/jobs/queue/list",
            params={"page": page, "per_page": per_page, "running": running},
        )

    def get(self, job_id: str, *, no_logs: bool = False, no_code: bool = False) -> dict[str, Any]:
        return self.http.get_json(
            f"/w/{self.http.workspace}/jobs_u/get/{job_id}",
            params={"no_logs": no_logs, "no_code": no_code},
        )

    def get_logs(self, job_id: str) -> str:
        return self.http.get_text(f"/w/{self.http.workspace}/jobs_u/get_logs/{job_id}")

    def get_update(
        self,
        job_id: str,
        *,
        log_offset: int = 0,
        stream_offset: int = 0,
        no_logs: bool = False,
    ) -> dict[str, Any]:
        return self.http.get_json(
            f"/w/{self.http.workspace}/jobs_u/getupdate/{job_id}",
            params={
                "log_offset": log_offset,
                "stream_offset": stream_offset,
                "no_logs": no_logs,
            },
        )

    def get_result_maybe(self, job_id: str) -> dict[str, Any]:
        return self.http.get_json(
            f"/w/{self.http.workspace}/jobs_u/completed/get_result_maybe/{job_id}",
            params={"get_started": True},
        )

    def wait(
        self,
        job_id: str,
        *,
        follow_logs: bool = False,
        poll_interval: float = 1.0,
        timeout: float | None = None,
        log_handler: LogHandler | None = None,
    ) -> WaitResult:
        if poll_interval <= 0:
            raise UsageError("--poll-interval must be greater than 0.")
        started_at = time.monotonic()
        log_offset = 0
        stream_offset = 0
        while True:
            if follow_logs:
                update = self.get_update(
                    job_id,
                    log_offset=log_offset,
                    stream_offset=stream_offset,
                )
                new_logs = update.get("new_logs") or ""
                if new_logs and log_handler:
                    log_handler(new_logs)
                log_offset = update.get("log_offset", log_offset)
                stream_offset = update.get("stream_offset", stream_offset)

            result = self.get_result_maybe(job_id)
            if result.get("completed"):
                return WaitResult(
                    job_id=job_id,
                    success=bool(result.get("success")),
                    started=bool(result.get("started")),
                    result=result.get("result"),
                )

            if timeout is not None and (time.monotonic() - started_at) >= timeout:
                raise UsageError(f"Timed out waiting for job {job_id}.")

            time.sleep(poll_interval)

