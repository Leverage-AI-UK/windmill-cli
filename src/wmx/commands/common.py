from __future__ import annotations

from typing import Any

import typer

from wmx.errors import WmxError
from wmx.state import AppState


def emit_job_submission(
    state: AppState,
    *,
    job_id: str,
    wait: bool,
    follow: bool,
    timeout: float | None,
    poll_interval: float,
    label: str,
) -> None:
    if not wait:
        state.output.emit({"job_id": job_id, "status": "queued"}, label=label, file_stem=label)
        return

    state.output.debug(f"Waiting for {label} job {job_id}")
    result = state.client().jobs.wait(
        job_id,
        follow_logs=follow,
        poll_interval=poll_interval,
        timeout=timeout,
        log_handler=lambda chunk: typer.echo(chunk, err=True, nl=False),
    )
    if not result.success:
        error_message = _extract_job_error(result.result)
        raise WmxError(f"Job {job_id} failed: {error_message}", exit_code=20)
    state.output.emit(
        {
            "job_id": job_id,
            "success": True,
            "result": result.result,
        },
        label=label,
        file_stem=label,
    )


def _extract_job_error(result: Any) -> str:
    if isinstance(result, dict):
        if "error" in result:
            return str(result["error"])
        if "message" in result:
            return str(result["message"])
    return str(result)

