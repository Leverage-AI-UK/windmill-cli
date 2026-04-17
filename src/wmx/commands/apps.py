from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from wmx.output import render_record, render_table
from wmx.state import get_state
from wmx.utils import confirm_or_abort, load_structured_file


app = typer.Typer(
    help=(
        "Manage Windmill apps.\n\n"
        "App payload files should contain the HTTP API request body, including value and policy.\n\n"
        "For raw apps (React/Svelte full-code apps), use the --raw flag. Raw apps require:\n"
        "  - value.files: Source files (/App.tsx, /index.tsx, /index.css, /package.json)\n"
        "  - value.data: {schema: 'app1', tables: []}\n"
        "  - value.runnables: Backend scripts (optional)\n"
    )
)


@app.command("list")
def list_apps(
    ctx: typer.Context,
    path_start: Annotated[Optional[str], typer.Option(help="Filter by remote path prefix.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    per_page: Annotated[int, typer.Option(help="Items per page.")] = 50,
) -> None:
    state = get_state(ctx)
    items = state.client().apps.list(path_start=path_start, page=page, per_page=per_page)
    state.output.emit(items, label="apps", human_renderer=lambda payload: render_table(payload))


@app.command("search")
def search_apps(
    ctx: typer.Context,
    query: Annotated[str, typer.Argument(help="Keywords to search for in app paths and definitions.")],
    path_start: Annotated[Optional[str], typer.Option(help="Filter by remote path prefix.")] = None,
    limit: Annotated[int, typer.Option(help="Maximum number of results.")] = 50,
) -> None:
    """Search apps by keyword matching in path and app definition."""
    from wmx.search import search_items

    state = get_state(ctx)
    items = state.client().apps.list_search(path_start=path_start)
    results = search_items(
        items,
        query,
        fields=["path", "value"],
        limit=limit,
    )
    summary = [{"path": r["path"]} for r in results]
    state.output.emit(summary, label="app search", human_renderer=lambda payload: render_table(payload))


@app.command("get")
def get_app(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Remote app path.")],
) -> None:
    state = get_state(ctx)
    item = state.client().apps.get(path)
    state.output.emit(item, label="app", human_renderer=lambda payload: render_record(payload))


@app.command("create")
def create_app(
    ctx: typer.Context,
    file: Annotated[Path, typer.Option("--file", exists=True, dir_okay=False, readable=True, help="App JSON or YAML file.")],
    raw: Annotated[bool, typer.Option("--raw", help="Create as raw app (React/Svelte). Required for full-code apps.")] = False,
) -> None:
    state = get_state(ctx)
    payload = load_structured_file(file)
    created = state.client().apps.create(payload, raw=raw)
    state.output.emit({"result": created, "path": payload.get("path") if isinstance(payload, dict) else None}, label="app create")


@app.command("update")
def update_app(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Remote app path.")],
    file: Annotated[Path, typer.Option("--file", exists=True, dir_okay=False, readable=True, help="App JSON or YAML file.")],
    raw: Annotated[bool, typer.Option("--raw", help="Update as raw app (React/Svelte). Required for full-code apps.")] = False,
) -> None:
    state = get_state(ctx)
    payload = load_structured_file(file)
    if isinstance(payload, dict):
        payload["path"] = path
    updated = state.client().apps.update(path, payload, raw=raw)
    state.output.emit({"path": path, "result": updated}, label="app update")


@app.command("delete")
def delete_app(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Remote app path.")],
    yes: Annotated[bool, typer.Option("--yes", help="Skip confirmation.")] = False,
) -> None:
    state = get_state(ctx)
    confirm_or_abort(yes=yes or state.yes, message=f"Delete app {path}?")
    deleted = state.client().apps.delete(path)
    state.output.emit({"path": path, "result": deleted}, label="app delete")
