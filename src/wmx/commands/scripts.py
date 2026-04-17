from __future__ import annotations

from pathlib import Path
from typing import Annotated, List, Optional

import typer

from wmx.commands.common import emit_job_submission
from wmx.errors import UsageError
from wmx.output import render_record, render_table
from wmx.state import get_state
from wmx.utils import build_script_payload, confirm_or_abort, parse_json_input, parse_modules


app = typer.Typer(
    help=(
        "Manage deployed scripts and remote preview runs.\n\n"
        "Examples:\n"
        "  wmx scripts list --path-start f/team/\n"
        "  wmx scripts get f/team/send_report\n"
        "  wmx scripts create f/team/send_report --file ./send_report.py --language python3\n"
        "  wmx scripts run f/team/send_report --data @args.json --wait\n"
        "  wmx scripts preview ./scratch.py --data '{\"customer_id\":\"123\"}' --wait\n"
    )
)


@app.command("list")
def list_scripts(
    ctx: typer.Context,
    path_start: Annotated[Optional[str], typer.Option(help="Filter by remote path prefix.")] = None,
    page: Annotated[int, typer.Option(help="Page number for paginated API endpoints.")] = 1,
    per_page: Annotated[int, typer.Option(help="Items per page.")] = 50,
    languages: Annotated[Optional[str], typer.Option(help="Comma-separated language filter.")] = None,
) -> None:
    state = get_state(ctx)
    items = state.client().scripts.list(
        path_start=path_start,
        page=page,
        per_page=per_page,
        languages=languages,
    )
    state.output.emit(items, label="scripts", human_renderer=lambda payload: render_table(payload))


@app.command("get")
def get_script(
    ctx: typer.Context,
    identifier: Annotated[str, typer.Argument(help="Remote script path by default, or a script hash with --hash.")],
    by_hash: Annotated[bool, typer.Option("--hash", help="Interpret IDENTIFIER as a script hash.")] = False,
) -> None:
    state = get_state(ctx)
    item = state.client().scripts.get_by_hash(identifier) if by_hash else state.client().scripts.get(identifier)
    state.output.emit(item, label="script", human_renderer=lambda payload: render_record(payload))


@app.command("create")
def create_script(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Remote script path, for example f/team/my_script.")],
    file: Annotated[Path, typer.Option("--file", exists=True, dir_okay=False, readable=True, help="Local source file.")],
    language: Annotated[Optional[str], typer.Option(help="Windmill language. Inferred from file extension when possible.")] = None,
    summary: Annotated[Optional[str], typer.Option(help="Short human-readable script summary.")] = None,
    description: Annotated[Optional[str], typer.Option(help="Longer script description.")] = None,
    kind: Annotated[str, typer.Option(help="Script kind.", case_sensitive=False)] = "script",
    tag: Annotated[Optional[str], typer.Option(help="Worker tag to target a worker group.")] = None,
    deployment_message: Annotated[Optional[str], typer.Option(help="Deployment message stored in Windmill history.")] = None,
    draft_only: Annotated[bool, typer.Option(help="Create as draft only instead of deploying immediately.")] = False,
    module: Annotated[Optional[List[str]], typer.Option(help="Extra module as RELATIVE=FILE, repeatable.")] = None,
) -> None:
    state = get_state(ctx)
    payload = build_script_payload(
        path=path,
        file=file,
        language=language,
        summary=summary,
        description=description,
        kind=kind,
        tag=tag,
        deployment_message=deployment_message,
        draft_only=draft_only,
        modules=parse_modules(module or []),
    )
    created = state.client().scripts.create(payload)
    state.output.emit({"path": path, "hash": created}, label="script create")


@app.command("update")
def update_script(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Remote script path to update, for example f/team/my_script.")],
    file: Annotated[Path, typer.Option("--file", exists=True, dir_okay=False, readable=True, help="Local source file.")],
    language: Annotated[Optional[str], typer.Option(help="Windmill language. Inferred from file extension when possible.")] = None,
    summary: Annotated[Optional[str], typer.Option(help="Short human-readable script summary.")] = None,
    description: Annotated[Optional[str], typer.Option(help="Longer script description.")] = None,
    tag: Annotated[Optional[str], typer.Option(help="Worker tag to target a worker group.")] = None,
    deployment_message: Annotated[Optional[str], typer.Option(help="Deployment message stored in Windmill history.")] = None,
    module: Annotated[Optional[List[str]], typer.Option(help="Extra module as RELATIVE=FILE, repeatable.")] = None,
) -> None:
    state = get_state(ctx)
    payload = build_script_payload(
        path=path,
        file=file,
        language=language,
        summary=summary,
        description=description,
        kind="script",
        tag=tag,
        deployment_message=deployment_message,
        draft_only=False,
        modules=parse_modules(module or []),
    )
    updated = state.client().scripts.update(path, payload)
    state.output.emit({"path": path, "hash": updated}, label="script update")


