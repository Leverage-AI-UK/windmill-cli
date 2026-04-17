from __future__ import annotations

from typing import Annotated, Optional

import typer

from wmx.commands.common import emit_job_submission
from wmx.output import render_record, render_table
from wmx.state import get_state


app = typer.Typer(
    help=(
        "Inspect and wait on Windmill jobs.\n\n"
        "Examples:\n"
        "  wmx jobs list --per-page 20\n"
        "  wmx jobs get 1c86...-...-...\n"
        "  wmx jobs wait 1c86...-...-... --follow\n"
    )
)


@app.command("list")
def list_jobs(
    ctx: typer.Context,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    per_page: Annotated[int, typer.Option(help="Items per page.")] = 50,
    success: Annotated[Optional[bool], typer.Option(help="Filter completed jobs by success.")] = None,
    script_path: Annotated[Optional[str], typer.Option(help="Filter by exact script path.")] = None,
    script_path_start: Annotated[Optional[str], typer.Option(help="Filter by script path prefix.")] = None,
    schedule_path: Annotated[Optional[str], typer.Option(help="Filter by schedule path.")] = None,
    created_by: Annotated[Optional[str], typer.Option(help="Filter by user who created the job.")] = None,
    tag: Annotated[Optional[str], typer.Option(help="Filter by worker tag.")] = None,
    label: Annotated[Optional[str], typer.Option(help="Filter by job label.")] = None,
    args: Annotated[Optional[str], typer.Option(help="JSON subset filter for job arguments.")] = None,
    result: Annotated[Optional[str], typer.Option(help="JSON subset filter for job results.")] = None,
    created_after: Annotated[Optional[str], typer.Option(help="Filter jobs created after this ISO datetime.")] = None,
    created_before: Annotated[Optional[str], typer.Option(help="Filter jobs created before this ISO datetime.")] = None,
) -> None:
    state = get_state(ctx)
    items = state.client().jobs.list_completed(
        page=page,
        per_page=per_page,
        success=success,
        script_path_exact=script_path,
        script_path_start=script_path_start,
        schedule_path=schedule_path,
        created_by=created_by,
        tag=tag,
        label=label,
        args=args,
        result=result,
        created_after=created_after,
        created_before=created_before,
    )
    state.output.emit(items, label="jobs", human_renderer=lambda payload: render_table(payload))


@app.command("get")
def get_job(
    ctx: typer.Context,
    job_id: Annotated[str, typer.Argument(help="Windmill job UUID.")],
    no_logs: Annotated[bool, typer.Option(help="Exclude logs from the job payload.")] = False,
    no_code: Annotated[bool, typer.Option(help="Exclude raw code from the job payload.")] = False,
) -> None:
    state = get_state(ctx)
    item = state.client().jobs.get(job_id, no_logs=no_logs, no_code=no_code)
    state.output.emit(item, label="job", human_renderer=lambda payload: render_record(payload))


@app.command("logs")
def get_job_logs(
    ctx: typer.Context,
    job_id: Annotated[str, typer.Argument(help="Windmill job UUID.")],
) -> None:
    state = get_state(ctx)
    logs = state.client().jobs.get_logs(job_id)
    state.output.emit(logs, label="job logs", file_stem=f"job-{job_id}-logs")


@app.command("wait")
def wait_job(
    ctx: typer.Context,
    job_id: Annotated[str, typer.Argument(help="Windmill job UUID.")],
    follow: Annotated[bool, typer.Option("--follow/--no-follow", help="Poll and stream logs to stderr while waiting.")] = False,
    timeout: Annotated[Optional[float], typer.Option(help="Maximum wait time in seconds.")] = None,
    poll_interval: Annotated[float, typer.Option(help="Polling interval in seconds.")] = 1.0,
) -> None:
    state = get_state(ctx)
    emit_job_submission(
        state,
        job_id=job_id,
        wait=True,
        follow=follow,
        timeout=timeout,
        poll_interval=poll_interval,
        label="job wait",
    )
