from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Optional

import typer

from wmx.commands.common import emit_job_submission
from wmx.output import render_record, render_table
from wmx.state import get_state
from wmx.utils import confirm_or_abort, load_structured_file, parse_json_input


app = typer.Typer(
    help=(
        "Manage Windmill flows and flow previews.\n\n"
        "Examples:\n"
        "  wmx flows list --path-start f/team/\n"
        "  wmx flows get f/team/daily_sync\n"
        "  wmx flows create --file ./daily_sync.flow.yaml\n"
        "  wmx flows update f/team/daily_sync --file ./daily_sync.flow.yaml\n"
        "  wmx flows run f/team/daily_sync --data @payload.json --wait\n"
    )
)


def _load_flow_payload(file: Path, *, path_override: Optional[str] = None) -> dict[str, Any]:
    payload = load_structured_file(file)
    if not isinstance(payload, dict):
        payload = {"value": payload}
    if "value" not in payload:
        payload = {"value": payload}
    if path_override:
        payload["path"] = path_override
    return payload


@app.command("list")
def list_flows(
    ctx: typer.Context,
    path_start: Annotated[Optional[str], typer.Option(help="Filter by remote path prefix.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    per_page: Annotated[int, typer.Option(help="Items per page.")] = 50,
) -> None:
    state = get_state(ctx)
    items = state.client().flows.list(path_start=path_start, page=page, per_page=per_page)
    state.output.emit(items, label="flows", human_renderer=lambda payload: render_table(payload))


@app.command("get")
def get_flow(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Remote flow path.")],
) -> None:
    state = get_state(ctx)
    item = state.client().flows.get(path)
    state.output.emit(item, label="flow", human_renderer=lambda payload: render_record(payload))


@app.command("create")
def create_flow(
    ctx: typer.Context,
    file: Annotated[Path, typer.Option("--file", exists=True, dir_okay=False, readable=True, help="Flow JSON or YAML file.")],
    path: Annotated[Optional[str], typer.Option(help="Override the path inside the file.")] = None,
) -> None:
    state = get_state(ctx)
    payload = _load_flow_payload(file, path_override=path)
    created = state.client().flows.create(payload)
    state.output.emit({"version": created, "path": payload.get("path")}, label="flow create")


@app.command("update")
def update_flow(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Remote flow path.")],
    file: Annotated[Path, typer.Option("--file", exists=True, dir_okay=False, readable=True, help="Flow JSON or YAML file.")],
) -> None:
    state = get_state(ctx)
    payload = _load_flow_payload(file, path_override=path)
    updated = state.client().flows.update(path, payload)
    state.output.emit({"path": path, "result": updated}, label="flow update")


@app.command("delete")
def delete_flow(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Remote flow path.")],
    keep_captures: Annotated[bool, typer.Option(help="Keep captures when deleting the flow.")] = False,
    yes: Annotated[bool, typer.Option("--yes", help="Skip confirmation.")] = False,
) -> None:
    state = get_state(ctx)
    confirm_or_abort(yes=yes or state.yes, message=f"Delete flow {path}?")
    deleted = state.client().flows.delete(path, keep_captures=keep_captures)
    state.output.emit({"path": path, "result": deleted}, label="flow delete")


@app.command("run")
def run_flow(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Remote flow path.")],
    data: Annotated[Optional[str], typer.Option("--data", "-d", help="Inline JSON, @file, or @- for stdin.")] = None,
    wait: Annotated[bool, typer.Option("--wait/--no-wait", help="Wait for the flow job to finish.")] = False,
    follow: Annotated[bool, typer.Option("--follow/--no-follow", help="Poll and stream logs to stderr while waiting.")] = False,
    timeout: Annotated[Optional[float], typer.Option(help="Maximum wait time in seconds.")] = None,
    poll_interval: Annotated[float, typer.Option(help="Polling interval in seconds.")] = 1.0,
) -> None:
    state = get_state(ctx)
    job_id = state.client().flows.run(path, parse_json_input(data))
    emit_job_submission(
        state,
        job_id=job_id,
        wait=wait,
        follow=follow,
        timeout=timeout,
        poll_interval=poll_interval,
        label="flow run",
    )


@app.command("preview")
def preview_flow(
    ctx: typer.Context,
    file: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True, help="Flow JSON or YAML file.")],
    data: Annotated[Optional[str], typer.Option("--data", "-d", help="Inline JSON, @file, or @- for stdin.")] = None,
    wait: Annotated[bool, typer.Option("--wait/--no-wait", help="Wait for the preview to finish.")] = True,
    follow: Annotated[bool, typer.Option("--follow/--no-follow", help="Poll and stream logs to stderr while waiting.")] = False,
    timeout: Annotated[Optional[float], typer.Option(help="Maximum wait time in seconds.")] = None,
    poll_interval: Annotated[float, typer.Option(help="Polling interval in seconds.")] = 1.0,
) -> None:
    state = get_state(ctx)
    payload = _load_flow_payload(file)
    payload["args"] = parse_json_input(data)
    job_id = state.client().flows.preview(payload)
    emit_job_submission(
        state,
        job_id=job_id,
        wait=wait,
        follow=follow,
        timeout=timeout,
        poll_interval=poll_interval,
        label="flow preview",
    )