@app.command("delete")
def delete_script(
    ctx: typer.Context,
    identifier: Annotated[str, typer.Argument(help="Remote script path, or a hash with --hash.")],
    by_hash: Annotated[bool, typer.Option("--hash", help="Interpret IDENTIFIER as a script hash.")] = False,
    keep_captures: Annotated[bool, typer.Option(help="Keep captures when deleting by path.")] = False,
    yes: Annotated[bool, typer.Option("--yes", help="Skip the destructive action confirmation.")] = False,
) -> None:
    state = get_state(ctx)
    target = f"delete script {'hash' if by_hash else 'path'} {identifier}?"
    confirm_or_abort(yes=yes or state.yes, message=target)
    payload = state.client().scripts.delete_hash(identifier) if by_hash else state.client().scripts.delete_path(identifier, keep_captures=keep_captures)
    state.output.emit(payload, label="script delete")


@app.command("run")
def run_script(
    ctx: typer.Context,
    identifier: Annotated[str, typer.Argument(help="Remote script path by default, or a hash with --hash.")],
    data: Annotated[Optional[str], typer.Option("--data", "-d", help="Inline JSON, @file, or @- for stdin.")] = None,
    by_hash: Annotated[bool, typer.Option("--hash", help="Interpret IDENTIFIER as a script hash.")] = False,
    wait: Annotated[bool, typer.Option("--wait/--no-wait", help="Wait for the job to finish.")] = False,
    follow: Annotated[bool, typer.Option("--follow/--no-follow", help="Poll and stream logs to stderr while waiting.")] = False,
    timeout: Annotated[Optional[float], typer.Option(help="Maximum wait time in seconds.")] = None,
    poll_interval: Annotated[float, typer.Option(help="Polling interval in seconds while waiting.")] = 1.0,
) -> None:
    state = get_state(ctx)
    args = parse_json_input(data)
    job_id = state.client().scripts.run_hash(identifier, args) if by_hash else state.client().scripts.run_path(identifier, args)
    emit_job_submission(
        state,
        job_id=job_id,
        wait=wait,
        follow=follow,
        timeout=timeout,
        poll_interval=poll_interval,
        label="script run",
    )


@app.command("preview")
def preview_script(
    ctx: typer.Context,
    file: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True, help="Local source file to preview remotely.")],
    data: Annotated[Optional[str], typer.Option("--data", "-d", help="Inline JSON, @file, or @- for stdin.")] = None,
    language: Annotated[Optional[str], typer.Option(help="Windmill language. Inferred from file extension when possible.")] = None,
    wait: Annotated[bool, typer.Option("--wait/--no-wait", help="Wait for the preview to finish.")] = True,
    follow: Annotated[bool, typer.Option("--follow/--no-follow", help="Poll and stream logs to stderr while waiting.")] = False,
    timeout: Annotated[Optional[float], typer.Option(help="Maximum wait time in seconds.")] = None,
    poll_interval: Annotated[float, typer.Option(help="Polling interval in seconds while waiting.")] = 1.0,
    tag: Annotated[Optional[str], typer.Option(help="Worker tag for the preview job.")] = None,
    module: Annotated[Optional[List[str]], typer.Option(help="Extra module as RELATIVE=FILE, repeatable.")] = None,
) -> None:
    state = get_state(ctx)
    payload = {
        "content": file.read_text(encoding="utf-8"),
        "args": parse_json_input(data),
        "language": language or build_script_payload(
            path="preview",
            file=file,
            language=language,
            summary="preview",
            description=None,
            kind="script",
            tag=None,
            deployment_message=None,
            draft_only=False,
            modules=None,
        )["language"],
    }
    modules = parse_modules(module or [])
    if modules:
        payload["modules"] = modules
    if tag:
        payload["tag"] = tag
    job_id = state.client().scripts.preview(payload)
    emit_job_submission(
        state,
        job_id=job_id,
        wait=wait,
        follow=follow,
        timeout=timeout,
        poll_interval=poll_interval,
        label="script preview",
    )
