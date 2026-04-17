from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from wmx.commands import apps, config_cmd, docs, flows, jobs, queue, resources, schedules, scripts, variables
from wmx.config import resolve_config
from wmx.errors import WmxError
from wmx.output import OutputManager, OutputOptions, render_record
from wmx.state import AppState, get_state


app = typer.Typer(
    help=(
        "Agent-native Windmill CLI.\n\n"
        "Use the Windmill HTTP API directly, keep output stable for automation, and spill large payloads to the filesystem when needed.\n\n"
        "Examples:\n"
        "  wmx --help\n"
        "  wmx whoami\n"
        "  wmx scripts list --json\n"
        "  wmx scripts preview ./scratch.py --data @args.json --wait\n"
        "  wmx resources get u/me/db --reveal --value-only --output-mode file --output-file ./db.json\n"
    ),
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)
app.info.name = "wmx"

app.add_typer(scripts.app, name="scripts")
app.add_typer(flows.app, name="flows")
app.add_typer(resources.app, name="resources")
app.add_typer(variables.app, name="variables")
app.add_typer(jobs.app, name="jobs")
app.add_typer(queue.app, name="queue")
app.add_typer(schedules.app, name="schedules")
app.add_typer(apps.app, name="apps")
app.add_typer(docs.app, name="docs")
app.add_typer(config_cmd.app, name="config")


@app.callback()
def main_callback(
    ctx: typer.Context,
    base_url: Annotated[Optional[str], typer.Option("--base-url", help="Windmill base URL, for example https://app.windmill.dev")] = None,
    workspace: Annotated[Optional[str], typer.Option("--workspace", help="Windmill workspace id.")] = None,
    token: Annotated[Optional[str], typer.Option("--token", help="Windmill user token.")] = None,
    json_mode: bool = typer.Option(False, "--json", help="Emit machine-friendly JSON to stdout."),
    quiet: bool = typer.Option(False, "--quiet", help="Reduce stderr diagnostics."),
    verbose: bool = typer.Option(False, "--verbose", help="Emit extra stderr diagnostics."),
    yes: bool = typer.Option(False, "--yes", help="Skip confirmations for destructive operations."),
    output_mode: Annotated[str, typer.Option(help="Output policy: inline, auto, or file.")] = "auto",
    output_file: Annotated[Optional[Path], typer.Option(help="Write the primary payload to this file.")] = None,
    spill_dir: Annotated[Path, typer.Option(help="Directory for automatically spilled payloads.")] = Path(".wmx-output"),
    spill_threshold_bytes: Annotated[int, typer.Option(help="Auto-spill payloads larger than this many bytes.")] = 131072,
) -> None:
    config = resolve_config(base_url=base_url, workspace=workspace, token=token)
    ctx.obj = AppState(
        config=config,
        output=OutputManager(
            OutputOptions(
                json_mode=json_mode,
                output_mode=output_mode,
                output_file=output_file,
                spill_dir=spill_dir,
                spill_threshold_bytes=spill_threshold_bytes,
                quiet=quiet,
                verbose=verbose,
            )
        ),
        yes=yes,
    )


@app.command("whoami")
def whoami(ctx: typer.Context) -> None:
    state = get_state(ctx)
    payload = {
        "version": state.client().auth.version(),
        "global": state.client().auth.global_whoami(),
        "workspace": state.client().auth.workspace_whoami(),
    }
    state.output.emit(payload, label="whoami", human_renderer=lambda item: render_record(item))


@app.command("doctor")
def doctor(ctx: typer.Context) -> None:
    state = get_state(ctx)
    payload = {
        "config": state.config.as_dict(),
        "version": state.client().auth.version(),
        "workspace_user": state.client().auth.workspace_whoami(),
    }
    state.output.emit(payload, label="doctor", human_renderer=lambda item: render_record(item))


def main() -> None:
    import sys
    try:
        app()
    except WmxError as exc:
        typer.echo(str(exc), err=True)
        sys.exit(exc.exit_code)
