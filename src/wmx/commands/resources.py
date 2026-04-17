from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Optional

import typer

from wmx.errors import UsageError
from wmx.output import render_record, render_table
from wmx.state import get_state
from wmx.utils import confirm_or_abort, load_structured_file, sanitize_resource


app = typer.Typer(
    help=(
        "Manage Windmill resources.\n\n"
        "Resource values are redacted by default because resources often contain credentials.\n"
        "Pass --reveal explicitly when you really want the raw value.\n"
    )
)

types_app = typer.Typer(help="Inspect resource types.")
app.add_typer(types_app, name="types")


def _resource_payload(file: Path, *, path: str, resource_type: Optional[str]) -> dict[str, Any]:
    payload = load_structured_file(file)
    if isinstance(payload, dict) and {"path", "resource_type", "value"} & set(payload.keys()):
        payload = dict(payload)
    else:
        if not resource_type:
            raise UsageError(
                "--type is required when the file contains only a raw resource value.",
            )
        payload = {"value": payload, "resource_type": resource_type}
    payload["path"] = path
    if resource_type:
        payload["resource_type"] = resource_type
    return payload


@app.command("list")
def list_resources(
    ctx: typer.Context,
    path_start: Annotated[Optional[str], typer.Option(help="Filter by remote path prefix.")] = None,
    resource_type: Annotated[Optional[str], typer.Option("--type", help="Filter by resource type.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    per_page: Annotated[int, typer.Option(help="Items per page.")] = 50,
) -> None:
    state = get_state(ctx)
    items = state.client().resources.list(
        path_start=path_start,
        resource_type=resource_type,
        page=page,
        per_page=per_page,
    )
    safe_items = [sanitize_resource(item, reveal=False) for item in items]
    state.output.emit(safe_items, label="resources", human_renderer=lambda payload: render_table(payload))


@app.command("search")
def search_resources(
    ctx: typer.Context,
    query: Annotated[str, typer.Argument(help="Keywords to search for in resource paths.")],
    path_start: Annotated[Optional[str], typer.Option(help="Filter by remote path prefix.")] = None,
    resource_type: Annotated[Optional[str], typer.Option("--type", help="Filter by resource type.")] = None,
    limit: Annotated[int, typer.Option(help="Maximum number of results.")] = 50,
) -> None:
    """Search resources by keyword matching in path only (values may contain secrets)."""
    from wmx.search import search_items

    state = get_state(ctx)
    items = state.client().resources.list_search(
        path_start=path_start,
        resource_type=resource_type,
    )
    # Search path only - values often contain secrets
    results = search_items(
        items,
        query,
        fields=["path"],
        limit=limit,
    )
    summary = [{"path": r["path"]} for r in results]
    state.output.emit(summary, label="resource search", human_renderer=lambda payload: render_table(payload))


@app.command("get")
def get_resource(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Remote resource path.")],
    reveal: Annotated[bool, typer.Option(help="Reveal the raw resource value.")] = False,
    value_only: Annotated[bool, typer.Option(help="Return only the resource value. Requires --reveal.")] = False,
    interpolate: Annotated[bool, typer.Option(help="Return the interpolated resource value. Requires --value-only and --reveal.")] = False,
) -> None:
    state = get_state(ctx)
    if value_only and not reveal:
        raise UsageError("--value-only requires --reveal for resources.")
    if interpolate and not value_only:
        raise UsageError("--interpolate only applies to --value-only.")

    if value_only:
        value = state.client().resources.get_value(path, interpolate=interpolate)
        state.output.emit(value, label="resource value")
        return

    item = state.client().resources.get(path)
    state.output.emit(
        sanitize_resource(item, reveal=reveal),
        label="resource",
        human_renderer=lambda payload: render_record(payload),
    )


@app.command("create")
def create_resource(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Remote resource path.")],
    file: Annotated[Path, typer.Option("--file", exists=True, dir_okay=False, readable=True, help="Resource JSON or YAML file.")],
    resource_type: Annotated[Optional[str], typer.Option("--type", help="Override resource_type or provide one for raw value files.")] = None,
    update_if_exists: Annotated[bool, typer.Option(help="Create or update if the resource already exists.")] = False,
) -> None:
    state = get_state(ctx)
    payload = _resource_payload(file, path=path, resource_type=resource_type)
    created = state.client().resources.create(payload, update_if_exists=update_if_exists)
    state.output.emit({"path": path, "result": created}, label="resource create")


@app.command("update")
def update_resource(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Remote resource path.")],
    file: Annotated[Path, typer.Option("--file", exists=True, dir_okay=False, readable=True, help="Resource JSON or YAML file.")],
    resource_type: Annotated[Optional[str], typer.Option("--type", help="Override resource_type or provide one for raw value files.")] = None,
) -> None:
    state = get_state(ctx)
    payload = _resource_payload(file, path=path, resource_type=resource_type)
    updated = state.client().resources.update(path, payload)
    state.output.emit({"path": path, "result": updated}, label="resource update")


@app.command("delete")
def delete_resource(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Remote resource path.")],
    yes: Annotated[bool, typer.Option("--yes", help="Skip confirmation.")] = False,
) -> None:
    state = get_state(ctx)
    confirm_or_abort(yes=yes or state.yes, message=f"Delete resource {path}?")
    deleted = state.client().resources.delete(path)
    state.output.emit({"path": path, "result": deleted}, label="resource delete")


@types_app.command("list")
def list_resource_types(ctx: typer.Context) -> None:
    state = get_state(ctx)
    items = state.client().resources.list_types()
    state.output.emit(items, label="resource types", human_renderer=lambda payload: render_table(payload))
