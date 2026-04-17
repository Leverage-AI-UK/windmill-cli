from __future__ import annotations

from typing import Annotated, Optional

import typer

from wmx.errors import UsageError
from wmx.output import render_record, render_table
from wmx.state import get_state
from wmx.utils import confirm_or_abort, read_stdin_value, sanitize_variable


app = typer.Typer(
    help=(
        "Manage Windmill variables.\n\n"
        "Secret values are never shown by default. Use --reveal or --encrypted explicitly.\n"
    )
)


def _resolve_value(
    *,
    value: Optional[str],
    value_file: Optional[str],
    value_from_stdin: bool,
) -> str:
    sources = [value is not None, value_file is not None, value_from_stdin]
    if sum(bool(source) for source in sources) != 1:
        raise UsageError("Provide exactly one of --value, --value-file, or --value-from-stdin.")
    if value is not None:
        return value
    if value_file is not None:
        return open(value_file, "r", encoding="utf-8").read().rstrip("\n")
    return read_stdin_value()


@app.command("list")
def list_variables(
    ctx: typer.Context,
    path_start: Annotated[Optional[str], typer.Option(help="Filter by remote path prefix.")] = None,
    page: Annotated[int, typer.Option(help="Page number.")] = 1,
    per_page: Annotated[int, typer.Option(help="Items per page.")] = 50,
    query: Annotated[Optional[str], typer.Option(help="Keyword search in path and description.")] = None,
) -> None:
    state = get_state(ctx)
    items = state.client().variables.list(path_start=path_start, page=page, per_page=per_page)

    # Apply client-side keyword filtering if query specified
    if query:
        from wmx.search import search_items
        items = search_items(items, query, fields=["path", "description"])

    safe_items = [sanitize_variable(item) for item in items]
    state.output.emit(safe_items, label="variables", human_renderer=lambda payload: render_table(payload))


@app.command("get")
def get_variable(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Remote variable path.")],
    metadata_only: Annotated[bool, typer.Option(help="Show metadata only and omit the value.")] = False,
    reveal: Annotated[bool, typer.Option(help="Reveal the plaintext value when allowed.")] = False,
    encrypted: Annotated[bool, typer.Option(help="Return the encrypted value instead of plaintext for secrets.")] = False,
    value_only: Annotated[bool, typer.Option(help="Return only the value. Requires --reveal or --encrypted for secrets.")] = False,
) -> None:
    state = get_state(ctx)
    if metadata_only and value_only:
        raise UsageError("--metadata-only and --value-only cannot be used together.")
    if reveal and encrypted:
        raise UsageError("--reveal and --encrypted are mutually exclusive.")

    item = state.client().variables.get(
        path,
        decrypt_secret=reveal,
        include_encrypted=encrypted,
    )
    if value_only:
        if item.get("is_secret") and not (reveal or encrypted):
            raise UsageError("--value-only for secret variables requires --reveal or --encrypted.")
        state.output.emit(item.get("value"), label="variable value")
        return
    state.output.emit(
        sanitize_variable(item, reveal=reveal or encrypted, metadata_only=metadata_only),
        label="variable",
        human_renderer=lambda payload: render_record(payload),
    )


@app.command("create")
def create_variable(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Remote variable path.")],
    secret: Annotated[bool, typer.Option("--secret", help="Mark the variable as secret.")] = False,
    value: Annotated[Optional[str], typer.Option(help="Variable value.")] = None,
    value_file: Annotated[Optional[str], typer.Option(help="Read the variable value from a file.")] = None,
    value_from_stdin: Annotated[bool, typer.Option(help="Read the variable value from stdin.")] = False,
    description: Annotated[str, typer.Option(help="Description stored with the variable.")] = "",
    already_encrypted: Annotated[bool, typer.Option(help="Treat the input value as already encrypted by Windmill.")] = False,
) -> None:
    state = get_state(ctx)
    payload = {
        "path": path,
        "value": _resolve_value(value=value, value_file=value_file, value_from_stdin=value_from_stdin),
        "is_secret": secret,
        "description": description,
    }
    created = state.client().variables.create(payload, already_encrypted=already_encrypted)
    state.output.emit({"path": path, "result": created}, label="variable create")


@app.command("update")
def update_variable(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Remote variable path.")],
    secret: Annotated[Optional[bool], typer.Option("--secret/--no-secret", help="Override whether the variable is secret.")] = None,
    value: Annotated[Optional[str], typer.Option(help="Variable value.")] = None,
    value_file: Annotated[Optional[str], typer.Option(help="Read the variable value from a file.")] = None,
    value_from_stdin: Annotated[bool, typer.Option(help="Read the variable value from stdin.")] = False,
    description: Annotated[Optional[str], typer.Option(help="Updated description.")] = None,
    already_encrypted: Annotated[bool, typer.Option(help="Treat the input value as already encrypted by Windmill.")] = False,
) -> None:
    state = get_state(ctx)
    payload: dict[str, object] = {"path": path}
    if any([value is not None, value_file is not None, value_from_stdin]):
        payload["value"] = _resolve_value(value=value, value_file=value_file, value_from_stdin=value_from_stdin)
    if secret is not None:
        payload["is_secret"] = secret
    if description is not None:
        payload["description"] = description
    updated = state.client().variables.update(path, payload, already_encrypted=already_encrypted)
    state.output.emit({"path": path, "result": updated}, label="variable update")


@app.command("delete")
def delete_variable(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Remote variable path.")],
    yes: Annotated[bool, typer.Option("--yes", help="Skip confirmation.")] = False,
) -> None:
    state = get_state(ctx)
    confirm_or_abort(yes=yes or state.yes, message=f"Delete variable {path}?")
    deleted = state.client().variables.delete(path)
    state.output.emit({"path": path, "result": deleted}, label="variable delete")
