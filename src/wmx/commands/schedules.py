from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from wmx.output import render_record, render_table
from wmx.state import get_state
from wmx.utils import confirm_or_abort, load_structured_file


app = typer.Typer(
    help=(
        "Manage schedules.\n\n"
        "Schedule definitions should use Windmill's 6-field cron format including seconds.\n"
    )
)


@app.command("list")
def list_schedules(
    ctx: typer.Context,
    path_start: Annotated[Optional[str], typer.Option(help="Filter by remote path prefix.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    per_page: Annotated[int, typer.Option(help="Items per page.")] = 50,
) -> None:
    state = get_state(ctx)
    items = state.client().schedules.list(path_start=path_start, page=page, per_page=per_page)
    state.output.emit(items, label="schedules", human_renderer=lambda payload: render_table(payload))


@app.command("get")
def get_schedule(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Remote schedule path.")],
) -> None:
    state = get_state(ctx)
    item = state.client().schedules.get(path)
    state.output.emit(item, label="schedule", human_renderer=lambda payload: render_record(payload))


@app.command("create")
def create_schedule(
    ctx: typer.Context,
    file: Annotated[Path, typer.Option("--file", exists=True, dir_okay=False, readable=True, help="Schedule JSON or YAML file.")],
) -> None:
    state = get_state(ctx)
    payload = load_structured_file(file)
    created = state.client().schedules.create(payload)
    state.output.emit({"result": created, "path": payload.get("path") if isinstance(payload, dict) else None}, label="schedule create")


@app.command("update")
def update_schedule(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Remote schedule path.")],
    file: Annotated[Path, typer.Option("--file", exists=True, dir_okay=False, readable=True, help="Schedule JSON or YAML file.")],
) -> None:
    state = get_state(ctx)
    payload = load_structured_file(file)
    updated = state.client().schedules.update(path, payload)
    state.output.emit({"path": path, "result": updated}, label="schedule update")


@app.command("delete")
def delete_schedule(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Remote schedule path.")],
    yes: Annotated[bool, typer.Option("--yes", help="Skip confirmation.")] = False,
) -> None:
    state = get_state(ctx)
    confirm_or_abort(yes=yes or state.yes, message=f"Delete schedule {path}?")
    deleted = state.client().schedules.delete(path)
    state.output.emit({"path": path, "result": deleted}, label="schedule delete")
